import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import duckdb, streamlit as st
from pipeline.config import DB_PATH

st.set_page_config(page_title="India Air Quality Monitor", layout="wide")
st.title("India Air Quality & Weather Monitor")
con = duckdb.connect(DB_PATH, read_only=True)

cities = [r[0] for r in con.execute("SELECT DISTINCT city FROM agg_daily ORDER BY 1").fetchall()]
city = st.sidebar.selectbox("City", cities)
last = con.execute("SELECT max(ts) FROM raw_readings").fetchone()[0]
st.sidebar.caption(f"Last data point: {last}")

latest = con.execute("SELECT * FROM stg_readings WHERE city=? AND aqi IS NOT NULL ORDER BY ts DESC LIMIT 1", [city]).df().iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("AQI (US)", int(latest.aqi))
c2.metric("PM2.5 µg/m³", latest.pm25)
c3.metric("Temp °C", latest.temp_c)
c4.metric("Humidity %", latest.humidity)

hourly = con.execute("SELECT ts, aqi, pm25 FROM stg_readings WHERE city=? ORDER BY ts", [city]).df().set_index("ts")
st.subheader("Hourly trend")
st.line_chart(hourly)

st.subheader("City ranking: average AQI, last 7 days")
st.bar_chart(con.execute("""SELECT city, avg(avg_aqi) AS aqi FROM agg_daily
    WHERE day >= (SELECT max(day) FROM agg_daily) - 6 GROUP BY 1 ORDER BY 2 DESC""").df().set_index("city"))

st.subheader("Detected PM2.5 anomalies (|z| > 3)")
st.dataframe(con.execute("SELECT * FROM fct_anomalies WHERE city=? ORDER BY ts DESC LIMIT 20", [city]).df(), use_container_width=True)
