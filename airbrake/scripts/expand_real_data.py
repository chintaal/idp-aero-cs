"""
Expand sparse wind-tunnel / CFD tabular data into a dense PINN training set.

Steps
-----
1. Parse real-data-new.txt (tab-separated, sparse metadata rows)
2. Forward-fill deployment %, angle, and reference area
3. Interpolate along Mach and deployment axes
4. Add physics-consistent synthetic samples via the drag equation
5. Write expanded CSV + JSON summary

Usage
-----
    python scripts/expand_real_data.py
    python scripts/expand_real_data.py --input ../real-data-new.txt --output data/processed/cd_expanded.csv
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

DEPLOY_RE = re.compile(
    r"(?P<pct>[\d.]+)\s*%\s*[-–]?\s*(?P<angle>[\d.]+)\s*deg",
    re.IGNORECASE,
)


def parse_deployment(raw: str) -> tuple[float, float]:
    """Extract deployment percent and angle from a label like '25%- 17.12 deg'."""
    match = DEPLOY_RE.search(str(raw))
    if not match:
        return float("nan"), float("nan")
    return float(match.group("pct")), float(match.group("angle"))


def load_real_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t")
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    df = df.replace(r"^\s*$", pd.NA, regex=True)

    meta_cols = [
        "%_of_deployment-_angle_(deg)",
        "area_of_rocket_in_contact_with_us_(m2)",
    ]
    for col in meta_cols:
        if col in df.columns:
            df[col] = df[col].ffill()

    pct_angle = df["%_of_deployment-_angle_(deg)"].apply(parse_deployment)
    df["deployment_pct"] = [p for p, _ in pct_angle]
    df["deployment_angle_deg"] = [a for _, a in pct_angle]

    rename = {
        "mach_number": "mach",
        "freestream_velocity_(m/s)": "velocity_m_s",
        "area_of_rocket_in_contact_with_us_(m2)": "area_m2",
        "altitude_(m)": "altitude_m",
        "atm._pressure(pa)": "pressure_pa",
        "density_of_air(kg/m3)": "density_kg_m3",
        "drag_force_(n)": "drag_force_n",
        "coefficient_of_drag": "cd",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    numeric_cols = [
        "mach", "velocity_m_s", "area_m2", "altitude_m",
        "pressure_pa", "density_kg_m3", "drag_force_n", "cd",
        "deployment_pct", "deployment_angle_deg",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["mach", "velocity_m_s", "cd", "deployment_pct"])
    df["area_m2"] = df["area_m2"].ffill().bfill()
    df["density_kg_m3"] = df["density_kg_m3"].ffill()
    df["altitude_m"] = df["altitude_m"].ffill()
    df["pressure_pa"] = df["pressure_pa"].ffill()
    return df.reset_index(drop=True)


def _interp_grid(
    df: pd.DataFrame,
    x_col: str,
    x_values: np.ndarray,
    y_col: str,
    y_values: np.ndarray,
    value_cols: list[str],
) -> pd.DataFrame:
    """Bilinear-style expansion via independent 1-D interpolations on a grid."""
    rows: list[dict] = []
    for x in x_values:
        for y in y_values:
            x_near = df[np.isclose(df[x_col], x, atol=1e-6)]
            y_near = df[np.isclose(df[y_col], y, atol=1e-6)]
            if len(x_near) == 0 or len(y_near) == 0:
                continue

            row: dict = {x_col: float(x), y_col: float(y), "synthetic": True}
            for col in value_cols:
                if col in (x_col, y_col):
                    continue
                x_interp = np.interp(x, df[x_col].unique(), [
                    df.loc[np.isclose(df[x_col], xv), col].mean()
                    for xv in sorted(df[x_col].unique())
                ])
                y_interp = np.interp(y, df[y_col].unique(), [
                    df.loc[np.isclose(df[y_col], yv), col].mean()
                    for yv in sorted(df[y_col].unique())
                ])
                row[col] = 0.5 * (x_interp + y_interp)
            rows.append(row)
    return pd.DataFrame(rows)


def expand_dataset(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = df.copy()
    base["synthetic"] = False

    mach_dense = np.round(np.arange(0.1, 0.41, 0.025), 3)
    deploy_dense = np.arange(0.0, 100.01, 6.25)

    synth_rows: list[dict] = []

    # Interpolate Cd, area, density along Mach for each deployment level
    for pct in sorted(base["deployment_pct"].unique()):
        subset = base[np.isclose(base["deployment_pct"], pct)]
        if len(subset) < 2:
            continue
        mach_pts = subset["mach"].values
        for m in mach_dense:
            if m in mach_pts:
                continue
            row = {"deployment_pct": pct, "mach": float(m), "synthetic": True}
            for col in ["cd", "area_m2", "velocity_m_s", "density_kg_m3", "altitude_m", "pressure_pa"]:
                row[col] = float(np.interp(m, mach_pts, subset[col].values))
            angle = subset["deployment_angle_deg"].iloc[0]
            row["deployment_angle_deg"] = float(angle) if not np.isnan(angle) else pct * 0.557
            row["velocity_m_s"] = row["mach"] * 343.0
            synth_rows.append(row)

    # Interpolate along deployment for each Mach
    for mach in sorted(base["mach"].unique()):
        subset = base[np.isclose(base["mach"], mach)]
        if len(subset) < 2:
            continue
        pct_pts = subset["deployment_pct"].values
        for pct in deploy_dense:
            if pct in pct_pts:
                continue
            row = {"deployment_pct": float(pct), "mach": float(mach), "synthetic": True}
            for col in ["cd", "area_m2", "density_kg_m3", "altitude_m", "pressure_pa"]:
                row[col] = float(np.interp(pct, pct_pts, subset[col].values))
            row["deployment_angle_deg"] = float(np.interp(pct, pct_pts, subset["deployment_angle_deg"].values))
            row["velocity_m_s"] = float(mach * 343.0)
            synth_rows.append(row)

    synth = pd.DataFrame(synth_rows)

    # Physics-consistent drag force and Cd cross-check samples
    physics_rows: list[dict] = []
    combined = pd.concat([base, synth], ignore_index=True)
    for _, r in combined.iterrows():
        rho = r["density_kg_m3"]
        v = r["velocity_m_s"]
        a = r["area_m2"]
        cd = r["cd"]
        if rho <= 0 or v <= 0 or a <= 0:
            continue
        f_drag = 0.5 * rho * v * v * cd * a
        physics_rows.append({
            **r.to_dict(),
            "drag_force_n": f_drag,
            "synthetic": True,
        })

        # Small perturbations for robustness (±3 % noise on inputs)
        for _ in range(2):
            noise = 1.0 + rng.normal(0.0, 0.03, 3)
            v_n = max(v * noise[0], 1.0)
            rho_n = max(rho * noise[1], 0.5)
            cd_n = max(cd * noise[2], 0.05)
            a_n = a
            physics_rows.append({
                "deployment_pct": r["deployment_pct"],
                "deployment_angle_deg": r["deployment_angle_deg"],
                "mach": v_n / 343.0,
                "velocity_m_s": v_n,
                "area_m2": a_n,
                "altitude_m": r["altitude_m"],
                "pressure_pa": r["pressure_pa"],
                "density_kg_m3": rho_n,
                "cd": cd_n,
                "drag_force_n": 0.5 * rho_n * v_n * v_n * cd_n * a_n,
                "synthetic": True,
            })

    expanded = pd.concat([base, synth, pd.DataFrame(physics_rows)], ignore_index=True)
    expanded = expanded.drop_duplicates(
        subset=["deployment_pct", "mach", "velocity_m_s", "area_m2"],
        keep="first",
    )
    return expanded.sort_values(["deployment_pct", "mach"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand real drag-coefficient data")
    parser.add_argument("--input", type=Path, default=Path("../real-data-new.txt"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/cd_expanded.csv"))
    parser.add_argument("--summary", type=Path, default=Path("data/processed/cd_expanded_summary.json"))
    args = parser.parse_args()

    df = load_real_data(args.input)
    expanded = expand_dataset(df)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    expanded.to_csv(args.output, index=False)

    summary = {
        "source_rows": int(len(df)),
        "expanded_rows": int(len(expanded)),
        "synthetic_rows": int(expanded["synthetic"].sum()),
        "deployment_pct_range": [float(expanded["deployment_pct"].min()), float(expanded["deployment_pct"].max())],
        "mach_range": [float(expanded["mach"].min()), float(expanded["mach"].max())],
        "cd_range": [float(expanded["cd"].min()), float(expanded["cd"].max())],
    }
    args.summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Loaded {len(df)} real rows -> expanded to {len(expanded)} rows")
    print(f"Wrote {args.output}")
    print(f"Wrote {args.summary}")


if __name__ == "__main__":
    main()
