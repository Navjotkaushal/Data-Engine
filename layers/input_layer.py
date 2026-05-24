from __future__ import annotations

import re
import shutil
import os
from pathlib import Path

import pandas as pd

from utils.logger import get_logger

log = get_logger(__name__)

RAW_DATA_DIR = Path(__file__).resolve().parent /".."/ "data" / "raw"


def _normalize_name(name: str) -> str:
    
    cleaned = str(name).strip().lower()
    cleaned = re.sub(r"[^\w]", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_")


def load_dataset(path: str | Path) -> pd.DataFrame:
    dataset_path = Path(path).expanduser().resolve()
    df = pd.read_csv(dataset_path)
    log.info("Dataset loaded from %s - shape: %s", dataset_path, df.shape)
    return df


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized_df = df.copy()
    normalized_df.columns = [_normalize_name(col) for col in normalized_df.columns]
    log.debug("Columns normalized: %s", normalized_df.columns.to_list())
    return normalized_df


def ask_target(df: pd.DataFrame) -> str:
    print("\nAvailable Columns:")
    for index, column in enumerate(df.columns, 1):
        print(f"  {index:>3}. {column}")

    raw_input = input("\nEnter target column: ")
    target = _normalize_name(raw_input)

    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in dataset.")

    log.info("Target column set to %s", target)
    return target


def basic_validator(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Dataset is empty; nothing to process.")

    log.info("Dataset validated - shape: %s", df.shape)

    duplicates = int(df.duplicated().sum())
    if duplicates:
        log.warning("%s duplicate rows detected", duplicates)

    return df


def data_input_pipeline(
    path: str | Path | None = None,
    target: str | None = None,
    interactive: bool = True,
) -> tuple[pd.DataFrame | None, str | None, str | None]:
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    try:
        if path is None:
            if not interactive:
                raise ValueError("A dataset path is required in non-interactive mode.")
            path = input("Enter the data file path: ").strip()

        path = Path(path).expanduser().resolve()

        df = load_dataset(path)

        # Save a byte-for-byte copy of the original file before any transformation.
        # Using shutil.copy instead of df.to_csv avoids pandas round-trip changes
        # (scientific notation, float precision loss, date reformatting).
        raw_data_path = RAW_DATA_DIR / f"{path.stem}.csv"
        shutil.copy(src=path, dst=raw_data_path)
        log.info("Raw file saved to %s", raw_data_path)

        df = normalize_columns(df)
        df = basic_validator(df)

        if target is None:
            if not interactive:
                raise ValueError("A target column is required in non-interactive mode.")
            target = ask_target(df)
        else:
            target = _normalize_name(target)
            if target not in df.columns:
                raise ValueError(f"Target column '{target}' not found in dataset.")
            log.info("Target column set to %s", target)

        dataset_name = path.stem

        return df, target, dataset_name

    except Exception as exc:
        log.error("Failed during input layer: %s", exc)
        raise