import pandas as pd 
from layers.schema_detection import schema_detection 
from layers.data_quality import quality

def test_schema_detection(messy_dataframe):
    target = "target"
    schema = schema_detection(messy_dataframe, target)
    
    assert "is_active" in schema["binary"]
    assert "age" in schema["numerical"]
    assert "city" in schema["categorical"]
    assert "id_col" in schema["id_columns"]
    
def test_data_quality(messy_dataframe):
    target = "target"
    schema = schema_detection(messy_dataframe, target)
    report = quality(messy_dataframe, target, schema)
    
    assert "age" in report["invalid_range_cols"]
    assert report["invalid_range_cols"]["age"] == 1