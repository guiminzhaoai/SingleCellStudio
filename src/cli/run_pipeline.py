"""Enterprise-friendly CLI for headless pipeline execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data import DataLoader, auto_detect_format
from analysis import run_standard_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run SingleCellStudio pipeline in headless mode")
    parser.add_argument("--input", required=True, help="Input data file/folder")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--min-genes", type=int, default=200)
    parser.add_argument("--min-cells", type=int, default=3)
    parser.add_argument("--target-sum", type=int, default=10000)
    parser.add_argument("--n-top-genes", type=int, default=2000)
    parser.add_argument("--n-pcs", type=int, default=40)
    parser.add_argument("--resolution", type=float, default=0.5)
    parser.add_argument("--use-harmony", action="store_true", help="Enable Harmony integration")
    parser.add_argument("--batch-key", default="batch")
    parser.add_argument("--checkpoint-mode", choices=["key", "all"], default="key")
    parser.add_argument("--max-cells-for-diagnostics", type=int, default=20000)
    parser.add_argument("--diagnostics-random-state", type=int, default=42)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    loader = DataLoader()
    fmt = auto_detect_format(args.input)
    adata = loader.load(args.input, fmt)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    result_adata, results = run_standard_pipeline(
        adata,
        output_dir=out_dir,
        min_genes=args.min_genes,
        min_cells=args.min_cells,
        target_sum=args.target_sum,
        n_top_genes=args.n_top_genes,
        n_pcs=args.n_pcs,
        resolution=args.resolution,
        use_harmony=args.use_harmony,
        batch_key=args.batch_key,
        checkpoint_mode=args.checkpoint_mode,
        max_cells_for_diagnostics=args.max_cells_for_diagnostics,
        diagnostics_random_state=args.diagnostics_random_state,
    )

    summary_path = out_dir / "metadata" / "cli_run_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "n_obs": int(result_adata.n_obs),
                "n_vars": int(result_adata.n_vars),
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"Pipeline complete. Summary: {summary_path}")


if __name__ == "__main__":
    main()
