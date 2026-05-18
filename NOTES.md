# Clear Grid Notes

## Running The Demo

The supported demo path is Docker Compose. From the repository root:

```bash
docker compose down -v
docker compose up --build
```

This starts:

- PostgreSQL on `127.0.0.1:5433`
- Flask/Gunicorn API on `127.0.0.1:5000`
- Vite/React SPA on `127.0.0.1:5173`

Open the SPA at:

```text
http://localhost:5173/
```

The `down -v` step clears any stale local database volume from previous runs,
which avoids Postgres password mismatches when environment variables have changed.

On startup the app container runs database migrations with `flask db upgrade`.
By default, `INGEST_ON_STARTUP=true`, so it then runs:

```bash
flask ingest-unit-results --date "$INGEST_DELIVERY_DATE"
```

The default compose settings ingest Habitat Energy unit auction results for
`2026-05-17`.

## Docker Requirement

This submission assumes Docker with Docker Compose is available. If Docker is not
installed, install Docker Desktop from the official Docker documentation:

```text
https://docs.docker.com/get-started/get-docker/
```

After installation, confirm Docker is available:

```bash
docker --version
docker compose version
```

## Configuration

The app can run with the defaults in `compose.yml`. To customize local settings:

```bash
cp .env.example .env
```

Useful variables:

- `INGEST_ON_STARTUP`: defaults to `true`; set to `false` to skip startup ingestion.
- `INGEST_DELIVERY_DATE`: delivery date to ingest, in `YYYY-MM-DD` format.
- `INGEST_PARTICIPANT`: registered auction participant filter.
- `INGEST_RESOURCE_ID`: optional NESO resource id override. If empty, the app uses `NESO_RESOURCE_ID`.
- `NESO_RESOURCE_ID`: NESO datastore resource for response reserve results by unit.

To run ingestion manually after the stack is up:

```bash
docker compose exec app flask ingest-unit-results --date 2026-05-17
```

To inspect ingestion status:

```bash
docker compose exec db psql -U clear_grid -d clear_grid -c \
"select id, status, records_seen, records_inserted, records_updated from ingestion_runs;"
```

## Optional Tools

pgAdmin is available behind the `tools` profile:

```bash
docker compose --profile tools up --build
```

Then open:

```text
http://localhost:8080/
```

## Troubleshooting

If the app logs show `password authentication failed for user "clear_grid"`,
the Postgres volume was probably initialized with a different password from a
previous run. `POSTGRES_PASSWORD` is only used when Postgres first creates the
database volume; changing `.env` later does not update the stored database user.

For a fresh demo database, reset the compose volume:

```bash
docker compose down -v
docker compose up --build
```

## Framework And Library Choices

- Flask provides a small API and CLI surface.
- SQLAlchemy/Alchemical and Flask-Migrate handle models and migrations.
- PostgreSQL is used for the Docker demo because it matches a realistic service setup.
- HTTPX is used for the synchronous NESO client. The ingestion workload is small and intentionally not parallelized; NESO recommends no more than two DataStore API requests per minute, so async support would be more useful later for orchestration than for concurrent request bursts.
- React and Vite provide the lightweight SPA table, search, sorting, and pagination.
- Docker Compose is the documented run path so reviewers do not need a local Python, Node, or PostgreSQL setup.

`requirements.txt` contains runtime dependencies used by the app container.
Developer-only tools such as pytest and Black are kept in `requirements-dev.txt`.

An async NESO client remains a future design option if the project needs multi-resource ingestion or broader workflow coordination.

## Non-Docker Run Path

There is not a fully supported non-Docker demo path. The test suite uses SQLite,
and the app has a SQLite fallback database URL, but the end-to-end demo is intended
to run with Docker Compose. Supporting a polished local-only path would require
documenting separate Python and Node environments, migration setup, and a local
database story. For this submission, Docker is the simpler and more reliable
review path.

## Assumptions And Decisions

- The ingestion filters to `HABITAT ENERGY LIMITED`.
- Startup ingestion uses the same Flask CLI command as manual ingestion, so there is one ingestion path.
- `postgres:17` is pinned to avoid accidental major-version changes from the floating `postgres` image tag.
- The SPA provides a lightweight visualization rather than a full dashboard.
- The root contains operational files such as `compose.yml`, `boot.sh`, `alembic.ini`, and migration files because they are needed for the Docker demo and database startup.
- "Local database" is interpreted as a database that can be run locally by the reviewer. The Docker setup uses a local PostgreSQL container rather than an in-memory database so migrations, persistence, and inspection behave like a real service.

## Planned Improvements

- Add a richer set of filters, including date, quantity, and clearing price.
- Add charts for accepted volume and clearing price over time.
- Add ingestion idempotency/reporting views in the SPA.
- Add retry/backoff behavior around NESO API calls.
- Add a documented local-only setup if Docker were not available.
- Split production and development Docker compose files more cleanly if this were becoming a maintained service.
