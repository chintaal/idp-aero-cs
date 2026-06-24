"""
Generate ESP32-compatible C headers for arbitrary-depth Cd PINN MLPs.

Weights are stored in flash (PROGMEM on ESP32). Inference uses two
activation scratch buffers sized to the widest hidden layer.
"""
from __future__ import annotations

from pathlib import Path

import torch.nn as nn

FEATURE_COLS = [
    "deployment_pct",
    "mach",
    "velocity_m_s",
    "density_kg_m3",
    "area_m2",
]


def _linear_layers(model: nn.Module) -> list[nn.Linear]:
    layers: list[nn.Linear] = []
    for module in model.modules():
        if isinstance(module, nn.Linear):
            layers.append(module)
    return layers


def count_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


def inference_stack_bytes(model: nn.Module) -> int:
    """Two-buffer scratch: 2 * max(layer_width) * sizeof(float)."""
    linears = _linear_layers(model)
    if not linears:
        return 0
    widths = [layer.in_features for layer in linears] + [linears[-1].out_features]
    return 2 * max(widths) * 4


def export_c_header(
    model: nn.Module,
    scaler_mins,
    scaler_maxs,
    stats: dict,
    out_path: Path,
    *,
    header_comment: str = "Auto-generated Cd PINN for ESP32-S3",
    model_tag: str = "CD",
) -> dict:
    """
    Export MLP weights + generic layer-wise inference to a C header.

    Returns a summary dict (params, weight_kb, stack_bytes, hidden_dims).
    """
    linears = _linear_layers(model)
    if not linears:
        raise ValueError("Model has no Linear layers")

    n_params = count_params(model)
    weight_kb = n_params * 4 / 1024.0
    stack_bytes = inference_stack_bytes(model)
    hidden_dims = [layer.out_features for layer in linears[:-1]]
    max_width = max(layer.in_features for layer in linears)
    max_width = max(max_width, linears[-1].out_features)

    tag = model_tag
    lines = [
        f"// {header_comment}",
        "#pragma once",
        "",
        "#include <stdint.h>",
        "#include <math.h>",
        "",
        "#if defined(ESP32) || defined(ESP32S3)",
        "#include <pgmspace.h>",
        "#define CD_MODEL_STORE PROGMEM",
        "#else",
        "#define CD_MODEL_STORE",
        "#endif",
        "",
        f"#define {tag}_N_FEATURES {len(FEATURE_COLS)}",
        f"#define {tag}_N_LAYERS {len(linears)}",
        f"#define {tag}_MAX_WIDTH {max_width}",
        f"#define {tag}_N_PARAMS {n_params}",
        f"#define {tag}_WEIGHT_KB {weight_kb:.2f}f",
        f"#define {tag}_STACK_BYTES {stack_bytes}",
        "",
        f"static const float {tag}_FEATURE_MINS[{tag}_N_FEATURES] CD_MODEL_STORE = {{",
        "    " + ", ".join(f"{v:.8f}f" for v in scaler_mins) + ",",
        "};",
        "",
        f"static const float {tag}_FEATURE_MAXS[{tag}_N_FEATURES] CD_MODEL_STORE = {{",
        "    " + ", ".join(f"{v:.8f}f" for v in scaler_maxs) + ",",
        "};",
        "",
        f"static const float {tag}_Y_MEAN CD_MODEL_STORE = {stats['y_mean']:.8f}f;",
        f"static const float {tag}_Y_STD  CD_MODEL_STORE = {stats['y_std']:.8f}f;",
        "",
    ]

    layer_meta: list[tuple[int, int, int]] = []
    for idx, layer in enumerate(linears, start=1):
        in_f = layer.in_features
        out_f = layer.out_features
        layer_meta.append((idx, in_f, out_f))
        w = layer.weight.detach().cpu().numpy().flatten()
        b = layer.bias.detach().cpu().numpy()
        lines.append(f"#define {tag}_L{idx}_IN {in_f}")
        lines.append(f"#define {tag}_L{idx}_OUT {out_f}")
        lines.append(f"static const float {tag}_W{idx}_W[{len(w)}] CD_MODEL_STORE = {{")
        lines.append("    " + ", ".join(f"{v:.8f}f" for v in w) + ",")
        lines.append("};")
        lines.append(f"static const float {tag}_W{idx}_B[{len(b)}] CD_MODEL_STORE = {{")
        lines.append("    " + ", ".join(f"{v:.8f}f" for v in b) + ",")
        lines.append("};")
        lines.append("")

    lines += [
        f"static inline float {tag.lower()}_silu(float x) {{",
        "    return x / (1.0f + expf(-x));",
        "}",
        "",
        f"static inline float {tag.lower()}_read_w(",
        f"    const float* weights, int idx) {{",
        "#if defined(ESP32) || defined(ESP32S3)",
        "    return pgm_read_float(&weights[idx]);",
        "#else",
        "    return weights[idx];",
        "#endif",
        "}",
        "",
        f"static inline void {tag.lower()}_dense_silu(",
        "    const float* input,",
        "    int in_dim,",
        "    float* output,",
        "    int out_dim,",
        "    const float* weights,",
        "    const float* bias) {",
        "    for (int j = 0; j < out_dim; j++) {",
        "        float sum = cd_read_w(bias, j);",
        "        for (int i = 0; i < in_dim; i++) {",
        "            sum += cd_read_w(weights, j * in_dim + i) * input[i];",
        "        }",
        "        output[j] = cd_silu(sum);",
        "    }",
        "}",
        "",
        f"static inline float {tag.lower()}_dense_linear(",
        "    const float* input,",
        "    int in_dim,",
        "    const float* weights,",
        "    const float* bias) {",
        "    float sum = cd_read_w(bias, 0);",
        "    for (int i = 0; i < in_dim; i++) {",
        "        sum += cd_read_w(weights, i) * input[i];",
        "    }",
        "    return sum;",
        "}",
        "",
        f"static inline float {tag.lower()}_predict(const float features[{tag}_N_FEATURES]) {{",
        f"    float x[{tag}_N_FEATURES];",
        f"    for (int i = 0; i < {tag}_N_FEATURES; i++) {{",
        f"        float rng = {tag}_FEATURE_MAXS[i] - {tag}_FEATURE_MINS[i];",
        "        if (rng < 1e-9f) rng = 1.0f;",
        f"        x[i] = (features[i] - {tag}_FEATURE_MINS[i]) / rng;",
        "    }",
        "",
        f"    float buf_a[{tag}_MAX_WIDTH];",
        f"    float buf_b[{tag}_MAX_WIDTH];",
        "    const float* in_buf = x;",
        f"    int in_dim = {tag}_N_FEATURES;",
        "    float* out_buf = buf_a;",
        "",
    ]

    for idx, in_f, out_f in layer_meta[:-1]:
        lines += [
            f"    // Hidden layer {idx}: {in_f} -> {out_f}",
            f"    cd_dense_silu(in_buf, in_dim, out_buf, {tag}_L{idx}_OUT, {tag}_W{idx}_W, {tag}_W{idx}_B);",
            "    in_buf = out_buf;",
            f"    in_dim = {tag}_L{idx}_OUT;",
            "    out_buf = (out_buf == buf_a) ? buf_b : buf_a;",
            "",
        ]

    # Output layer (linear, no SiLU)
    last_idx, last_in, last_out = layer_meta[-1]
    lines += [
        f"    float out_norm = cd_dense_linear(in_buf, in_dim, {tag}_W{last_idx}_W, {tag}_W{last_idx}_B);",
        f"    return out_norm * {tag}_Y_STD + {tag}_Y_MEAN;",
        "}",
        "",
        f"static inline float {tag.lower()}_drag_force(float cd, float rho, float velocity, float area) {{",
        "    return 0.5f * rho * velocity * velocity * cd * area;",
        "}",
        "",
    ]

    # Fix function name prefixes in generated helpers (use tag consistently)
    body = "\n".join(lines)
    prefix = tag.lower()
    body = body.replace("cd_read_w", f"{prefix}_read_w")
    body = body.replace("cd_dense_silu", f"{prefix}_dense_silu")
    body = body.replace("cd_dense_linear", f"{prefix}_dense_linear")
    body = body.replace("cd_silu", f"{prefix}_silu")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body, encoding="utf-8")

    summary = {
        "n_params": n_params,
        "weight_bytes_fp32": n_params * 4,
        "weight_kb": round(weight_kb, 2),
        "stack_bytes": stack_bytes,
        "max_width": max_width,
        "hidden_dims": hidden_dims,
        "n_layers": len(linears),
        "header_bytes": out_path.stat().st_size,
    }
    print(
        f"Exported {out_path}  |  {n_params:,} params  "
        f"({weight_kb:.1f} KB fp32)  stack={stack_bytes} B"
    )
    return summary
