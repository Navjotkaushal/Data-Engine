# Centralized tuning values for the data engine.

# Schema Detection
MISSING_DROP_THRESHOLD = 0.50
ID_UNIQUE_RATIO = 0.95
DATETIME_VALID_RATIO = 0.80
DATETIME_YEAR_MIN = 1900
DATETIME_YEAR_MAX = 2100
TEXT_AVG_LENGTH = 30
NUMERIC_CATEGORY_MAX_UNIQUE = 15
ID_COLUMN_HINTS = ("id", "uuid", "identifier", "code")

# Data Profiling
OUTLIER_IQR_FACTOR = 1.5
OUTLIER_CAP_IQR_FACTOR = 3.0
TARGET_CLASSIFICATION_MAX_UNIQUE = 20


# Data Quality
HIGH_MISSING_FLAG = 0.35
LEAKAGE_CORR_THRESHOLD = 0.95
NUMERIC_CORRUPTION_RATIO = 0.80
ALWAYS_POSITIVE_HINTS = [
    "age",
    "price",
    "cost",
    "count",
    "quantity",
    "amount",
    "salary",
    "revenue",
    "population",
]

# Decision Engine
SKEW_THRESHOLD = 1.0
HIGH_CARDINALITY_LIMIT = 20
OUTLIER_CAP_THRESHOLD = 0.05


