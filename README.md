# MLflow with PostgreSQL and RustFS - Docker Setup

This Docker Compose setup provides a complete MLflow tracking server with:
- **PostgreSQL** for metadata and experiment tracking
- **RustFS** for artifact storage (S3-compatible)
- **MLflow Server** for experiment tracking and model registry

## Prerequisites

- Docker Desktop for Mac installed and running
- At least 4GB of RAM allocated to Docker

## Quick Start

1. **Copy and configure the environment file:**
   ```bash
   cp .env.example .env
   # Edit .env to customize ports, credentials, or MLflow version
   ```

2. **Create the volumes directories:**
   ```bash
   mkdir -p ~/volumes/postgres ~/volumes/rustfs ~/volumes/postgres-backups
   # RustFS runs as UID 10001; on a native Linux host: sudo chown -R 10001:10001 ~/volumes/rustfs
   ```

3. **Start the services:**
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to be ready** (usually takes 30-60 seconds):
   ```bash
   docker-compose logs -f mlflow
   ```
   Wait until you see "Listening at: http://0.0.0.0:5000"

5. **Access the services** (using default `.env` values):
   - MLflow UI: http://localhost:5010
   - RustFS Console: http://localhost:9001 (user: `rustfs`, password: `rustfs123`)
   - PostgreSQL: localhost:5432 (user: `mlflow`, password: `mlflow123`, db: `mlflow`)

## Configuration

All configurable values live in `.env`. Copy `.env.example` as a starting point.

### Ports

| Variable | Default | Description |
|---|---|---|
| `MLFLOW_PORT` | `5010` | Host port for the MLflow UI |
| `POSTGRES_PORT` | `5432` | Host port for PostgreSQL |
| `RUSTFS_API_PORT` | `9000` | Host port for the RustFS S3 API |
| `RUSTFS_CONSOLE_PORT` | `9001` | Host port for the RustFS web console |

### Credentials

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `mlflow` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `mlflow123` | PostgreSQL password |
| `POSTGRES_DB` | `mlflow` | PostgreSQL database name |
| `RUSTFS_ROOT_USER` | `rustfs` | RustFS root username |
| `RUSTFS_ROOT_PASSWORD` | `rustfs123` | RustFS root password |
| `RUSTFS_BUCKET` | `mlflow` | RustFS bucket for artifacts |

### GenAI / LLM Endpoint

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | _(empty)_ | OpenAI API key for GenAI evaluation |
| `ANTHROPIC_API_KEY` | _(empty)_ | Anthropic API key for GenAI evaluation |
| `OPENAI_API_BASE` | `http://host.docker.internal:1234/v1` | OpenAI-compatible API endpoint — override to point at a local LLM (e.g. LM Studio, vLLM) |

### MLflow Assistant (Beta)

The in-UI assistant is **localhost-only by design** — it can run the MLflow CLI and edit
project code, so MLflow refuses to expose it to anything but the machine running the
server. Behind Docker the browser is never seen as localhost (Docker's port proxy rewrites
the source address to the bridge gateway), so out of the box every assistant call fails
with:

> Error: You do not have permission to access this resource.

Two things make it work here, both already wired into `docker-compose.yml`:

1. `MLFLOW_ENABLE_REMOTE_ASSISTANT=true` lifts the localhost restriction — but **only for
   providers that declare `allows_remote_access`**. Ollama and plain OpenAI-compatible
   providers stay blocked no matter what; the practical choice is **MLflow AI Gateway**,
   which is safe remotely because the LLM call is proxied server-side.
2. `MLFLOW_PORT` is used as both the host and container port. The assistant builds its
   self-call URL to the in-server gateway from the browser's `Host` header, so a host port
   that differs from the container's listen port makes the server dial a port it isn't
   bound to.

`PUT /config` and `POST /skills/install` keep a hard DENY policy and stay blocked from a
browser regardless — so **the Save button in the assistant settings panel will not work**,
and provider selection has to happen server-side. Use the helper script:

```bash
# Point the assistant at a local Ollama model (the container mounts ./scripts at /scripts)
docker compose exec mlflow python /scripts/setup_assistant.py \
  --base-url http://host.docker.internal:11434/v1 \
  --model qwen3:14b

# The gateway caches resolved endpoint configs, so restart after any change
docker compose restart mlflow
```

#### Selecting endpoints in the UI (Ollama *and* LM Studio)

`docker-compose.yml` runs MLflow bound to loopback inside the container and puts a
`socat` relay in front of it, in the same container, forwarding the published port to
that listener. The server then sees a real `127.0.0.1` peer, so **the whole assistant UI
works** — including the endpoint dropdown and the settings Save button. Every AI Gateway
endpoint you create under **LLM Connections** shows up in that dropdown, so Ollama and
LM Studio endpoints can be switched between freely at runtime.

This is only safe because the published port is bound to `127.0.0.1`. The two together
restore MLflow's intended "same host only" guarantee rather than bypassing it. **If you
need to reach this server from another machine, drop the relay and bind `--host
0.0.0.0`** — otherwise anyone who can route to the port gets arbitrary code execution in
the container.

The relay lives in the mlflow container rather than in a sidecar precisely so that
`docker compose restart mlflow` is safe: a sidecar sharing the container's network
namespace is stranded by a restart, leaving MLflow reporting healthy while the published
port answers nothing.

Endpoints are created with the same script; use `--name` to add several:

```bash
docker compose exec mlflow python /scripts/setup_assistant.py \
  --name ollama-qwen3-14b --base-url http://host.docker.internal:11434/v1 --model qwen3:14b

docker compose exec mlflow python /scripts/setup_assistant.py \
  --name lmstudio-gpt-oss --base-url http://host.docker.internal:1234/v1 --model openai/gpt-oss-20b

docker compose restart mlflow
```

Pick tool-calling models — the assistant is a tool-calling agent and a chat-only model
will not work.

The light config is wired identically — relay, loopback binding and all. Add
`-f docker-compose-local-light.yml` to each command.

The AI Gateway only needs a database-backed store, and SQLite satisfies that, so no
Postgres is involved. Note that the two stacks keep **separate** gateway stores: an LLM
Connection created against one does not exist in the other.

When creating an LLM Connection through the UI, the base URL must be
`http://host.docker.internal:<port>` — **not** `localhost`, which inside the container
refers to the container itself — and it needs the `/v1` suffix for Ollama's
OpenAI-compatible shim (`http://host.docker.internal:11434/v1`).

Pick a model that supports tool calling — the assistant needs it. The script is
idempotent, so re-run it to switch models or base URLs.

`MLFLOW_CRYPTO_KEK_PASSPHRASE` encrypts gateway secrets at rest; MLflow falls back to a
well-known default passphrase when unset. **Set it before creating any LLM Connection.**
It is left commented out in `.env.example` on purpose: changing it later makes every
existing secret undecryptable (`Failed to decrypt secret...`) and each API key has to be
re-entered — there is no re-encryption path for keys you no longer have. With the
loopback binding above the default passphrase is an acceptable local-dev tradeoff; set a
real one on any server reachable over a network.

### MLflow Version

Set `MLFLOW_VERSION` in `.env` to pin or upgrade MLflow:

```env
# Default — latest 3.x with GenAI extras
MLFLOW_VERSION=mlflow[genai]>=3.10.0

# Pin to an exact version
MLFLOW_VERSION=mlflow[genai]==3.10.0
```

### Port Conflicts

If any default ports clash with other services on your machine, change them in `.env`:

```env
MLFLOW_PORT=5020
RUSTFS_CONSOLE_PORT=9091
```

No changes to `docker-compose.yml` are needed.

## Using MLflow from Your Python Code

Install the MLflow client:
```bash
pip install mlflow boto3
```

Set environment variables (adjust port if you changed `MLFLOW_PORT`):
```bash
export MLFLOW_TRACKING_URI=http://localhost:5010
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
export AWS_ACCESS_KEY_ID=rustfs
export AWS_SECRET_ACCESS_KEY=rustfs123
```

Example Python code:
```python
import mlflow
import os

mlflow.set_tracking_uri("http://localhost:5010")

os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://localhost:9000'
os.environ['AWS_ACCESS_KEY_ID'] = 'rustfs'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'rustfs123'

mlflow.set_experiment("my-experiment")

with mlflow.start_run():
    mlflow.log_param("param1", 5)
    mlflow.log_metric("metric1", 0.85)

    with open("example.txt", "w") as f:
        f.write("Hello MLflow!")
    mlflow.log_artifact("example.txt")
```

## Useful Commands

**Stop all services:**
```bash
docker-compose down
```

**Stop and remove all data:**
```bash
docker-compose down
rm -rf ~/volumes/postgres ~/volumes/rustfs
```

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f mlflow
docker-compose logs -f postgres
docker-compose logs -f rustfs
```

**Restart a specific service:**
```bash
docker-compose restart mlflow
```

**Update MLflow to a new version:**

Edit `MLFLOW_VERSION` in `.env`, then force-recreate only the MLflow container (postgres and rustfs are left untouched):
```bash
docker-compose up -d --force-recreate mlflow
```
This triggers a fresh `pip install` on startup with the new version.

**Run a schema migration (before upgrading MLflow):**

The `mlflow-migrate` service is opt-in and will:
1. Create a timestamped pg_dump backup in `~/volumes/postgres-backups/`
2. Run `mlflow db upgrade` to apply any pending schema changes

```bash
docker-compose --profile migrate up mlflow-migrate
```

This service exits automatically when done. Check the output for the backup file path. The stack (postgres, rustfs, mlflow) does not need to be stopped beforehand.

**Check service status:**
```bash
docker-compose ps
```

## Data Persistence

All data is stored in the `~/volumes` directory on your Mac:
- `~/volumes/postgres`: PostgreSQL database files
- `~/volumes/rustfs`: RustFS object storage files
- `~/volumes/postgres-backups`: Pre-migration pg_dump backups (created by `mlflow-migrate`)

This data persists even when containers are stopped. To completely remove data:
```bash
docker-compose down
rm -rf ~/volumes/postgres ~/volumes/rustfs
mkdir -p ~/volumes/postgres ~/volumes/rustfs
```

## Accessing RustFS Console

1. Open http://localhost:9001 (or your `RUSTFS_CONSOLE_PORT`)
2. Login with your `RUSTFS_ROOT_USER` / `RUSTFS_ROOT_PASSWORD` from `.env`
3. Navigate to "Buckets" to see the `mlflow` bucket and stored artifacts

## Health Checks

All services include health checks:
```bash
docker-compose ps
```
All services should show "healthy" status after startup.

## Troubleshooting

**MLflow can't connect to PostgreSQL:**
- Wait a few seconds after starting services
- Check logs: `docker-compose logs postgres`
- Verify PostgreSQL is healthy: `docker-compose ps`

**Artifacts not uploading:**
- Verify RustFS is running: `docker-compose ps rustfs`
- Check RustFS console at http://localhost:9001
- Ensure bucket exists (created automatically by `rustfs-setup`)

## Backup and Restore

**Backup:**
```bash
docker-compose down
tar czf mlflow-backup-$(date +%Y%m%d).tar.gz -C ~ volumes/
docker-compose up -d
```

**Restore:**
```bash
docker-compose down
rm -rf ~/volumes/postgres ~/volumes/rustfs
tar xzf mlflow-backup-YYYYMMDD.tar.gz -C ~
docker-compose up -d
```

## Resource Requirements

Typical resource usage:
- CPU: 0.5-1 cores
- RAM: 1-2 GB
- Disk: Depends on your artifacts and experiments
