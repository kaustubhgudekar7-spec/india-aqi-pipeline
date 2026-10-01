# India Air Quality & Weather Pipeline

Automated ELT pipeline + live dashboard tracking hourly AQI, PM2.5 and weather for 6 Indian cities (Open-Meteo, no API key).

```
Open-Meteo APIs -> ingest (incremental, idempotent upsert) -> DuckDB raw_readings
  -> quality gates (fail-fast) -> SQL models (stg -> agg_daily, fct_anomalies) -> Streamlit
```

## Features
- **Incremental loads**: fetches only the gap since the last timestamp per city; upserts on (city, ts), so reruns are safe.
- **Data-quality gates**: range, null and freshness checks; errors exit non-zero and fail the CI run.
- **Anomaly detection**: rolling 7-day z-score on PM2.5 in pure SQL window functions.
- **CI/CD**: GitHub Actions runs tests and the pipeline every 3 hours.
- **Containerized**: `docker build -t aqi . && docker run -p 8501:8501 aqi`

## Run locally
```
pip install -r requirements.txt
python -m pipeline.run
streamlit run dashboard/app.py
pytest
```

## Add your own numbers (for your resume)
After a few days of runs, measure: `SELECT count(*) FROM raw_readings;`, runtime from the log line, tests passing, cities covered.
