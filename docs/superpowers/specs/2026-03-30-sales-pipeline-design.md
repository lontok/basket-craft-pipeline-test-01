# Basket Craft Monthly Sales Pipeline — Design Spec

## Purpose

Build a data pipeline that extracts order data from the Basket Craft MySQL database, loads it into a local PostgreSQL instance running in Docker, and provides a queryable monthly sales summary by cuisine type.

## Source

- **Database:** MySQL at `db.isba.co:3306`, database `campus_bites`
- **Table:** `orders` (1,132 rows, July 2025 – June 2026)
- **Schema:**
  - `order_id` INT (PK)
  - `order_date` DATE
  - `order_time` TIME
  - `customer_segment` VARCHAR(20) — Dorm, Grad Student, Greek Life, Off-Campus
  - `order_value` DECIMAL(10,2)
  - `cuisine_type` VARCHAR(20) — Asian, Burgers, Mexican, Pizza
  - `delivery_time_mins` INT
  - `promo_code_used` ENUM('Yes','No')
  - `is_reorder` ENUM('Yes','No')

## Destination

- **Database:** PostgreSQL 16 in Docker (via `docker-compose.yml`)
- **Persistence:** Named Docker volume so data survives container restarts

### Tables

`raw_orders` — staging table that mirrors the source schema:

| Column | Type | Notes |
|---|---|---|
| order_id | INT | Primary key |
| order_date | DATE | |
| order_time | TIME | |
| customer_segment | VARCHAR(20) | |
| order_value | NUMERIC(10,2) | |
| cuisine_type | VARCHAR(20) | |
| delivery_time_mins | INT | |
| promo_code_used | VARCHAR(3) | |
| is_reorder | VARCHAR(3) | |

`monthly_sales_summary` — a SQL view on `raw_orders`:

```sql
CREATE VIEW monthly_sales_summary AS
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

## Architecture

```
┌─────────────────┐       ┌──────────────────────────────────────────┐
│  MySQL (source)  │       │         Docker                           │
│  db.isba.co:3306 │       │  ┌──────────────────────────────────┐   │
│                  │       │  │  PostgreSQL 16                    │   │
│  orders table    │       │  │                                  │   │
│  (1,132 rows)    │       │  │  raw_orders        (staging)     │   │
│                  │       │  │       │                           │   │
└────────┬─────────┘       │  │       ▼  SQL VIEW                │   │
         │                 │  │  monthly_sales_summary            │   │
         │  Full extract   │  │  (revenue, count, avg_order_val  │   │
         │  via Python     │  │   by cuisine_type + month)       │   │
         └─────────────────│──►                                  │   │
                           │  └──────────────────────────────────┘   │
                           └──────────────────────────────────────────┘
```

Approach is ELT — extract raw data into Postgres, transform via SQL view.

Extract strategy is full extract (truncate-and-reload). At ~1K rows, incremental extraction would add complexity for no real benefit.

## Project structure

```
basket-craft-pipeline-test-01/
├── docker-compose.yml          # Postgres container definition
├── .env                        # MySQL + Postgres credentials
├── requirements.txt            # pymysql, psycopg2-binary, python-dotenv
├── pipeline/
│   ├── __init__.py
│   ├── extract.py              # Connect to MySQL, SELECT * FROM orders
│   ├── load.py                 # Truncate raw_orders, bulk insert
│   └── main.py                 # Orchestrator: extract -> load
├── sql/
│   ├── 01_create_raw_orders.sql
│   └── 02_create_monthly_summary.sql
└── tests/
    └── test_pipeline.py        # End-to-end integration test
```

## How a run works

1. `docker compose up -d` — starts Postgres. On first run, SQL init scripts create the schema.
2. `python -m pipeline.main` — extracts all rows from MySQL, truncates `raw_orders`, bulk-inserts.
3. Query `monthly_sales_summary` — the view is always current, no extra refresh step.

## Configuration

The `.env` file holds all credentials:

```
# MySQL (source) — already exists
MYSQL_HOST=db.isba.co
MYSQL_PORT=3306
MYSQL_USER=analyst
MYSQL_PASSWORD=go_lions
MYSQL_DATABASE=basket_craft

# PostgreSQL (destination) — added by this pipeline
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=pipeline
POSTGRES_PASSWORD=pipeline_pass
POSTGRES_DB=basket_craft_dw
```

## Dependencies

- `pymysql` — MySQL client
- `psycopg2-binary` — PostgreSQL client
- `python-dotenv` — load `.env` credentials

## Error handling

If MySQL or Postgres is unreachable, the script fails with a clear error message and a non-zero exit code. `TRUNCATE raw_orders` runs before each load, so re-running is always safe — no duplicates. The `docker-compose.yml` includes a Postgres healthcheck so the container only reports ready when it's actually accepting connections.

No retries, alerting, or dead-letter queues. Fail loud, re-run manually.

## Testing

Run the full pipeline against real MySQL and a test Postgres container, then query `monthly_sales_summary` and check that it returns rows with expected columns and non-null values. After load, verify `SELECT COUNT(*) FROM raw_orders` matches the source count (1,132). Tests use pytest. No mocks — the data is small and both databases are accessible.

## Out of scope

- Incremental/CDC extraction
- Scheduling/orchestration framework
- Dashboard UI — this pipeline produces the queryable summary; visualization is separate
- Customer segment dimension — pipeline groups by cuisine_type only
