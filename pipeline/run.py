import logging, os, sys, time
import duckdb
from . import ingest, quality, transform
from .config import DB_PATH

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pipeline")

def main():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    con = duckdb.connect(DB_PATH)
    t0 = time.time()
    rows = ingest.run(con)
    errors, warns = quality.run(con)
    for w in warns:
        log.warning("QUALITY WARN %s", w)
    if errors:
        log.error("QUALITY FAIL %s", errors)
        sys.exit(1)  # non-zero exit -> CI marks the run failed -> alert
    transform.run(con)
    log.info("done: %d rows ingested in %.1fs", rows, time.time() - t0)

if __name__ == "__main__":
    main()
