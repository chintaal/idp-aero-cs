"""
Train a tiny physics-informed neural network for drag coefficient (Cd) prediction.

Designed for ESP32-S3 TinyML deployment:
  - ~400–800 float32 parameters (< 4 KB weights)
  - Inputs: deployment_pct, mach, velocity, density, area
  - Output: Cd
  - Physics loss enforces F_d = 0.5 * rho * v^2 * Cd * A

Usage
-----
    python scripts/expand_real_data.py
    python scripts/train_pinn_cd.py
    python scripts/train_pinn_cd.py --export-header ../cd_model.h
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

FEATURE_COLS = ["deployment_pct", "mach", "velocity_m_s", "density_kg_m3", "area_m2"]
TARGET_COL = "cd"


class TinyCdPINN(nn.Module):
    """Compact MLP for embedded Cd inference."""

    def __init__(self, hidden: tuple[int, ...] = (16, 16)) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        prev = len(FEATURE_COLS)
        for h in hidden:
            layers += [nn.Linear(prev, h), nn.SiLU()]
            prev = h
        layers.append(nn.Linear(prev, 1))
        self.net = nn.Sequential(*layers)
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class MinMaxScaler:
    def __init__(self) -> None:
        self.mins: np.ndarray | None = None
        self.maxs: np.ndarray | None = None

    def fit(self, x: np.ndarray) -> "MinMaxScaler":
        self.mins = x.min(axis=0)
        self.maxs = x.max(axis=0)
        return self

    def transform(self, x: np.ndarray) -> np.ndarray:
        assert self.mins is not None and self.maxs is not None
        rng = np.where(self.maxs - self.mins < 1e-9, 1.0, self.maxs - self.mins)
        return (x - self.mins) / rng

    def inverse(self, x_norm: np.ndarray) -> np.ndarray:
        assert self.mins is not None and self.maxs is not None
        rng = np.where(self.maxs - self.mins < 1e-9, 1.0, self.maxs - self.mins)
        return x_norm * rng + self.mins


def physics_loss(
    cd_pred: torch.Tensor,
    features_raw: torch.Tensor,
    drag_force: torch.Tensor,
) -> torch.Tensor:
    """
    Residual on drag equation: F_d - 0.5 * rho * v^2 * Cd * A.
    features_raw columns: [deployment_pct, mach, velocity, density, area]
    """
    v = features_raw[:, 2].clamp(min=1.0)
    rho = features_raw[:, 3].clamp(min=0.5)
    area = features_raw[:, 4].clamp(min=1e-5)
    f_pred = 0.5 * rho * v.pow(2) * cd_pred.squeeze(-1) * area
    return nn.functional.mse_loss(f_pred, drag_force)


def monotonic_loss(cd_pred: torch.Tensor, deploy_pct: torch.Tensor) -> torch.Tensor:
    """Soft penalty: Cd should not decrease when deployment increases (pairwise)."""
    if len(cd_pred) < 2:
        return cd_pred.new_zeros(())
    order = torch.argsort(deploy_pct.squeeze(-1))
    cd_sorted = cd_pred[order].squeeze(-1)
    diffs = cd_sorted[1:] - cd_sorted[:-1]
    return nn.functional.relu(-diffs).mean()


def train(
    df: pd.DataFrame,
    artifacts_dir: Path,
    hidden: tuple[int, ...] = (16, 16),
    epochs: int = 800,
    lr: float = 2e-3,
    w_data: float = 1.0,
    w_phys: float = 0.15,
    w_mono: float = 0.05,
    device: str = "cpu",
) -> tuple[TinyCdPINN, MinMaxScaler, dict]:
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    x_raw = df[FEATURE_COLS].values.astype(np.float32)
    y_raw = df[TARGET_COL].values.astype(np.float32).reshape(-1, 1)
    f_drag = df["drag_force_n"].values.astype(np.float32)
    if np.isnan(f_drag).any():
        f_drag = 0.5 * x_raw[:, 3] * x_raw[:, 2] ** 2 * y_raw.squeeze() * x_raw[:, 4]

    scaler = MinMaxScaler().fit(x_raw)
    x_norm = scaler.transform(x_raw)

    y_mean = float(y_raw.mean())
    y_std = float(y_raw.std()) + 1e-8
    y_norm = (y_raw - y_mean) / y_std

    dev = torch.device(device)
    x_t = torch.from_numpy(x_norm).to(dev)
    y_t = torch.from_numpy(y_norm).to(dev)
    x_raw_t = torch.from_numpy(x_raw).to(dev)
    f_t = torch.from_numpy(f_drag).to(dev)
    deploy_t = x_raw_t[:, 0:1]

    model = TinyCdPINN(hidden=hidden).to(dev)
    opt = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs, eta_min=lr * 0.05)

    best_loss = float("inf")
    history: list[dict] = []

    for epoch in range(1, epochs + 1):
        model.train()
        opt.zero_grad()
        pred_norm = model(x_t)
        pred_cd = pred_norm * y_std + y_mean

        loss_data = nn.functional.huber_loss(pred_norm, y_t)
        loss_phys = physics_loss(pred_cd, x_raw_t, f_t)
        loss_mono = monotonic_loss(pred_cd, deploy_t)
        loss = w_data * loss_data + w_phys * loss_phys + w_mono * loss_mono
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()

        model.eval()
        with torch.no_grad():
            mae = float(torch.abs(pred_cd.squeeze() - torch.from_numpy(y_raw.squeeze()).to(dev)).mean())

        rec = {
            "epoch": epoch,
            "loss": float(loss.item()),
            "data": float(loss_data.item()),
            "physics": float(loss_phys.item()),
            "mono": float(loss_mono.item()),
            "mae_cd": mae,
        }
        history.append(rec)

        if loss.item() < best_loss:
            best_loss = loss.item()
            torch.save(model.state_dict(), artifacts_dir / "cd_pinn_best.pt")

        if epoch % 100 == 0 or epoch == 1:
            print(
                f"Epoch {epoch:4d}  loss={rec['loss']:.5f}  "
                f"data={rec['data']:.5f}  phys={rec['physics']:.5f}  MAE(Cd)={mae:.5f}"
            )

    model.load_state_dict(torch.load(artifacts_dir / "cd_pinn_best.pt", weights_only=True))
    stats = {"y_mean": y_mean, "y_std": y_std}
    meta = {
        "feature_cols": FEATURE_COLS,
        "hidden": list(hidden),
        "n_params": sum(p.numel() for p in model.parameters()),
        "weight_bytes_fp32": sum(p.numel() for p in model.parameters()) * 4,
        "stats": stats,
        "scaler_mins": scaler.mins.tolist(),
        "scaler_maxs": scaler.maxs.tolist(),
    }
    (artifacts_dir / "cd_model_meta.json").write_text(json.dumps(meta, indent=2))
    (artifacts_dir / "cd_training_history.json").write_text(json.dumps(history, indent=2))
    return model, scaler, stats


def export_c_header(model: TinyCdPINN, scaler: MinMaxScaler, stats: dict, out_path: Path) -> None:
    """Export trained weights + scaler as a standalone C header for ESP32."""
    n_params = sum(p.numel() for p in model.parameters())
    weight_kb = n_params * 4 / 1024.0
    lines = [
        "// Auto-generated by airbrake/scripts/train_pinn_cd.py",
        "// Tiny PINN for drag coefficient (Cd) — ESP32-S3 TinyML",
        "#pragma once",
        "",
        "#include <stdint.h>",
        "#include <math.h>",
        "",
        f"#define CD_N_FEATURES {len(FEATURE_COLS)}",
        f"#define CD_N_HIDDEN1 {model.net[0].out_features}",
        f"#define CD_N_HIDDEN2 {model.net[2].out_features}",
        f"#define CD_N_PARAMS {n_params}",
        f"#define CD_WEIGHT_KB {weight_kb:.2f}f",
        "",
        "static const float CD_FEATURE_MINS[CD_N_FEATURES] = {",
        "    " + ", ".join(f"{v:.8f}f" for v in scaler.mins) + ",",
        "};",
        "",
        "static const float CD_FEATURE_MAXS[CD_N_FEATURES] = {",
        "    " + ", ".join(f"{v:.8f}f" for v in scaler.maxs) + ",",
        "};",
        "",
        f"static const float CD_Y_MEAN = {stats['y_mean']:.8f}f;",
        f"static const float CD_Y_STD  = {stats['y_std']:.8f}f;",
        "",
    ]

    idx = 0
    for layer in model.net:
        if isinstance(layer, nn.Linear):
            idx += 1
            w = layer.weight.detach().cpu().numpy()
            b = layer.bias.detach().cpu().numpy()
            flat_w = w.flatten()
            lines.append(f"static const float CD_W{idx}_W[{len(flat_w)}] = {{")
            lines.append("    " + ", ".join(f"{v:.8f}f" for v in flat_w) + ",");
            lines.append("};")
            lines.append(f"static const float CD_W{idx}_B[{len(b)}] = {{")
            lines.append("    " + ", ".join(f"{v:.8f}f" for v in b) + ",");
            lines.append("};")
            lines.append("")

    lines += [
        "static inline float cd_silu(float x) { return x / (1.0f + expf(-x)); }",
        "",
        "static inline float cd_predict(const float features[CD_N_FEATURES]) {",
        "    float x[CD_N_FEATURES];",
        "    for (int i = 0; i < CD_N_FEATURES; i++) {",
        "        float rng = CD_FEATURE_MAXS[i] - CD_FEATURE_MINS[i];",
        "        if (rng < 1e-9f) rng = 1.0f;",
        "        x[i] = (features[i] - CD_FEATURE_MINS[i]) / rng;",
        "    }",
        "",
        "    float h1[CD_N_HIDDEN1];",
        "    for (int j = 0; j < CD_N_HIDDEN1; j++) {",
        "        float s = CD_W1_B[j];",
        "        for (int i = 0; i < CD_N_FEATURES; i++)",
        "            s += CD_W1_W[j * CD_N_FEATURES + i] * x[i];",
        "        h1[j] = cd_silu(s);",
        "    }",
        "",
        "    float h2[CD_N_HIDDEN2];",
        "    for (int j = 0; j < CD_N_HIDDEN2; j++) {",
        "        float s = CD_W2_B[j];",
        "        for (int i = 0; i < CD_N_HIDDEN1; i++)",
        "            s += CD_W2_W[j * CD_N_HIDDEN1 + i] * h1[i];",
        "        h2[j] = cd_silu(s);",
        "    }",
        "",
        "    float out = CD_W3_B[0];",
        "    for (int i = 0; i < CD_N_HIDDEN2; i++)",
        "        out += CD_W3_W[i] * h2[i];",
        "",
        "    return out * CD_Y_STD + CD_Y_MEAN;",
        "}",
        "",
        "static inline float cd_drag_force(float cd, float rho, float velocity, float area) {",
        "    return 0.5f * rho * velocity * velocity * cd * area;",
        "}",
        "",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported C header: {out_path}  ({out_path.stat().st_size} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train tiny Cd PINN for ESP32")
    parser.add_argument("--data", type=Path, default=Path("data/processed/cd_expanded.csv"))
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/cd_pinn"))
    parser.add_argument("--export-header", type=Path, action="append", default=[])
    parser.add_argument(
        "--export-header-default",
        type=Path,
        default=Path("../hardware/firmware/esp32-airbrake/include/cd_model.h"),
        help="Primary header path when --export-header is not passed",
    )
    parser.add_argument("--epochs", type=int, default=800)
    parser.add_argument("--hidden", type=int, nargs="+", default=[16, 16])
    args = parser.parse_args()

    if not args.data.exists():
        print(f"Dataset missing: {args.data} — run expand_real_data.py first")
        sys.exit(1)

    df = pd.read_csv(args.data)
    model, scaler, stats = train(
        df,
        artifacts_dir=args.artifacts,
        hidden=tuple(args.hidden),
        epochs=args.epochs,
    )
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Training complete. Parameters: {n_params:,}  (~{n_params * 4 / 1024:.1f} KB fp32)")

    export_paths = args.export_header or [
        args.export_header_default,
        Path("../hardware/arduino/esp32_airbrake/cd_model.h"),
    ]
    seen: set[str] = set()
    for header_path in export_paths:
        key = str(header_path.resolve())
        if key in seen:
            continue
        seen.add(key)
        export_c_header(model, scaler, stats, header_path)


if __name__ == "__main__":
    main()
