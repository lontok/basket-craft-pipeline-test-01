import os

import psycopg2
from dotenv import load_dotenv
from pipeline.extract import extract_orders
from pipeline.load import load_orders
from pipeline.main import run_pipeline

load_dotenv()


def test_extract_orders_returns_rows():
    rows = extract_orders()
    assert len(rows) > 0, "Expected at least one row from MySQL"


def test_extract_orders_has_expected_columns():
    rows = extract_orders()
    first = rows[0]
    expected_keys = {
        "order_id", "order_date", "order_time", "customer_segment",
        "order_value", "cuisine_type", "delivery_time_mins",
        "promo_code_used", "is_reorder",
    }
    assert set(first.keys()) == expected_keys


def get_pg_connection():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )


def test_load_orders_inserts_rows():
    rows = extract_orders()
    load_orders(rows)
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM raw_orders")
            count = cur.fetchone()[0]
    finally:
        conn.close()
    assert count == len(rows), f"Expected {len(rows)} rows, got {count}"


def test_load_is_idempotent():
    rows = extract_orders()
    load_orders(rows)
    load_orders(rows)
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM raw_orders")
            count = cur.fetchone()[0]
    finally:
        conn.close()
    assert count == len(rows), f"Expected {len(rows)} after double load, got {count}"


def test_pipeline_populates_summary_view():
    run_pipeline()
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM monthly_sales_summary LIMIT 1")
            row = cur.fetchone()
            assert row is not None, "Summary view returned no rows"
            cur.execute("SELECT COUNT(*) FROM monthly_sales_summary")
            count = cur.fetchone()[0]
            assert count > 0, "Summary view is empty"
    finally:
        conn.close()


def test_pipeline_row_count_matches_source():
    run_pipeline()
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM raw_orders")
            count = cur.fetchone()[0]
    finally:
        conn.close()
    assert count == 1132, f"Expected 1132 rows, got {count}"
