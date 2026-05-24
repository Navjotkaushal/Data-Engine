from __future__ import annotations

from config.thresholds import (
    HIGH_CARDINALITY_LIMIT,
    OUTLIER_CAP_THRESHOLD,
    SKEW_THRESHOLD,
)
from utils.logger import get_logger

log = get_logger(__name__)


def decision_engine(schema: dict, stats: dict, quality_report: dict) -> dict:
    decisions = {
        "drop_cols": [],
        "drop_duplicates": False,
        "extract_datetime": [],
        "impute_mean": [],
        "impute_median": [],
        "impute_mode": [],
        # "impute_constant": {},
        "cap_outliers": [],
        "encode_onehot": [],
        "encode_label": [],
        "scale_standard": [],
        "scale_minmax": [],
    }

    to_drop = set(schema.get("drop_columns", []))
    to_drop.update(quality_report.get("leakage_cols", []))
    to_drop.update(schema.get("id_columns", []))
    to_drop.update(schema.get("text", []))

    decisions["drop_cols"] = sorted(to_drop)
    for column in decisions["drop_cols"]:
        log.info("Decision -> drop column: %s", column)

    if quality_report.get("duplicate_rows", 0) > 0:
        decisions["drop_duplicates"] = True
        log.info("Decision -> drop duplicate rows")

    for column in schema.get("datetime", []):
        if column in decisions["drop_cols"]:
            continue
        decisions["extract_datetime"].append(column)
        log.info("Decision -> extract datetime features: %s", column)

    for column in schema.get("numerical", []):
        if column in decisions["drop_cols"]:
            continue

        missing_ratio = stats["missing_ratio"].get(column, 0)
        skewness = stats["skewness"].get(column, 0)
        outlier_ratio = stats["outlier_ratio"].get(column, 0)

        if missing_ratio > 0:
            if abs(skewness) > SKEW_THRESHOLD:
                decisions["impute_median"].append(column)
                log.info("Decision -> impute median (skew=%.2f): %s", skewness, column)
            else:
                decisions["impute_mean"].append(column)
                log.info("Decision -> impute mean (skew=%.2f): %s", skewness, column)

        if outlier_ratio > OUTLIER_CAP_THRESHOLD:
            decisions["cap_outliers"].append(column)
            log.info("Decision -> cap outliers (ratio=%.2f): %s", outlier_ratio, column)

        if abs(skewness) > SKEW_THRESHOLD:
            decisions["scale_minmax"].append(column)
            log.info("Decision -> min-max scale: %s", column)
        else:
            decisions["scale_standard"].append(column)
            log.info("Decision -> standard scale: %s", column)

    for column in schema.get("categorical", []):
        if column in decisions["drop_cols"]:
            continue

        missing_ratio = stats["missing_ratio"].get(column, 0)
        cardinality = stats["cardinality"].get(column, 0)

        if missing_ratio > 0:
            decisions["impute_mode"].append(column)
            log.info("Decision -> impute mode: %s", column)

        if cardinality <= HIGH_CARDINALITY_LIMIT:
            decisions["encode_onehot"].append(column)
            log.info("Decision -> one-hot encode: %s", column)
        else:
            decisions["encode_label"].append(column)
            log.info("Decision -> label encode: %s", column)

    for column in schema.get("binary", []):
        if column in decisions["drop_cols"]:
            continue

        missing_ratio = stats["missing_ratio"].get(column, 0)
        if missing_ratio > 0:
            decisions["impute_mode"].append(column)
            log.info("Decision -> impute mode (binary): %s", column)

        decisions["encode_label"].append(column)
        log.info("Decision -> label encode (binary): %s", column)

    log.info("Decision engine complete")
    return decisions
