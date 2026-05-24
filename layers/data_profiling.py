from __future__ import annotations

import pandas as pd

from config.thresholds import OUTLIER_IQR_FACTOR, TARGET_CLASSIFICATION_MAX_UNIQUE
from utils.logger import get_logger

log = get_logger(__name__)


def profiling(df: pd.DataFrame, target: str, schema: dict) -> dict:
    numerical_cols = [col for col in schema["numerical"] if col in df.columns]
    total_rows = len(df)

    stats = {
        "missing_count": {},
        "missing_ratio": {},
        "cardinality": {},
        "skewness": {},
        "outlier_ratio": {},
        "constant_cols": [],
        "class_distribution": None,
        "target_summary": None,
        "correlation_matrix": None,
    }

    for column in df.columns:
        if column == target:
            continue

        series = df[column]

        if series.nunique(dropna=False) <= 1:
            stats["constant_cols"].append(column)
            continue

        missing_count = int(series.isna().sum())
        stats["missing_count"][column] = missing_count
        stats["missing_ratio"][column] = round(missing_count / total_rows, 4)
        stats["cardinality"][column] = int(series.nunique(dropna=True))

        if column not in numerical_cols:
            continue

        skewness = series.skew()
        stats["skewness"][column] = round(float(skewness), 4) if pd.notna(skewness) else 0.0

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - OUTLIER_IQR_FACTOR * iqr
        upper = q3 + OUTLIER_IQR_FACTOR * iqr
        outliers = int(((series < lower) | (series > upper)).sum())
        stats["outlier_ratio"][column] = round(outliers / total_rows, 4)

    if df[target].dtype == "object" or df[target].nunique(dropna=True) < TARGET_CLASSIFICATION_MAX_UNIQUE:
        stats["class_distribution"] = df[target].value_counts(dropna=False).to_dict()
        log.info("Class distribution computed for target")
        
    elif pd.api.types.is_numeric_dtype(df[target]):
        stats["target_summary"] = {
            "mean": round(float(df[target].mean()), 4),
            "median": round(float(df[target].median()), 4),
            "std": round(float(df[target].std()), 4),
            "min": round(float(df[target].min()), 4),
            "max": round(float(df[target].max()), 4),
        }
        log.info("Regression target summary computed")

    if numerical_cols:
        stats["correlation_matrix"] = df[numerical_cols].corr().round(4).to_dict()
        log.info("Correlation matrix computed for %s numerical columns", len(numerical_cols))

    log.info("Profiling complete - %s features analyzed", len(df.columns) - 1)
    return stats
