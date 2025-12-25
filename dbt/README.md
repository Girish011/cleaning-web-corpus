# dbt Project for Cleaning Warehouse

This dbt project transforms raw ClickHouse data into analytical models for the cleaning workflow corpus.

## Setup

1. Install dbt-clickhouse:
   ```bash
   pip install dbt-clickhouse
   ```

2. Verify connection:
   ```bash
   cd dbt
   dbt debug
   ```

## Running dbt

```bash
# Navigate to dbt directory
cd dbt

# Run all models
dbt run

# Run specific model
dbt run --select stg_documents

# Run tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

## Project Structure

- `models/sources/` - Source definitions for ClickHouse tables
- `models/staging/` - Staging models (cleaned, normalized data)
- `models/dimensions/` - Dimension tables (future)
- `models/facts/` - Fact tables (aggregated metrics)

## Connection

The project connects to ClickHouse using settings from `profiles.yml`:
- Host: localhost
- Port: 9000
- Database: cleaning_warehouse
- User: default
- Password: default

