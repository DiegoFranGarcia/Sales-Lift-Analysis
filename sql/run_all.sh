#!/usr/bin/env bash
set -euo pipefail

psql -f sql/01_schema.sql
psql -c "\copy raw_train FROM 'data/raw/train.csv' WITH (FORMAT csv, HEADER true, NULL '')"
psql -c "\copy raw_store FROM 'data/raw/store.csv' WITH (FORMAT csv, HEADER true, NULL '')"
psql -f sql/02_panel.sql
psql -f sql/03_sample.sql
psql -f sql/99_assertions.sql

echo "Pipeline rebuilt successfully."