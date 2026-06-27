"""
reporting_system/html_reporter.py
──────────────────────────────────
Generates a self-contained HTML summary page from the pipeline report dict.
Drops the result into  data/output/reports/<dataset_name>_report.html
and returns the path.

If your project already has an html_reporter.py / generate_html_report,
rename this file and call yours instead from api/routes/pipeline.py.
"""
from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "data" / "output" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_html_report(report: dict, dataset_name: str) -> Path:
    """Render report dict → HTML file. Returns the output path."""
    html = _render(report, dataset_name)
    out_path = REPORTS_DIR / f"{dataset_name}_report.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


# ── Rendering helpers ─────────────────────────────────────────────────────────

def _render(r: dict, name: str) -> str:
    shape_raw = r.get("dataset_shape", ["?", "?"])
    shape_clean = r.get("clean_shape", ["?", "?"])
    target = r.get("target", "—")
    schema: dict = r.get("schema", {})
    stats: dict = r.get("stats", {})
    quality: dict = r.get("quality_report", {})
    decisions: dict = r.get("decisions", {})

    rows_removed = (shape_raw[0] - shape_clean[0]) if isinstance(shape_raw[0], int) else "?"
    cols_removed = (shape_raw[1] - shape_clean[1]) if isinstance(shape_raw[1], int) else "?"

    raw_row_count = shape_raw[0] if isinstance(shape_raw[0], int) else 0
    health_score = _health_score(quality, raw_row_count)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Data Engine Report – {name}</title>
<style>
  :root {{
    --bg: #0f172a; --surface: #1e293b; --card: #253047;
    --accent: #6366f1; --accent2: #06b6d4;
    --green: #22c55e; --red: #ef4444; --yellow: #f59e0b;
    --text: #e2e8f0; --muted: #94a3b8; --border: #334155;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg);
          color: var(--text); min-height: 100vh; }}
  header {{ background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
             border-bottom: 1px solid var(--accent); padding: 2rem 2.5rem; }}
  header h1 {{ font-size: 1.8rem; font-weight: 700; color: #fff; }}
  header h1 span {{ color: var(--accent); }}
  header p {{ color: var(--muted); margin-top: .3rem; font-size: .9rem; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1.5rem; }}
  .grid-4 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
              gap: 1rem; margin-bottom: 2rem; }}
  .stat-card {{ background: var(--card); border: 1px solid var(--border);
                border-radius: 10px; padding: 1.2rem 1.4rem; }}
  .stat-card .label {{ font-size: .75rem; text-transform: uppercase;
                        letter-spacing: .06em; color: var(--muted); }}
  .stat-card .value {{ font-size: 1.9rem; font-weight: 700; margin-top: .2rem; }}
  .stat-card .sub {{ font-size: .8rem; color: var(--muted); margin-top: .15rem; }}
  section {{ margin-bottom: 2.5rem; }}
  section h2 {{ font-size: 1.1rem; font-weight: 600; color: var(--accent2);
                border-left: 3px solid var(--accent2); padding-left: .75rem;
                margin-bottom: 1rem; }}
  table {{ width: 100%; border-collapse: collapse; background: var(--surface);
            border-radius: 8px; overflow: hidden; }}
  th {{ background: var(--card); color: var(--muted); font-size: .75rem;
        text-transform: uppercase; letter-spacing: .06em; padding: .75rem 1rem;
        text-align: left; }}
  td {{ padding: .7rem 1rem; font-size: .875rem; border-top: 1px solid var(--border); }}
  tr:hover td {{ background: rgba(99,102,241,.06); }}
  .badge {{ display: inline-block; padding: .15rem .55rem; border-radius: 999px;
             font-size: .7rem; font-weight: 600; }}
  .badge-int    {{ background: rgba(99,102,241,.2); color: #a5b4fc; }}
  .badge-float  {{ background: rgba(6,182,212,.2); color: #67e8f9; }}
  .badge-str    {{ background: rgba(34,197,94,.2); color: #86efac; }}
  .badge-date   {{ background: rgba(245,158,11,.2); color: #fcd34d; }}
  .badge-other  {{ background: rgba(148,163,184,.15); color: var(--muted); }}
  .badge-yes  {{ background: rgba(34,197,94,.2); color: #86efac; }}
  .badge-no   {{ background: rgba(239,68,68,.2); color: #fca5a5; }}
  .decisions-grid {{ display: grid;
                      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                      gap: .75rem; }}
  .dec-card {{ background: var(--surface); border: 1px solid var(--border);
                border-radius: 8px; padding: 1rem 1.2rem; }}
  .dec-card .col-name {{ font-weight: 600; color: var(--text); margin-bottom: .5rem; }}
  .dec-card .actions {{ list-style: none; }}
  .dec-card .actions li {{ font-size: .82rem; color: var(--muted);
                             padding: .2rem 0; display: flex; gap: .4rem; }}
  .dec-card .actions li::before {{ content: "→"; color: var(--accent); }}
  .json-block {{ background: var(--surface); border: 1px solid var(--border);
                  border-radius: 8px; padding: 1.2rem; font-family: monospace;
                  font-size: .8rem; color: #94a3b8; white-space: pre-wrap;
                  overflow-x: auto; max-height: 400px; overflow-y: auto; }}
  footer {{ text-align: center; padding: 2rem; color: var(--muted); font-size: .8rem;
             border-top: 1px solid var(--border); margin-top: 2rem; }}
</style>
</head>
<body>
<header>
  <h1>Data <span>Engine</span> Report</h1>
  <p>Dataset: <strong>{name}</strong> &nbsp;|&nbsp; Target column: <strong>{target}</strong></p>
</header>
<main>

  <!-- ── Overview cards ── -->
  <div class="grid-4">
    {_stat_card("Raw Rows", shape_raw[0], "before cleaning")}
    {_stat_card("Clean Rows", shape_clean[0], f"{rows_removed} removed", color="var(--green)")}
    {_stat_card("Raw Columns", shape_raw[1], "before cleaning")}
    {_stat_card("Clean Columns", shape_clean[1], f"{cols_removed} removed", color="var(--accent2)")}
    {_stat_card("Health Score", f"{health_score}/100", "heuristic, see notes", color="var(--green)" if health_score >= 70 else "var(--yellow)" if health_score >= 40 else "var(--red)")}
  </div>

  <!-- ── Schema ── -->
  <section>
    <h2>Schema Detection</h2>
    {_schema_table(schema)}
  </section>

  <!-- ── Data Quality ── -->
  <section>
    <h2>Data Quality Report</h2>
    {_quality_table(quality)}
  </section>

  <!-- ── Stats ── -->
  <section>
    <h2>Column Statistics</h2>
    {_stats_table(stats)}
  </section>

  <!-- ── Decisions ── -->
  <section>
    <h2>Decision Engine – Applied Transformations</h2>
    {_decisions_grid(decisions)}
  </section>

  <!-- ── Raw JSON ── -->
  <section>
    <h2>Full JSON Report</h2>
    <pre class="json-block">{json.dumps(r, indent=2, default=str)}</pre>
  </section>

</main>
<footer>Generated by Data Engine &nbsp;·&nbsp; {_now()}</footer>
</body>
</html>"""


def _health_score(quality: dict, total_rows: int) -> float:
    """
    Heuristic 0-100 data health score derived from quality_report.
    Not a statistically validated metric — a simple weighted deduction
    from 100 based on how many issues were flagged and their severity.
    """
    score = 100.0

    dup_rows = quality.get("duplicate_rows", 0)
    if total_rows:
        dup_ratio = dup_rows / total_rows
        score -= min(20.0, dup_ratio * 100)

    score -= min(15.0, len(quality.get("constant_cols", [])) * 3)
    score -= min(15.0, len(quality.get("leakage_cols", [])) * 5)
    score -= min(20.0, len(quality.get("corrupted_cols", {})) * 4)
    score -= min(15.0, len(quality.get("invalid_range_cols", {})) * 4)
    score -= min(15.0, len(quality.get("high_missing_cols", {})) * 3)

    return round(max(0.0, score), 1)


def _stat_card(label, value, sub="", color="var(--accent)"):
    return f"""
    <div class="stat-card">
      <div class="label">{label}</div>
      <div class="value" style="color:{color}">{value}</div>
      <div class="sub">{sub}</div>
    </div>"""


def _type_badge(t: str) -> str:
    t = str(t).lower()
    cls = (
        "badge-int"   if "int"  in t else
        "badge-float" if "float" in t else
        "badge-date"  if "date" in t else
        "badge-str"   if "str"  in t or "obj" in t else
        "badge-other"
    )
    return f'<span class="badge {cls}">{t}</span>'


def _schema_table(schema: dict) -> str:
    if not schema:
        return "<p style='color:var(--muted)'>No schema data.</p>"
    rows = ""
    for col, info in schema.items():
        if isinstance(info, dict):
            dtype = info.get("dtype", info.get("type", "—"))
            nullable = info.get("nullable", info.get("has_nulls", "—"))
        else:
            dtype = str(info)
            nullable = "—"
        nb = f'<span class="badge badge-yes">yes</span>' if str(nullable).lower() in ("true","yes","1") \
             else f'<span class="badge badge-no">no</span>' if str(nullable).lower() in ("false","no","0") \
             else str(nullable)
        rows += f"<tr><td>{col}</td><td>{_type_badge(dtype)}</td><td>{nb}</td></tr>"
    return f"""
    <table>
      <thead><tr><th>Column</th><th>Detected Type</th><th>Nullable</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def _quality_table(quality: dict) -> str:
    if not quality:
        return "<p style='color:var(--muted)'>No quality data.</p>"

    rows = ""

    dup_rows = quality.get("duplicate_rows", 0)
    rows += f"<tr><td>Duplicate rows</td><td colspan='3'>{dup_rows}</td></tr>"

    list_checks = [
        ("Leakage columns", quality.get("leakage_cols", [])),
        ("Constant columns", quality.get("constant_cols", [])),
    ]
    for label, cols in list_checks:
        val = ", ".join(cols) if cols else "none"
        rows += f"<tr><td>{label}</td><td colspan='3'>{val}</td></tr>"

    dict_checks = [
        ("Corrupted values (count)", quality.get("corrupted_cols", {})),
        ("Invalid range (negative count)", quality.get("invalid_range_cols", {})),
        ("High missing ratio", quality.get("high_missing_cols", {})),
    ]
    for label, per_col in dict_checks:
        if not per_col:
            rows += f"<tr><td>{label}</td><td colspan='3'>none</td></tr>"
            continue
        detail = ", ".join(f"{col} ({val})" for col, val in per_col.items())
        rows += f"<tr><td>{label}</td><td colspan='3'>{detail}</td></tr>"

    return f"""
    <table>
      <thead><tr><th>Check</th><th colspan="3">Result</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def _stats_table(stats: dict) -> str:
    if not stats:
        return "<p style='color:var(--muted)'>No stats data.</p>"

    # stats is metric-first: {"missing_count": {col: val, ...}, "skewness": {...}, ...}
    # Pivot to column-first so each row is one column.
    metric_keys = ["missing_count", "missing_ratio", "cardinality", "skewness", "outlier_ratio"]
    columns = set()
    for key in metric_keys:
        per_col = stats.get(key)
        if isinstance(per_col, dict):
            columns.update(per_col.keys())

    if not columns:
        return "<p style='color:var(--muted)'>No per-column stats available.</p>"

    rows = ""
    for col in sorted(columns):
        missing_count = _fmt(stats.get("missing_count", {}).get(col))
        missing_ratio = _fmt(stats.get("missing_ratio", {}).get(col))
        cardinality   = _fmt(stats.get("cardinality", {}).get(col))
        skewness      = _fmt(stats.get("skewness", {}).get(col))
        outlier_ratio = _fmt(stats.get("outlier_ratio", {}).get(col))
        rows += (
            f"<tr><td>{col}</td><td>{missing_count}</td><td>{missing_ratio}</td>"
            f"<td>{cardinality}</td><td>{skewness}</td><td>{outlier_ratio}</td></tr>"
        )

    target_block = ""
    target_summary = stats.get("target_summary")
    if isinstance(target_summary, dict):
        trow = "".join(f"<tr><td>{k}</td><td>{_fmt(v)}</td></tr>" for k, v in target_summary.items())
        target_block = f"""
        <h3 style="margin-top:1.5rem;font-size:.95rem;color:var(--muted)">Target column summary</h3>
        <table style="margin-top:.5rem">
          <thead><tr><th>Metric</th><th>Value</th></tr></thead>
          <tbody>{trow}</tbody>
        </table>"""

    return f"""
    <table>
      <thead><tr><th>Column</th><th>Missing count</th><th>Missing ratio</th><th>Cardinality</th><th>Skewness</th><th>Outlier ratio</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    {target_block}"""


def _decisions_grid(decisions: dict) -> str:
    if not decisions:
        return "<p style='color:var(--muted)'>No decisions recorded.</p>"
    cards = ""
    for col, actions in decisions.items():
        if isinstance(actions, list):
            items = "".join(f"<li>{a}</li>" for a in actions)
        elif isinstance(actions, dict):
            items = "".join(f"<li><b>{k}</b>: {v}</li>" for k, v in actions.items())
        else:
            items = f"<li>{actions}</li>"
        cards += f"""
        <div class="dec-card">
          <div class="col-name">{col}</div>
          <ul class="actions">{items}</ul>
        </div>"""
    return f'<div class="decisions-grid">{cards}</div>'


def _fmt(v) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):.4g}"
    except (TypeError, ValueError):
        return str(v)


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")