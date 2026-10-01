import duckdb, pandas as pd, pytest
from pipeline import ingest, quality, transform

def make_df(n=400, spike=False):
    ts = pd.date_range(end=pd.Timestamp.now().floor("h"), periods=n, freq="h")
    pm = [40 + (i % 5) for i in range(n)]
    if spike: pm[-1] = 400
    return pd.DataFrame({"city": "Testville", "ts": ts, "temp_c": 30.0, "humidity": 50.0,
                         "wind_kmh": 5.0, "pm25": pm, "pm10": 60.0, "aqi": 90.0})

@pytest.fixture
def con():
    c = duckdb.connect(":memory:")
    c.execute(ingest.DDL)
    return c

def test_load_is_idempotent(con):
    df = make_df(50)
    ingest.load(con, df); ingest.load(con, df)
    assert con.execute("SELECT count(*) FROM raw_readings").fetchone()[0] == 50

def test_incremental_window(con):
    assert ingest.backfill_days(con, "Testville") == ingest.INITIAL_BACKFILL_DAYS
    ingest.load(con, make_df(48))
    assert ingest.backfill_days(con, "Testville") <= 2

def test_quality_passes_clean_data(con):
    ingest.load(con, make_df(50))
    assert quality.run(con)[0] == []

def test_quality_catches_bad_temp(con):
    df = make_df(50); df.loc[0, "temp_c"] = 999
    ingest.load(con, df)
    assert any("temp" in e for e in quality.run(con)[0])

def test_anomaly_detected(con):
    ingest.load(con, make_df(400, spike=True))
    transform.run(con)
    assert con.execute("SELECT count(*) FROM fct_anomalies").fetchone()[0] >= 1
    assert con.execute("SELECT count(*) FROM agg_daily").fetchone()[0] >= 1
