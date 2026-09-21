# Agent Instructions: phi-guardrails

Local harness for simulating PHI in Postgres to test LLM guardrails.
Data is CMS SYNPUF sample files (synthetic, public), but treat `data/` as
sensitive anyway: it is gitignored and must never be committed.

## Layout

- `src/phi_guardrails/`: package
  - `config.py`: env/.env config (`DatabaseConfig`, `load_config()`)
  - `db.py`: psycopg connection helper (role comes from `.env`)
  - `fetch.py`: download + extract the CMS sample zips into `data/`
  - `load.py`: bulk-load CSVs into Postgres via Polars
- `tests/`: pytest; unit tests plus a few integration tests against the local DB
- `scripts/init/`: SQL run once by the Postgres container on first start
  (roles, schema, and the `claims_test` DB used only by the test suite)
- `docker-compose.yml`: Postgres 16 with `claims_db`, human + agent roles
- `justfile`: helper commands
- `notebooks/dev.ipynb`: raw-SQL exploration notebook

## Commands (just)

Always use the justfile recipes; never invoke `uv run pytest` / `uv run ruff`
manually. Drop to raw `uv run pytest <path>::<test>` only when you need to
target a specific test.

```bash
just help                # list all recipes
just test                # pytest
just lint                # ruff check
just lint-fix            # ruff check --fix
just format              # ruff format
just db-up               # start Postgres (creates DB, roles, schema on first run)
just db-down             # stop Postgres
just db-reset            # stop + wipe volume
just db-init-test        # create claims_test on a running container (idempotent)
just fetch               # download + extract CSVs into data/
just load                # load CSVs (append)
just load-fresh          # TRUNCATE + load
just db-counts           # row counts for both tables
```

## Credentials

- `.env` (gitignored) holds all DB creds; `.env.example` is the template.
- The app connects via a single `DATABASE_URL`. The active role is toggled by
  swapping that value between the human and agent lines in `.env`:
  - `human001` / `fake-human-password`: unrestricted operator (owns the DB)
  - `agent001` / `fake-agent-password`: restricted role for guardrail work
- `DB_USER`, `DB_PASSWORD`, `AGENT_DB_USER`, `AGENT_DB_PASSWORD` in `.env`
  exist only to seed the Docker container (compose + init script); the
  Python code never reads them.
- Creds are obviously fake (local demo). Never print, log, or commit
  credentials. Never dump the environment.
- Do not elaborate on agent permissions until the owner defines the policy.

## PHI / PII in version control: NEVER

- `data/` is gitignored and must never be committed, even though the CMS
  SYNPUF sample is synthetic. Treat it as real PHI.
- Never commit: query results, screenshots of data, notebook outputs
  containing data rows, log files, or anything derived from the DB.
  `notebooks/dev.ipynb` must be committed with **empty outputs** only.
- If data or credentials ever land in git history, treat them as exposed:
  rotate credentials and purge history before pushing.
- Never commit personal file paths (e.g. `/Users/<name>/...`) or personal
  names into code, docs, or notebooks. Use env vars or config for anything
  machine-specific.

## Conventions

- Python >= 3.11, deps managed by `uv` (`pyproject.toml`, pinned versions),
  tests with pytest, lint with ruff (line length 100, rules E/F/I/UP/B/SIM/W).
- Keep things simple: stdlib + psycopg + polars + python-dotenv. No ORM.
- Column names in `scripts/init/02-create-schema.sql` are the lowercased CSV
  headers; keep them in sync if the schema changes.
- New code needs unit tests. Unit tests must not require a running Postgres.
- Integration tests that need a real DB use the `db` fixture in
  `tests/conftest.py`. It connects to `claims_test` only (never `claims_db`),
  auto-skips when Postgres is down, and rolls back on teardown, so tests may
  freely TRUNCATE/INSERT into the real tables there. Stick to the DB-API
  surface (`cursor()`, `execute()`, `fetchall()`, `row["col"]`) so the fixture
  could be pointed at sqlite later. On a container created before
  `03-create-test-db.sql` existed, run `just db-init-test` once.
- `load_table` writes over the connection it is given. Never open a second
  connection inside a helper; an uncommitted lock on the first will hang it.
- `pytest-timeout` caps every test at 30s so a hang fails instead of freezing.
