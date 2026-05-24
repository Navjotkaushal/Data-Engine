from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from layers.data_profiling import profiling
from layers.data_quality import quality
from layers.decision_engine import decision_engine
from layers.input_layer import data_input_pipeline
from layers.schema_detection import schema_detection
from layers.transformer import transformer
from utils.logger import get_logger
from utils.sanitizer import sanitize

log = get_logger("pipeline")

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "output" / "cleaned_data"
DEFAULT_JSON_OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "output" / "json_data"


def run_pipeline(
    dataset_path: str | None = None,
    target: str | None = None,
    output_dir: str | os.PathLike[str] | None = None,
    json_output_dir: str | os.PathLike[str] | None = None,
    interactive: bool | None = None,
) -> dict | None:
    final_output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    final_json_output_dir = Path(json_output_dir) if json_output_dir else DEFAULT_JSON_OUTPUT_DIR
    final_output_dir.mkdir(parents=True, exist_ok=True)
    final_json_output_dir.mkdir(parents=True, exist_ok=True)

    if interactive is None:
        interactive = dataset_path is None or target is None

    log.info("=" * 55)
    log.info("DATA INTELLIGENCE LAYER - Pipeline Start")
    log.info("=" * 55)

    log.info("[Layer 1] Data Input")
    df, resolved_target, dataset_name = data_input_pipeline(
        path=dataset_path,
        target=target,
        interactive=interactive,
    )
    if df is None or resolved_target is None:
        log.error("No data loaded. Exiting pipeline.")
        return None

    log.info("[Layer 2] Schema Detection")
    schema = schema_detection(df, resolved_target)

    log.info("[Layer 3] Data Profiling")
    stats = profiling(df, resolved_target, schema)

    log.info("[Layer 4] Data Quality")
    quality_report = quality(df, resolved_target, schema)

    log.info("[Layer 5] Decision Engine")
    decisions = decision_engine(schema, stats, quality_report)

    log.info("[Layer 6] Transformer")
    clean_df = transformer(
        df=df,
        decisions=decisions,
        target=resolved_target,
        output_dir=str(final_output_dir),
        dataset_name=dataset_name,
    )

    report = sanitize(
        {
            "target": resolved_target,
            "dataset_shape": list(df.shape),
            "clean_shape": list(clean_df.shape),
            "schema": schema,
            "stats": stats,
            "quality_report": quality_report,
            "decisions": decisions,
        }
    )

    report_path = final_json_output_dir / f"{dataset_name}_report.json"
    with report_path.open("w", encoding="utf-8") as file_handle:
        json.dump(report, file_handle, indent=2)

    log.info("=" * 55)
    log.info("PIPELINE COMPLETE")
    log.info("Clean CSV  -> %s", final_output_dir / f"{dataset_name}_cleaned.csv")
    log.info("Full report -> %s", report_path)
    log.info("Logs       -> data/output/logger_run.log")
    log.info("=" * 55)

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Data Intelligence Layer pipeline.")
    parser.add_argument(
        "--dataset",
        "-d",
        help="Path to the dataset CSV file.",
    )
    parser.add_argument(
        "--target",
        "-t",
        help="Name of the target column.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where clean_output.csv and dil_report.json will be written.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for missing values instead of failing in non-interactive mode.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    interactive = args.interactive or not (args.dataset and args.target)

    run_pipeline(
        dataset_path=args.dataset,
        target=args.target,
        output_dir=args.output_dir,
        interactive=interactive,
    )


if __name__ == "__main__":
    main()
