from __future__ import annotations

import pandas as pd

from config.thresholds import (
    DATETIME_VALID_RATIO,
    DATETIME_YEAR_MAX,
    DATETIME_YEAR_MIN,
    ID_UNIQUE_RATIO,
    MISSING_DROP_THRESHOLD,
    NUMERIC_CATEGORY_MAX_UNIQUE,
    TEXT_AVG_LENGTH,
    ID_COLUMN_HINTS,
)
from utils.logger import get_logger

log = get_logger(__name__)




def _object_average_length(series: pd.Series) -> float:
    non_null = series.dropna().astype(str)
    if non_null.empty:
        return 0.0
    return float(non_null.str.len().mean())


def _is_binary(series: pd.Series) -> bool:
    return series.nunique(dropna=True) == 2


def _is_numeric_categorical(series: pd.Series) -> bool:
    if not pd.api.types.is_numeric_dtype(series):
        return False

    non_null = series.dropna()
    if non_null.empty:
        return False

    if not (non_null % 1 == 0).all():
        return False

    return non_null.nunique() <= NUMERIC_CATEGORY_MAX_UNIQUE


def _detect_datetime(series: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True

    if series.dtype != "object":
        return False

    parsed = pd.to_datetime(series, errors="coerce", format="mixed")
    valid_ratio = parsed.notna().mean()
    if valid_ratio < DATETIME_VALID_RATIO:
        return False

    valid_years = parsed.dropna().dt.year
    if valid_years.empty:
        return False

    return bool(valid_years.between(DATETIME_YEAR_MIN, DATETIME_YEAR_MAX).mean() >= 0.9)


def _is_sequential_index(series: pd.Series) -> bool:
    """Return True if the series looks like a row index: integers incrementing by 1."""
    non_null = series.dropna()
    if non_null.empty:
        return False
    if not (non_null % 1 == 0).all():
        return False
    diffs = non_null.sort_values().reset_index(drop=True).diff().dropna()
    return bool((diffs == 1).all())


def _is_id_column(column_name: str, series: pd.Series, unique_ratio: float, avg_length: float) -> bool:
    normalized_name = column_name.lower()
    has_id_hint = any(hint in normalized_name for hint in ID_COLUMN_HINTS)

    if pd.api.types.is_numeric_dtype(series):
        return has_id_hint or _is_sequential_index(series)
    

    return has_id_hint or (unique_ratio >= ID_UNIQUE_RATIO and avg_length <= TEXT_AVG_LENGTH)


def schema_detection(df: pd.DataFrame, target: str) -> dict:
    schema = {
        "numerical": [],
        "categorical": [],
        "binary": [],
        "datetime": [],
        "text": [],
        "id_columns": [],
        "drop_columns": [],
    }

    total_rows = len(df)

    for column in df.columns:
        if column == target:
            continue

        series = df[column]
        unique_count = series.nunique(dropna=True)
        missing_ratio = series.isna().mean()
        unique_ratio = unique_count / total_rows if total_rows else 0.0
        avg_length = _object_average_length(series) if series.dtype == "object" else 0.0

        if unique_count <= 1:
            schema["drop_columns"].append(column)
            log.debug("Drop constant column: %s", column)
            continue

        if missing_ratio > MISSING_DROP_THRESHOLD:
            schema["drop_columns"].append(column)
            log.debug("Drop high-missing column (%s): %s", f"{missing_ratio:.0%}", column)
            continue

        if _is_binary(series):
            schema["binary"].append(column)
            log.debug("Binary column: %s", column)
            continue

        if _detect_datetime(series):
            schema["datetime"].append(column)
            log.debug("Datetime column: %s", column)
            continue

        if series.dtype == "object" and avg_length > TEXT_AVG_LENGTH and unique_ratio > 0.3:
            schema["text"].append(column)
            log.debug("Text column: %s", column)
            continue

        if _is_id_column(column, series, unique_ratio, avg_length):
            schema["id_columns"].append(column)
            log.debug("ID-like column: %s", column)
            continue

        if _is_numeric_categorical(series):
            schema["categorical"].append(column)
            log.debug("Numeric-coded categorical column: %s", column)
            continue

        if pd.api.types.is_numeric_dtype(series):
            schema["numerical"].append(column)
            log.debug("Numerical column: %s", column)
            continue

        schema["categorical"].append(column)
        log.debug("Categorical column: %s", column)

    for bucket, columns in schema.items():
        if columns:
            log.info("%s -> %s", f"{bucket:<15}", columns)

    return schema
