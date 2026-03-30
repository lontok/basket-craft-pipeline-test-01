import logging
from pipeline.extract import extract_orders
from pipeline.load import load_orders

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


def run_pipeline():
    log.info("Starting pipeline")
    log.info("Extracting orders from MySQL")
    rows = extract_orders()
    log.info("Extracted %d rows", len(rows))
    log.info("Loading into PostgreSQL")
    load_orders(rows)
    log.info("Loaded %d rows into raw_orders", len(rows))
    log.info("Pipeline complete")


if __name__ == "__main__":
    run_pipeline()
