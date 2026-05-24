import numpy as np
import pandas as pd


def sanitize(obj):
    """
    Recursively convert numpy / pandas objects into JSON-safe Python values.
    """
    if isinstance(obj, dict):
        return {str(key): sanitize(value) for key, value in obj.items()}

    if isinstance(obj, list):
        return [sanitize(value) for value in obj]

    # pd.NaT is not a float or numpy type — falls through to `return obj`
    # without this check, which crashes json.dump.
    if obj is pd.NaT:
        return None

    # pd.NA (nullable integer / boolean extension type) also crashes json.dump.
    try:
        if pd.isna(obj) and not isinstance(obj, float):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(obj, pd.DataFrame):
        return {
            str(column): {str(index): sanitize(value) for index, value in obj[column].items()}
            for column in obj.columns
        }

    if isinstance(obj, pd.Series):
        return {str(key): sanitize(value) for key, value in obj.items()}

    if isinstance(obj, np.ndarray):
        return [sanitize(value) for value in obj.tolist()]

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return None if (np.isnan(obj) or np.isinf(obj)) else float(obj)

    if isinstance(obj, np.bool_):
        return bool(obj)

    if isinstance(obj, float):
        return None if (np.isnan(obj) or np.isinf(obj)) else obj

    return obj