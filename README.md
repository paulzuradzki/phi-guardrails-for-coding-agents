# phi-guardrails

Local Postgres simulation of PHI data (CMS SYNPUF sample files) for testing
LLM guardrails. Two database roles: `human001` (unrestricted operator) and
`agent001` (restricted, to be defined).

No data is committed to this repo; everything below reproduces it locally.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Docker (with compose)
- Python >= 3.11 (uv handles this)

## Setup

```bash
# 1. Python deps
uv sync

# 2. Credentials
cp .env.example .env   # then edit passwords in .env

# 3. Start Postgres (creates claims_db, both roles, and the schema)
docker compose up -d

# 4. Download + extract the CMS sample CSVs into data/
uv run python -m phi_guardrails.fetch

# 5. Load CSVs into Postgres
uv run python -m phi_guardrails.load
```

## Verify

```bash
docker compose exec postgres psql -U human001 -d claims_db \
  -c "SELECT COUNT(*) FROM beneficiary; SELECT COUNT(*) FROM inpatient_claims;"
```

Expected: ~116k beneficiaries, ~66k inpatient claims.

## Data sets

- Member beneficiary file: https://www.cms.gov/research-statistics-data-and-systems/downloadable-public-use-files/synpufs/downloads/de1_0_2008_beneficiary_summary_file_sample_1.zip
- Inpatient claims file: https://www.cms.gov/research-statistics-data-and-systems/downloadable-public-use-files/synpufs/downloads/de1_0_2008_to_2010_inpatient_claims_sample_1.zip

## Database

| Role | Purpose |
|------|---------|
| `human001` | Unrestricted operator (owns `claims_db`) |
| `agent001` | Restricted role for agent/guardrail testing (permissions TBD) |

Tables: `beneficiary`, `inpatient_claims` (column names are the lowercased
CSV headers).

## Development

```bash
uv run pytest              # tests; DB-backed ones use claims_test and auto-skip when Postgres is down
just db-init-test          # one-off: create claims_test on a container started before it existed
uv run ruff check src tests
```

See `AGENTS.md` for agent instructions.

## Reset

```bash
docker compose down -v     # wipes the volume: DB, data, schema
# then re-run steps 3-5 above
```
