from __future__ import annotations

import os
import joblib
import pandas as pd
from config.thresholds import OUTLIER_IQR_FACTOR, OUTLIER_CAP_IQR_FACTOR
from pathlib import Path
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, OneHotEncoder, StandardScaler

from utils.logger import get_logger

log = get_logger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "output", "cleaned_data")


def _build_onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def _extract_datetime_features(df: pd.DataFrame, datetime_cols: list[str]) -> pd.DataFrame:
    transformed_df = df.copy()

    for column in datetime_cols:
        if column not in transformed_df.columns:
            continue

        parsed = pd.to_datetime(transformed_df[column], errors="coerce")
        transformed_df[f"{column}_year"] = parsed.dt.year
        transformed_df[f"{column}_month"] = parsed.dt.month
        transformed_df[f"{column}_day"] = parsed.dt.day
        transformed_df[f"{column}_dayofweek"] = parsed.dt.dayofweek
        transformed_df.drop(columns=column, inplace=True)
        log.info("Extracted datetime features from %s", column)

    return transformed_df


def transformer(
    df: pd.DataFrame,
    decisions: dict,
    target: str,
    output_dir: str | None = None,
    dataset_name: str = "output",
) -> pd.DataFrame:
    
    """
    Apply all transformations defined by the decision layer.
    Returns a clean, ML-ready DataFrame and saves it as CSV.
    """
    
    transformed_df = df.copy()
    final_output_dir = output_dir or OUTPUT_DIR
    os.makedirs(final_output_dir, exist_ok=True)
    
    
    drop_cols = [column for column in decisions.get("drop_cols", []) if column in transformed_df.columns]
    if drop_cols:
        transformed_df = transformed_df.drop(columns=drop_cols)
        log.info("Dropped columns: %s", drop_cols)

    if decisions.get("drop_duplicates", False):
        before = len(transformed_df)
        transformed_df = transformed_df.drop_duplicates().reset_index(drop=True)
        log.info("Dropped %s duplicate rows", before - len(transformed_df))

    datetime_cols = decisions.get("extract_datetime", [])
    if datetime_cols:
        transformed_df = _extract_datetime_features(transformed_df, datetime_cols)

    for column in decisions.get("impute_mean", []):
        if column in transformed_df.columns and transformed_df[column].isna().any():
            fill_value = transformed_df[column].mean()
            transformed_df[column] = transformed_df[column].fillna(fill_value)
            log.info("Imputed mean (%.2f): %s", fill_value, column)

    for column in decisions.get("impute_median", []):
        if column in transformed_df.columns and transformed_df[column].isna().any():
            fill_value = transformed_df[column].median()
            transformed_df[column] = transformed_df[column].fillna(fill_value)
            log.info("Imputed median (%.2f): %s", fill_value, column)

    for column in decisions.get("impute_mode", []):
        if column in transformed_df.columns and transformed_df[column].isna().any():
            fill_value = transformed_df[column].mode(dropna=True)
            if not fill_value.empty:
                transformed_df[column] = transformed_df[column].fillna(fill_value.iloc[0])
                log.info("Imputed mode (%s): %s", fill_value.iloc[0], column)

    for column, value in decisions.get("impute_constant", {}).items():
        if column in transformed_df.columns:
            transformed_df[column] = transformed_df[column].fillna(value)
            log.info("Imputed constant (%s): %s", value, column)

    for column in decisions.get("cap_outliers", []):
        if column not in transformed_df.columns:
            continue

        q1 = transformed_df[column].quantile(0.25)
        q3 = transformed_df[column].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - OUTLIER_CAP_IQR_FACTOR * iqr
        upper = q3 + OUTLIER_CAP_IQR_FACTOR * iqr
        outlier_count = int(((transformed_df[column] < lower) | (transformed_df[column] > upper)).sum())
        transformed_df[column] = transformed_df[column].clip(lower=lower, upper=upper)
        log.info("Capped %s outliers in %s", outlier_count, column)

    onehot_cols = [column for column in decisions.get("encode_onehot", []) if column in transformed_df.columns]
    if onehot_cols:
        encoder = _build_onehot_encoder()
        encoded = encoder.fit_transform(transformed_df[onehot_cols].astype(str))
        encoded_df = pd.DataFrame(
            encoded,
            columns=encoder.get_feature_names_out(onehot_cols),
            index=transformed_df.index,
        )
        transformed_df = pd.concat(
            [transformed_df.drop(columns=onehot_cols), encoded_df],
            axis=1,
        )
        log.info("One-hot encoded columns: %s", onehot_cols)



    for column in decisions.get("encode_label", []):
        if column not in transformed_df.columns:
            continue
        encoder = LabelEncoder()
        transformed_df[column] = encoder.fit_transform(transformed_df[column].astype(str))
        log.info("Label encoded: %s", column)


    std_cols = [column for column in decisions.get("scale_standard", []) if column in transformed_df.columns]
    if std_cols:
        scaler = StandardScaler()
        transformed_df[std_cols] = scaler.fit_transform(transformed_df[std_cols])
        log.info("Applied standard scaling: %s", std_cols)

    minmax_cols = [column for column in decisions.get("scale_minmax", []) if column in transformed_df.columns]
    if minmax_cols:
        scaler = MinMaxScaler()
        transformed_df[minmax_cols] = scaler.fit_transform(transformed_df[minmax_cols])
        log.info("Applied min-max scaling: %s", minmax_cols)


    if target in transformed_df.columns:
        ordered_cols = [column for column in transformed_df.columns if column != target] + [target]
        transformed_df = transformed_df[ordered_cols]
    
    output_path = Path(final_output_dir) / f"{Path(dataset_name).stem}_cleaned.csv"
    transformed_df.to_csv(output_path, index = False)

    log.info("Clean CSV saved to %s", os.path.abspath(output_path))
    log.info("Final shape: %s rows x %s columns", transformed_df.shape[0], transformed_df.shape[1])

    return transformed_df
