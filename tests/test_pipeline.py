import os
from dotenv import load_dotenv
from pipeline.extract import extract_orders

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
