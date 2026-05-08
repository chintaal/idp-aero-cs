"""
Convert parquet datasets to human-readable CSV files with summaries.

Usage:
    python scripts/convert_datasets_to_csv.py
    python scripts/convert_datasets_to_csv.py --input-root data/raw --output-root data/human_readable
    python scripts/convert_datasets_to_csv.py --txt-file "../real data.txt"
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    normalized = [
        col.strip().lower().replace("%", "percent").replace(".", "").replace("/", "_per_")
        for col in df.columns
    ]
    normalized = ["_".join(part for part in col.replace("-", " ").split()) for col in normalized]
    df.columns = normalized
    return df


def _clean_tabular_text(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t")
    df = _normalize_columns(df)

    # Turn empty strings into NA to make cleanup easier.
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    for column in df.columns:
        # Forward-fill metadata columns where the source file intentionally leaves repeated values blank.
        if df[column].dtype == "object":
            df[column] = df[column].ffill()
    return df


def _dataset_summary(df: pd.DataFrame, source_file: str) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "source_file": source_file,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "null_counts": {k: int(v) for k, v in df.isna().sum().to_dict().items()},
        "dtypes": {k: str(v) for k, v in df.dtypes.to_dict().items()},
    }

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if numeric_cols:
        describe = df[numeric_cols].describe().round(6).to_dict()
        summary["numeric_describe"] = describe
    return summary


def _write_summary_markdown(summaries: list[dict[str, Any]], output_path: Path) -> None:
    lines = ["# Dataset Summary", ""]
    for item in summaries:
        lines.append(f"## {item['source_file']}")
        lines.append(f"- rows: {item['rows']}")
        lines.append(f"- columns: {item['columns']}")
        lines.append(f"- column_names: {', '.join(item['column_names'])}")
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def convert_parquet_tree(input_root: Path, output_root: Path) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    parquet_files = sorted(input_root.rglob("*.parquet"))
    output_root.mkdir(parents=True, exist_ok=True)

    for parquet_file in parquet_files:
        relative = parquet_file.relative_to(input_root)
        csv_path = output_root / relative.with_suffix(".csv")
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        df = pd.read_parquet(parquet_file)
        df.to_csv(csv_path, index=False)

        summaries.append(_dataset_summary(df, str(parquet_file)))
        print(f"Converted parquet -> csv: {parquet_file} -> {csv_path}")
    return summaries


def convert_text_files(files: list[Path], output_root: Path) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for txt_file in files:
        if not txt_file.exists():
            print(f"Skipping missing file: {txt_file}")
            continue
        try:
            df = _clean_tabular_text(txt_file)
        except EmptyDataError:
            print(f"Skipping empty file: {txt_file}")
            continue
        csv_path = output_root / f"{txt_file.stem.replace(' ', '_').lower()}.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        summaries.append(_dataset_summary(df, str(txt_file)))
        print(f"Converted text -> csv: {txt_file} -> {csv_path}")
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert parquet datasets into human-readable CSV files and summaries."
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("data/raw"),
        help="Root directory containing parquet files.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/human_readable"),
        help="Root directory where CSV and summaries are written.",
    )
    parser.add_argument(
        "--txt-file",
        type=Path,
        action="append",
        default=[],
        help="Optional tabular text file to clean and convert. Can be passed multiple times.",
    )
    args = parser.parse_args()

    all_summaries: list[dict[str, Any]] = []

    all_summaries.extend(convert_parquet_tree(args.input_root, args.output_root))
    all_summaries.extend(convert_text_files(args.txt_file, args.output_root))

    summary_json = args.output_root / "dataset_summary.json"
    summary_md = args.output_root / "dataset_summary.md"
    summary_json.write_text(json.dumps(all_summaries, indent=2), encoding="utf-8")
    _write_summary_markdown(all_summaries, summary_md)

    print(f"Wrote summaries: {summary_json} and {summary_md}")


if __name__ == "__main__":
    main()
