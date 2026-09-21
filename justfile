set -euo pipefail

default: help

## Run unit tests
test:
	uv run pytest -q

## Run linter
lint:
	uv run ruff check src tests

## Run linter with autofix
lint-fix:
	uv run ruff check --fix src tests

## Format code
format:
	uv run ruff format src tests

## Start Postgres (creates DB, roles, schema on first run)
db-up:
	docker compose up -d

## Stop Postgres
db-down:
	docker compose down

## Stop Postgres and wipe the volume (DB + data)
db-reset:
	docker compose down -v

## Download + extract CMS sample CSVs into data/
fetch:
	uv run python -m phi_guardrails.fetch

## Load CSVs into Postgres (adds to existing data)
load:
	uv run python -m phi_guardrails.load

## Truncate tables, then load CSVs into Postgres
load-fresh:
	uv run python -m phi_guardrails.load --truncate

## Show row counts for both tables
db-counts:
	docker compose exec -T postgres psql -U human001 -d claims_db -c \
		"SELECT 'beneficiary' AS table, COUNT(*) FROM beneficiary \
		 UNION ALL SELECT 'inpatient_claims', COUNT(*) FROM inpatient_claims;"

## Print this help
help:
	@grep -E '^## ' $(justfile) | sed 's/## //'
