# Sales Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an ELT pipeline that extracts orders from MySQL, loads them into Postgres (Docker), and exposes a monthly sales summary view.

**Architecture:** Python scripts extract all rows from MySQL and bulk-load into a `raw_orders` staging table in Postgres. A SQL view `monthly_sales_summary` aggregates by cuisine type and month. Docker Compose manages the Postgres container.

**Tech Stack:** Python 3.9+, pymysql, psycopg2-binary, python-dotenv, Docker Compose, PostgreSQL 16, pytest

---

## File structure

```
basket-craft-pipeline-test-01/
├── docker-compose.yml
├── .env                        # already exists with MySQL creds; add Postgres creds
├── requirements.txt
├── pipeline/
│   ├── __init__.py
│   ├── extract.py
│   ├── load.py
│   └── main.py
├── sql/
│   ├── 01_create_raw_orders.sql
│   └── 02_create_monthly_summary.sql
└── tests/
    └── test_pipeline.py
```

---

### Task 1: Docker Compose and SQL init scripts

**Files:**
- Create: `docker-compose.yml`
- Create: `sql/01_create_raw_orders.sql`
- Create: `sql/02_create_monthly_summary.sql`
- Modify: `.env` (add Postgres credentials)

- [ ] **Step 1: Add Postgres credentials to `.env`**

Append to the existing `.env` file:

```
# PostgreSQL (destination)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=pipeline
POSTGRES_PASSWORD=pipeline_pass
POSTGRES_DB=basket_craft_dw
```

- [ ] **Step 2: Create `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:16
    container_name: basket_craft_pg
    env_file: .env
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "${POSTGRES_PORT}:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./sql:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pg_data:
```

- [ ] **Step 3: Create `sql/01_create_raw_orders.sql`**

```sql
CREATE TABLE IF NOT EXISTS raw_orders (
    order_id INT PRIMARY KEY,
    order_date DATE NOT NULL,
    order_time TIME NOT NULL,
    customer_segment VARCHAR(20) NOT NULL,
    order_value NUMERIC(10,2) NOT NULL,
    cuisine_type VARCHAR(20) NOT NULL,
    delivery_time_mins INT NOT NULL,
    promo_code_used VARCHAR(3) NOT NULL,
    is_reorder VARCHAR(3)
);
```

- [ ] **Step 4: Create `sql/02_create_monthly_summary.sql`**

```sql
CREATE OR REPLACE VIEW monthly_sales_summary AS
SELECT
    DATE_TRUNC('month', order_date) AS month,
    cuisine_type,
    COUNT(*) AS order_count,
    SUM(order_value) AS total_revenue,
    AVG(order_value) AS avg_order_value
FROM raw_orders
GROUP BY DATE_TRUNC('month', order_date), cuisine_type
ORDER BY DATE_TRUNC('month', order_date), cuisine_type;
```

- [ ] **Step 5: Start the container and verify**

Run:
```bash
docker compose up -d
```

Wait for healthy status, then verify the schema was created:
```bash
docker exec basket_craft_pg psql -U pipeline -d basket_craft_dw -c "\dt"
docker exec basket_craft_pg psql -U pipeline -d basket_craft_dw -c "\dv"
```

Expected: `raw_orders` table and `monthly_sales_summary` view both exist.

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml sql/
git commit -m "Add Docker Compose for Postgres and SQL init scripts"
```

Do NOT commit `.env` — it is already in `.gitignore`.

---

### Task 2: Python environment and dependencies

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Create `requirements.txt`**

```
pymysql==1.1.1
psycopg2-binary==2.9.10
python-dotenv==1.1.0
pytest==8.3.5
```

- [ ] **Step 2: Create virtual environment and install**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "Add requirements.txt with pipeline dependencies"
```

---

### Task 3: Extract module

**Files:**
- Create: `pipeline/__init__.py`
- Create: `pipeline/extract.py`
- Create: `tests/test_pipeline.py`

- [ ] **Step 1: Create `pipeline/__init__.py`**

Empty file:
```python
```

- [ ] **Step 2: Write the failing test for extraction**

Create `tests/test_pipeline.py`:

```python
import os
import pymysql
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run:
```bash
source .venv/bin/activate
pytest tests/test_pipeline.py -v
```

Expected: FAIL — `pipeline.extract` does not exist yet.

- [ ] **Step 4: Implement `pipeline/extract.py`**

```python
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()


def extract_orders():
    connection = pymysql.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ["MYSQL_PORT"]),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM orders")
            rows = cursor.fetchall()
    finally:
        connection.close()
    return rows
```

- [ ] **Step 5: Run tests to verify they pass**

Run:
```bash
pytest tests/test_pipeline.py -v
```

Expected: both `test_extract_orders_returns_rows` and `test_extract_orders_has_expected_columns` PASS.

- [ ] **Step 6: Commit**

```bash
git add pipeline/ tests/
git commit -m "Add extract module with MySQL connection and tests"
```

---

### Task 4: Load module

**Files:**
- Create: `pipeline/load.py`
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test for loading**

Append to `tests/test_pipeline.py`:

```python
import psycopg2
from pipeline.load import load_orders


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
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run:
```bash
pytest tests/test_pipeline.py::test_load_orders_inserts_rows -v
```

Expected: FAIL — `pipeline.load` does not exist yet.

- [ ] **Step 3: Implement `pipeline/load.py`**

```python
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
            for row in rows:
                cur.execute(INSERT_SQL, row)
        conn.commit()
    finally:
        conn.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_pipeline.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/load.py tests/test_pipeline.py
git commit -m "Add load module with truncate-and-reload and tests"
```

---

### Task 5: Main orchestrator

**Files:**
- Create: `pipeline/main.py`
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test for the summary view**

Append to `tests/test_pipeline.py`:

```python
from pipeline.main import run_pipeline


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_pipeline.py::test_pipeline_populates_summary_view -v
```

Expected: FAIL — `pipeline.main` does not exist yet.

- [ ] **Step 3: Implement `pipeline/main.py`**

```python
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
```

- [ ] **Step 4: Run all tests**

Run:
```bash
pytest tests/test_pipeline.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Run the pipeline manually and verify**

Run:
```bash
source .venv/bin/activate
python -m pipeline.main
```

Expected output:
```
... INFO Starting pipeline
... INFO Extracting orders from MySQL
... INFO Extracted 1132 rows
... INFO Loading into PostgreSQL
... INFO Loaded 1132 rows into raw_orders
... INFO Pipeline complete
```

Then query the summary:
```bash
docker exec basket_craft_pg psql -U pipeline -d basket_craft_dw -c "SELECT * FROM monthly_sales_summary"
```

Expected: 48 rows (12 months x 4 cuisine types).

- [ ] **Step 6: Commit**

```bash
git add pipeline/main.py tests/test_pipeline.py
git commit -m "Add pipeline orchestrator and end-to-end tests"
```

---

## Self-review notes

- Spec coverage: all sections covered. Docker, raw_orders, view, extract, load, main, .env config, testing, error handling (fail loud via exceptions).
- No placeholders: every step has complete code.
- Type consistency: `extract_orders()` returns `list[dict]`, `load_orders(rows)` accepts `list[dict]`, `run_pipeline()` calls both. `INSERT_SQL` uses `%(key)s` dict parameterization matching pymysql's DictCursor output.
- The `ORDER BY` in the view definition won't be honored in a view on some Postgres versions (the optimizer can ignore it). This is fine — consumers can add their own ORDER BY when querying. Leaving it in because it documents intended sort order and the spec includes it.
