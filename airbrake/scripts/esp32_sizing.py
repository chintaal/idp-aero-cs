"""
ESP32-S3 PINN sizing envelope and architecture search.

Budget assumptions (conservative, no PSRAM required):
  - Weights live in flash (PROGMEM), not SRAM
  - Inference scratch = 2 * max(hidden_width) * 4 bytes
  - Default app partition ~1.25 MB — cap model weights at 450 KB fp32
  - Loop-task stack headroom: keep scratch <= 8 KB

Usage:
    python scripts/esp32_sizing.py
    python scripts/esp32_sizing.py --target-kb 400
"""


from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass
class ArchResult:
    hidden: tuple[int, ...]
    n_params: int
    weight_kb: float
    stack_bytes: int


def count_mlp_params(in_dim: int, hidden: tuple[int, ...]) -> int:
    dims = [in_dim, *hidden, 1]
    total = 0
    for i in range(len(dims) - 1):
        total += dims[i] * dims[i + 1] + dims[i + 1]
    return total


def stack_bytes(hidden: tuple[int, ...], in_dim: int = 5) -> int:
    widths = [in_dim, *hidden, 1]
    return 2 * max(widths) * 4


def search_max_arch(
    in_dim: int = 5,
    max_weight_kb: float = 450.0,
    max_stack_bytes: int = 8192,
    width_candidates: tuple[int, ...] = (32, 48, 64, 96, 128, 160, 192, 224, 256, 288, 320),
) -> ArchResult:
    best: ArchResult | None = None

    def consider(hidden: tuple[int, ...]) -> None:
        nonlocal best
        n_params = count_mlp_params(in_dim, hidden)
        w_kb = n_params * 4 / 1024.0
        stk = stack_bytes(hidden, in_dim)
        if w_kb > max_weight_kb or stk > max_stack_bytes:
            return
        cand = ArchResult(hidden, n_params, w_kb, stk)
        if best is None or cand.n_params > best.n_params:
            best = cand

    # Hand-tuned pyramids near the ESP32-S3 fp32 flash knee (~450 KB)
    for hidden in (
        (256, 256, 128, 64, 32),
        (384, 192, 96, 48, 32),
        (320, 160, 80, 40, 32),
        (224, 224, 112, 56, 28),
        (192, 192, 128, 64, 32),
    ):
        consider(hidden)

    for depth in range(2, 7):
        for w in width_candidates:
            pyramid: list[int] = []
            cur = w
            for _ in range(depth):
                pyramid.append(cur)
                cur = max(32, cur // 2)
            consider(tuple(pyramid))

    if best is None:
        raise RuntimeError("No architecture fits the given ESP32 budget")
    return best


def main() -> None:
    parser = argparse.ArgumentParser(description="ESP32-S3 PINN sizing search")
    parser.add_argument("--target-kb", type=float, default=450.0)
    parser.add_argument("--max-stack", type=int, default=8192)
    args = parser.parse_args()

    best = search_max_arch(max_weight_kb=args.target_kb, max_stack_bytes=args.max_stack)
    print("ESP32-S3 PINN sizing envelope")
    print(f"  Weight budget:   <= {args.target_kb:.0f} KB fp32 (flash / PROGMEM)")
    print(f"  Stack budget:    <= {args.max_stack} B (inference scratch)")
    print("")
    print("Recommended MAX architecture:")
    print(f"  hidden = {list(best.hidden)}")
    print(f"  params = {best.n_params:,}")
    print(f"  weights = {best.weight_kb:.1f} KB fp32")
    print(f"  stack   = {best.stack_bytes} B")


if __name__ == "__main__":
    main()
