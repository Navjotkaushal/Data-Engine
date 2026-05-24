from pipeline import run_pipeline 
import pandas as pd 
import json 

def test_full_pipeline(messy_dataframe, tmp_path):
    
    dataset_path = tmp_path / "messy_data.csv"
    messy_dataframe.to_csv(dataset_path, index = False)
    
    # Running the pipeline 
    report = run_pipeline(dataset_path=str(dataset_path),
                          target = "target",
                          output_dir=tmp_path,
                          interactive=False
                          )
    
    # Verify output exists 
    assert( tmp_path / "clean_output.csv").exists()
    assert( tmp_path / "dil_report.json").exists()
    
    # Verifying transformation worked 
    clean_df = pd.read_csv(tmp_path / "clean_output.csv")
    assert clean_df.isna().sum().sum() == 0
    assert "id_col" not in clean_df.columns
    