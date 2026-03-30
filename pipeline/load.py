import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

INSERT_SQL = """
    INSERT INTO raw_orders (
        order_id, order_date, order_time, customer_segment,
        order_value, cuisine_type, delivery_time_mins,
        promo_code_used, is_reorder
    ) VALUES (
        %(order_id)s, %(order_date)s, %(order_time)s, %(customer_segment)s,
        %(order_value)s, %(cuisine_type)s, %(delivery_time_mins)s,
        %(promo_code_used)s, %(is_reorder)s
    )
"""


def load_orders(rows):
    conn = psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE raw_orders")
            cur.executemany(INSERT_SQL, rows)
        conn.commit()
    finally:
        conn.close()
