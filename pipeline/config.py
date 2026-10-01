import os
DB_PATH = os.getenv("WAREHOUSE_PATH", "data/warehouse.duckdb")
CITIES = {
    "Kolhapur": {"lat": 16.70, "lon": 74.24},
    "Pune": {"lat": 18.52, "lon": 73.86},
    "Mumbai": {"lat": 19.08, "lon": 72.88},
    "Delhi": {"lat": 28.61, "lon": 77.21},
    "Bengaluru": {"lat": 12.97, "lon": 77.59},
    "Chennai": {"lat": 13.08, "lon": 80.27},
}
INITIAL_BACKFILL_DAYS = 30
MAX_BACKFILL_DAYS = 90
