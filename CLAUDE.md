# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

ELT pipeline that extracts order data from a remote MySQL database (Basket Craft / campus_bites), loads it into a local PostgreSQL instance running in Docker, and exposes a `monthly_sales_summary` SQL view aggregating revenue, order counts, and average order value by cuisine type and month.

## Commands

```bash
# Start Postgres (required before running pipeline or tests)
docker compose up -d

# Run the pipeline
source .venv/bin/activate
python -m pipeline.main

# Run all tests
pytest tests/test_pipeline.py -v

# Run a single test
pytest tests/test_pipeline.py::test_pipeline_row_count_matches_source -v

# Query the summary view
docker exec basket_craft_pg psql -U pipeline -d basket_craft_dw -c "SELECT * FROM monthly_sales_summary"
```

## Architecture

The pipeline follows an ELT pattern with a truncate-and-reload strategy (full extract every run, idempotent):

1. `pipeline/extract.py` connects to MySQL, runs `SELECT * FROM orders`, returns a list of dicts
2. `pipeline/load.py` truncates `raw_orders` in Postgres, bulk-inserts via `executemany`
3. `pipeline/main.py` orchestrates extract then load with logging
4. `sql/` contains Postgres init scripts mounted into Docker's `/docker-entrypoint-initdb.d` (run once on first container start)
5. `monthly_sales_summary` is a SQL view on `raw_orders` -- always current, no refresh needed

All database credentials are read from `.env` via `python-dotenv`. The `.env` file is gitignored.

## Conventions

- Use a Python virtual environment to manage dependencies.
- Use explicit column names in GROUP BY and ORDER BY clauses, not positional integers.
- Tests are integration tests against real databases (MySQL source + Postgres in Docker). No mocks.
- If the Postgres container schema needs to change, modify the SQL files in `sql/` and recreate the container (`docker compose down -v && docker compose up -d`).
