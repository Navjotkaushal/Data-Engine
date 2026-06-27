# Data Engine

A modular, API-driven data preprocessing pipeline that ingests raw datasets, profiles and cleans them, and produces structured reports. Built with FastAPI, Pydantic, and a layered architecture that separates ingestion, transformation, quality checks, and reporting.

**Live demo:** https://navjotkaushal.github.io/Data-Engine-frontend/

![Report screenshot](data_report.png)
<!-- Replace with an actual screenshot of the HTML report (health score, null severity bars, schema table) -->

---

## What It Does

1. **Accepts file uploads** via REST API or the included frontend (`frontend/index.html`) — drag-and-drop upload with live pipeline status
2. **Runs a preprocessing pipeline** — schema detection → profiling → quality checks → transformation → decision engine
3. **Outputs** cleaned CSVs, JSON summaries, HTML reports, and structured logs
4. **Tracks job state** so the frontend can poll the status of long-running pipelines

---

## Project Structure

```
data_engine/
├── api/                        # FastAPI layer
│   ├── main.py                 # App entry point
│   └── routes/
│       ├── upload.py           # POST /upload
│       ├── pipeline.py         # POST /run-pipeline
│       ├── process.py          # POST /process (one-shot upload + run)
│       ├── report.py           # GET /report/{job_id}
│       └── health.py           # GET /health
│
├── config/
│   ├── settings.py             # Pydantic BaseSettings (env-driven config)
│   └── thresholds.py           # Quality thresholds
│
├── core/
│   └── job_manager.py          # Pipeline job state tracking
│
├── layers/                     # Core pipeline logic
│   ├── input_layer.py          # File ingestion and parsing
│   ├── schema_detection.py     # Column type inference
│   ├── data_profiling.py       # Stats, distributions, null counts
│   ├── data_quality.py         # Validation rules and flagging
│   ├── transformer.py          # Cleaning and transformations
│   └── decision_engine.py      # Automated fix decisions
│
├── reporting_system/
│   ├── stats_engine.py         # Aggregates pipeline metrics
│   ├── html_reporter.py        # Renders HTML report
│   └── templates/
│       └── report_template.html
│
├── frontend/
│   └── index.html              # Drag-and-drop upload UI, polls job status
│
├── data/
│   ├── raw/                    # Uploaded input files (gitignored)
│   └── output/                 # Cleaned CSVs, JSON, HTML reports (gitignored)
│
├── tests/
│   ├── conftest.py
│   ├── test_layers.py
│   ├── test_pipeline.py
│   └── test_api.py
│
├── utils/
│   ├── logger.py
│   └── sanitizer.py
│
├── pipeline.py                 # Core pipeline orchestration (no FastAPI)
└── requirements.txt
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health check |
| `POST` | `/upload` | Upload a raw data file |
| `POST` | `/run-pipeline` | Trigger pipeline on an uploaded file |
| `GET` | `/report/{job_id}` | Fetch the report for a completed job |

---

## Pipeline Layers

Each layer is independently testable and runs in sequence:

```
Input → Schema Detection → Data Profiling → Data Quality → Transformer → Decision Engine → Report
```

| Layer | Responsibility |
|-------|---------------|
| `input_layer` | Parse and load raw file into a DataFrame |
| `schema_detection` | Infer column types (int, float, string, datetime) |
| `data_profiling` | Compute nulls, distributions, outliers, cardinality |
| `data_quality` | Flag rows/columns failing validation rules |
| `transformer` | Apply cleaning (type coercion, imputation, dedup) |
| `decision_engine` | Decide which automated fixes to apply based on thresholds |

---

## Setup

### Prerequisites

- Python 3.10+

### Local Installation

```bash
git clone https://github.com/Navjotkaushal/data-engine.git
cd data-engine

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env           # Fill in your config values
```

### Run the API

```bash
uvicorn api.main:app --reload
```

API docs available at: `http://localhost:8000/docs`

---

## Configuration

All settings are driven by environment variables, loaded via Pydantic `BaseSettings` in `config/settings.py`.

Key variables (set in `.env`):

```env
APP_ENV=development
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE_MB=50
OUTPUT_DIR=data/output
```

Thresholds for data quality decisions (e.g., max null ratio before dropping a column) are configured in `config/thresholds.py`.

---

## Running Tests

```bash
pytest tests/
```

Tests are split by concern:
- `test_layers.py` — unit tests for each pipeline layer
- `test_pipeline.py` — end-to-end pipeline integration tests
- `test_api.py` — FastAPI route tests using `TestClient`

---

## Running the Pipeline Directly (No API)

```bash
python pipeline.py --input data/raw/your_file.csv
```

Outputs will be written to `data/output/`.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| API framework | FastAPI |
| Data validation | Pydantic v2 |
| Data processing | Pandas |
| Reporting | Jinja2 HTML templates |
| Testing | Pytest |

---

## Contributing

1. Branch off `main`
2. Write tests for new pipeline layers
3. Keep pipeline logic in `layers/` and `pipeline.py` — do not add business logic inside API routes
4. Run `pytest` before opening a PR

---

## Author

[Navjot](https://github.com/Navjotkaushal)