import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def messy_dataframe():
    """A slightly larger mock dataframe to properly trigger thresholds."""
    data = {
        "id_col": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        # Added a decimal (25.5) so it doesn't get flagged as an integer-category
        "age": [25.5, 30.0, -5.0, 40.0, np.nan, 22.0, 28.0, 35.0, 45.0, 50.0],
        # Added duplicate salaries so the unique_ratio drops below the ID threshold
        "salary": [50000, 60000, 1000000, 55000, 50000, 62000, 60000, 58000, 55000, 50000],
        "city": ["New York", "London", "London", np.nan, "Paris", "New York", "Paris", "London", np.nan, "Tokyo"],
        "is_active": [1, 0, 1, 1, 0, 1, 0, 1, 1, 0],
        "target": [0, 1, 0, 1, 1, 0, 1, 0, 1, 0]
    }
    return pd.DataFrame(data)