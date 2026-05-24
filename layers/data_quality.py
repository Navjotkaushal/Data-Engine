from __future__ import annotations

import pandas as pd

from config.thresholds import HIGH_MISSING_FLAG, LEAKAGE_CORR_THRESHOLD, ALWAYS_POSITIVE_HINTS, NUMERIC_CORRUPTION_RATIO
from utils.logger import get_logger


log = get_logger(__name__)


def _numeric_corruption_count(series: pd.Series) -> int:
    if pd.api.types.is_numeric_dtype(series):
        return 0

    non_null = series.dropna()
    if non_null.empty:
        return 0

    coerced = pd.to_numeric(non_null.astype(str).str.replace(",", "", regex=False), errors="coerce")
    numeric_ratio = coerced.notna().mean()

    if numeric_ratio < NUMERIC_CORRUPTION_RATIO:
        return 0

    return int(coerced.isna().sum())


def quality(df: pd.DataFrame, target: str, schema: dict) -> dict:
    numerical_cols = [col for col in schema["numerical"] if col in df.columns]
    total_rows = len(df)

    quality_report = {
        "duplicate_rows": 0,
        "leakage_cols": [],
        "constant_cols": [],
        "corrupted_cols": {},
        "invalid_range_cols": {},
        "high_missing_cols": {},
    }

    duplicate_rows = int(df.duplicated().sum())
    quality_report["duplicate_rows"] = duplicate_rows
    if duplicate_rows:
        log.warning("%s duplicate rows found", duplicate_rows)

    for column in df.columns:
        if column == target:
            continue

        series = df[column]

        if series.nunique(dropna=False) <= 1:
            quality_report["constant_cols"].append(column)
            continue

        missing_ratio = series.isna().mean()
        if missing_ratio > HIGH_MISSING_FLAG:
            quality_report["high_missing_cols"][column] = round(missing_ratio, 4)
            log.warning("High missing (%s): %s", f"{missing_ratio:.0%}", column)

        corrupted_count = _numeric_corruption_count(series)
        if corrupted_count:
            quality_report["corrupted_cols"][column] = corrupted_count
            log.warning("Corrupted numeric-like values (%s): %s", corrupted_count, column)

        if column in numerical_cols:
            lowered = column.lower()
            if any(hint in lowered for hint in ALWAYS_POSITIVE_HINTS):
                negative_count = int((series < 0).sum())
                if negative_count:
                    quality_report["invalid_range_cols"][column] = negative_count
                    log.warning(
                        "Negative values (%s) in likely-positive column: %s",
                        negative_count,
                        column,
                    )

    leakage_columns: list[str] = []

    if pd.api.types.is_numeric_dtype(df[target]):
        for column in numerical_cols:
            try:
                correlation = abs(df[column].corr(df[target]))
            except Exception:
                continue

            if pd.notna(correlation) and correlation > LEAKAGE_CORR_THRESHOLD:
                leakage_columns.append(column)
                log.warning("Possible leakage (corr=%.3f): %s", correlation, column)

    else:
        # Classification target: encode target as integer codes and correlate.
        # Not as precise as mutual information but fast and catches obvious leakage.
        target_encoded = df[target].astype("category").cat.codes.astype(float)
        for column in numerical_cols:
            try:
                correlation = abs(df[column].corr(target_encoded))
            except Exception:
                continue

            if pd.notna(correlation) and correlation > LEAKAGE_CORR_THRESHOLD:
                leakage_columns.append(column)
                log.warning("Possible leakage vs categorical target (corr=%.3f): %s", correlation, column)

    quality_report["leakage_cols"] = sorted(set(leakage_columns))

    log.info("Quality check complete")
    return quality_report