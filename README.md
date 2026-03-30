# Basket Craft Sales Pipeline

ELT pipeline that pulls order data from the Basket Craft MySQL database and loads it into a local PostgreSQL instance for analysis. A SQL view aggregates the data into a monthly sales summary by cuisine type.

## Prerequisites

- Python 3.9+
- Docker Desktop

## Setup

1. Create a `.env` file with your database credentials:

```
MYSQL_HOST=...
MYSQL_PORT=3306
MYSQL_USER=...
MYSQL_PASSWORD=...
MYSQL_DATABASE=basket_craft

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=pipeline
POSTGRES_PASSWORD=pipeline_pass
POSTGRES_DB=basket_craft_dw
```

2. Start Postgres and install dependencies:

```bash
docker compose up -d
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the pipeline:

```bash
source .venv/bin/activate
python -m pipeline.main
```

Query the results:

```bash
docker exec basket_craft_pg psql -U pipeline -d basket_craft_dw \
  -c "SELECT * FROM monthly_sales_summary"
```

## How it works

The pipeline does a full extract-and-reload each run:

1. Extracts all rows from the `orders` table in MySQL
2. Truncates the `raw_orders` staging table in Postgres
3. Bulk-inserts the extracted rows
4. The `monthly_sales_summary` view automatically reflects the latest data -- it computes revenue, order count, and average order value grouped by cuisine type and month

Re-running the pipeline is always safe. The truncate-before-insert pattern prevents duplicates.

## Tests

```bash
pytest tests/test_pipeline.py -v
```

Tests run against real databases (MySQL source and local Postgres), so both must be accessible.
