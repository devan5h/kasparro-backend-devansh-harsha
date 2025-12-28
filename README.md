# Kasparoo Backend + ETL System

A production-grade backend and ETL system for ingesting, normalizing, and serving cryptocurrency market data from multiple sources.

## 🏗️ Architecture

The project follows a clean architecture pattern with clear separation of concerns:

```
├── api/              # FastAPI application and routes
├── core/             # Core configuration, database, logging
├── ingestion/        # ETL pipeline ingesters
├── services/         # Business logic (normalization, checkpoints, etc.)
├── schemas/          # Pydantic models for validation
├── tests/            # Pytest test suite
└── alembic/          # Database migrations
```

## 🚀 Features

### ETL Pipeline
- **Multi-source ingestion**: CoinPaprika API, CoinGecko API, and CSV files
- **Incremental ingestion**: Checkpoint system for resumable ETL runs
- **Idempotent writes**: Prevents duplicate data insertion
- **Rate limiting**: Token bucket algorithm for API rate limiting
- **Retry logic**: Exponential backoff for failed API requests
- **Structured logging**: JSON-formatted logs with context

### Backend API
- **GET /api/data**: Paginated market data with filtering
- **GET /api/health**: Health check with DB and ETL status
- **GET /api/stats**: ETL run statistics and summaries
- **Request metadata**: Includes request_id and api_latency_ms

### Data Normalization
- **Unified schema**: All sources normalized into `coins`, `prices`, and `market_data` tables
- **Source tracking**: Maintains data lineage with source attribution
- **Type safety**: Pydantic models for validation

## 🛠️ Tech Stack

- **Python 3.11**
- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migrations
- **PostgreSQL**: Production database
- **Pydantic**: Data validation
- **Pytest**: Testing framework
- **Docker & Docker Compose**: Containerization

## 📋 Prerequisites

- Docker and Docker Compose
- (Optional) Python 3.11+ for local development

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd Kasparoo_Backend_project

# Create .env file (optional, for API keys)
cp .env.example .env
# Edit .env and add your COINPAPRIKA_API_KEY if you have one
```

### 2. Start Services

```bash
# Start all services (API, ETL, Database)
make up

# Or using docker-compose directly
docker-compose up -d
```

### 3. Run Migrations

```bash
# Run database migrations
make migrate
```

### 4. Access Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432 (postgres/postgres)

## 📖 Usage

### API Endpoints

#### GET /api/data
Get paginated market data with filtering options.

```bash
# Basic request
curl http://localhost:8000/api/data

# PowerShell alternative
Invoke-WebRequest -Uri http://localhost:8000/api/data | Select-Object -ExpandProperty Content

# With pagination
curl http://localhost:8000/api/data?page=1&page_size=20

# PowerShell alternative
Invoke-WebRequest -Uri "http://localhost:8000/api/data?page=1&page_size=20" | Select-Object -ExpandProperty Content

# With filters
curl http://localhost:8000/api/data?symbol=BTC&source=coinpaprika

# PowerShell alternative
Invoke-WebRequest -Uri "http://localhost:8000/api/data?symbol=BTC&source=coinpaprika" | Select-Object -ExpandProperty Content
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 100)
- `symbol`: Filter by coin symbol
- `source`: Filter by data source (coinpaprika, coingecko, csv)
- `start_date`: Start date filter (ISO format)
- `end_date`: End date filter (ISO format)

#### GET /api/health
Check system health and ETL status.

```bash
# Linux/Mac
curl http://localhost:8000/api/health

# PowerShell (Windows)
Invoke-WebRequest -Uri http://localhost:8000/api/health | Select-Object -ExpandProperty Content
```

#### GET /api/stats
Get ETL run statistics.

```bash
# All sources
curl http://localhost:8000/api/stats

# PowerShell alternative
Invoke-WebRequest -Uri http://localhost:8000/api/stats | Select-Object -ExpandProperty Content | ConvertFrom-Json

# Filter by source
curl http://localhost:8000/api/stats?source=coinpaprika

# PowerShell alternative
Invoke-WebRequest -Uri "http://localhost:8000/api/stats?source=coinpaprika" | Select-Object -ExpandProperty Content | ConvertFrom-Json
```

### ETL Pipeline

The ETL pipeline runs automatically in the background. It:
1. Ingests data from all configured sources
2. Stores raw data in `raw_*` tables
3. Normalizes data into unified schema
4. Updates checkpoints for incremental ingestion
5. Runs continuously with configurable interval (default: 5 minutes)

**Manual ETL Run:**
```bash
# Run ETL once
make etl-once

# Or using docker-compose
docker-compose exec etl python run_etl.py
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run tests locally (requires local setup)
make test-local

# Or using pytest directly
pytest tests/ -v
```

## 📁 Project Structure

```
Kasparoo_Backend_project/
├── api/
│   ├── main.py              # FastAPI application
│   └── routes/              # API route handlers
│       ├── data.py          # Data endpoint
│       ├── health.py        # Health check endpoint
│       └── stats.py         # Stats endpoint
├── core/
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   └── logging_config.py    # Structured logging setup
├── ingestion/
│   ├── base_ingester.py     # Base ingester class
│   ├── coinpaprika_ingester.py
│   ├── coingecko_ingester.py
│   └── csv_ingester.py
├── services/
│   ├── models.py            # SQLAlchemy models
│   ├── normalizer.py        # Data normalization
│   ├── checkpoint_manager.py
│   ├── etl_runner.py        # ETL orchestration
│   ├── http_client.py       # HTTP client with retry
│   └── rate_limiter.py      # Rate limiting
├── schemas/
│   └── models.py            # Pydantic models
├── tests/                    # Test suite
├── alembic/                  # Database migrations
├── data/                     # CSV data directory
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md
```

## 🔧 Configuration

Configuration is managed through environment variables (see `.env.example`):

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/kasparoo_db

# API Keys
COINPAPRIKA_API_KEY=your_api_key_here

# ETL Settings
ETL_RUN_INTERVAL_SECONDS=300
ETL_BATCH_SIZE=100

# Rate Limiting
COINPAPRIKA_RATE_LIMIT=10
COINGECKO_RATE_LIMIT=10

# Logging
LOG_LEVEL=INFO
```

## 🗄️ Database Schema

### Raw Tables
- `raw_coinpaprika`: Raw data from CoinPaprika API
- `raw_coingecko`: Raw data from CoinGecko API
- `raw_csv`: Raw data from CSV files

### Normalized Tables
- `coins`: Unified coin information
- `prices`: Price data with timestamps
- `market_data`: Market data with additional metrics

### Metadata Tables
- `etl_checkpoints`: Checkpoints for incremental ingestion
- `etl_runs`: ETL execution history

## 🎯 Design Decisions

### 1. Clean Architecture
- **Separation of concerns**: Each layer has a clear responsibility
- **Dependency inversion**: High-level modules don't depend on low-level modules
- **Testability**: Easy to mock and test individual components

### 2. Incremental Ingestion
- **Checkpoint system**: Tracks last processed item per source
- **Resumable**: Can resume from last checkpoint after failure
- **Idempotent**: Same data can be processed multiple times safely

### 3. Rate Limiting & Retry
- **Token bucket algorithm**: Smooth rate limiting without bursts
- **Exponential backoff**: Reduces load on external APIs during failures
- **Configurable**: Rate limits and retry settings via environment variables

### 4. Structured Logging
- **JSON format**: Easy to parse and search in log aggregation systems
- **Contextual**: Includes relevant context (request_id, source, etc.)
- **Levels**: Configurable log levels for different environments

### 5. Data Normalization
- **Unified schema**: All sources map to same tables
- **Source tracking**: Maintains data lineage
- **Type safety**: Pydantic models ensure data integrity

### 6. Error Handling
- **ETL run tracking**: All runs are logged with status and error messages
- **Graceful degradation**: System continues operating even if one source fails
- **Detailed errors**: Error messages stored for debugging

## 🏭 ETL Architecture & Operations

### ETL Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      ETL Runner (Orchestrator)                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Continuous Loop (every 5min)                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
    ┌─────────────────┐ ┌──────────────┐ ┌──────────┐
    │ CoinPaprika     │ │ CoinGecko    │ │ CSV      │
    │ Ingester        │ │ Ingester     │ │ Ingester │
    └─────────────────┘ └──────────────┘ └──────────┘
            │                 │              │
            │                 │              │
    ┌───────┴────────┐ ┌──────┴──────┐ ┌────┴────┐
    │                │ │             │ │         │
    ▼                ▼ ▼             ▼ ▼         ▼
┌──────────────────────────────────────────────────────┐
│  HTTP Client Layer                                    │
│  ├─ Rate Limiter (Token Bucket)                       │
│  ├─ Retry Logic (429/5xx with exponential backoff)    │
│  └─ get_with_retry() helper                           │
└──────────────────────────────────────────────────────┘
            │                 │              │
            ▼                 ▼              ▼
    ┌──────────────────────────────────────────────┐
    │  Checkpoint Manager                          │
    │  ├─ Read last_successful_timestamp            │
    │  ├─ Filter records > timestamp                │
    │  └─ Update checkpoint on success only         │
    └──────────────────────────────────────────────┘
            │                 │              │
            ▼                 ▼              ▼
    ┌──────────────────────────────────────────────┐
    │  Raw Data Storage (raw_* tables)              │
    │  ├─ raw_coinpaprika                          │
    │  ├─ raw_coingecko                            │
    │  └─ raw_csv                                  │
    └──────────────────────────────────────────────┘
            │                 │              │
            ▼                 ▼              ▼
    ┌──────────────────────────────────────────────┐
    │  Normalizer (UPSERT with ON CONFLICT)        │
    │  ├─ Normalize to unified schema              │
    │  ├─ Idempotent writes (UNIQUE constraints)   │
    │  └─ coins, prices, market_data tables        │
    └──────────────────────────────────────────────┘
            │                 │              │
            ▼                 ▼              ▼
    ┌──────────────────────────────────────────────┐
    │  ETL Run Tracking                             │
    │  ├─ etl_runs table (status, timestamps)       │
    │  ├─ etl_checkpoints (last_successful_*)      │
    │  └─ Automatic cleanup on startup             │
    └──────────────────────────────────────────────┘
```

### Incremental Ingestion Strategy

The system implements **timestamp-based incremental ingestion** to minimize redundant API calls and ensure data consistency.

**Core Principle:**
- Each source maintains a `last_successful_timestamp` checkpoint
- Only records with `timestamp > last_successful_timestamp` are processed
- Checkpoint is updated **only** after successful ETL completion

**Implementation Flow:**

1. **Checkpoint Read (Start of ETL Run)**
   ```python
   checkpoint = checkpoint_manager.get_checkpoint(source_name)
   last_successful_timestamp = checkpoint.last_successful_timestamp
   ```

2. **Record Filtering**
   ```python
   # CoinPaprika/CoinGecko: Filter by API response timestamp
   if record_timestamp <= last_successful_timestamp:
       continue  # Skip already processed records
   
   # CSV: Filter by file modification time
   if file_mtime <= last_successful_timestamp:
       skip_processing()
   ```

3. **Checkpoint Update (End of Successful Run)**
   ```python
   # Only called on successful completion
   checkpoint_manager.update_checkpoint_on_success(
       source_name=source_name,
       last_successful_timestamp=latest_timestamp,
       last_run_id=current_run.id
   )
   ```

**Benefits:**
- **Efficiency**: Processes only new/updated records
- **Resilience**: Failed runs don't advance checkpoint
- **Idempotency**: Re-running same data is safe (UPSERT handles duplicates)

### Checkpoint Logic

The checkpoint system provides **authoritative state** for incremental ingestion.

**Schema:**
```sql
etl_checkpoints (
    source_name VARCHAR(50) UNIQUE,
    last_successful_timestamp TIMESTAMP,  -- Only updated on success
    last_run_id INTEGER REFERENCES etl_runs(id),
    last_ingested_id VARCHAR(200),         -- Optional: source-specific ID
    checkpoint_data TEXT                  -- JSON for additional state
)
```

**Checkpoint Lifecycle:**

1. **First Run (No Checkpoint)**
   - `last_successful_timestamp = NULL`
   - Processes all available records
   - Creates checkpoint with latest timestamp

2. **Subsequent Runs (Checkpoint Exists)**
   - Reads `last_successful_timestamp`
   - Filters records: `WHERE timestamp > last_successful_timestamp`
   - Updates checkpoint only if run succeeds

3. **Failed Run**
   - Checkpoint **NOT** updated
   - `last_successful_timestamp` remains unchanged
   - Next run retries from same point

**Checkpoint Update Rules:**
- ✅ **Update on**: Successful ETL completion (`ETLStatus.SUCCESS`)
- ❌ **No update on**: Failed runs, interrupted runs, partial completions
- 🔒 **Atomic**: Checkpoint update happens in same transaction as data commit

### Resume-on-Failure Behavior

The system implements **automatic recovery** from failures without data loss or duplication.

**Failure Scenarios & Recovery:**

1. **API Failure (429, 5xx)**
   ```
   Attempt 1: HTTP 429 → Wait 1s → Retry
   Attempt 2: HTTP 429 → Wait 2s → Retry
   Attempt 3: HTTP 429 → Wait 4s → Retry
   Attempt 4: Still failing → Mark ETL run as FAILED
   ```
   - Checkpoint **not updated** → Next run retries from same point
   - Partial data (if any) preserved in raw tables
   - Normalized data uses UPSERT (idempotent)

2. **Process Crash/Interruption**
   - ETL run remains in `RUNNING` state
   - `completed_at = NULL`
   - **On startup**: Automatic cleanup marks as `FAILED` with error "Interrupted due to restart"
   - Checkpoint unchanged → Next run resumes from last successful point

3. **Database Connection Loss**
   - Transaction rollback prevents partial writes
   - Checkpoint not updated
   - ETL run marked as `FAILED`
   - Next run retries from checkpoint

4. **Partial Ingestion**
   - If 50/100 records processed before failure:
     - Raw data: May have partial records (acceptable)
     - Normalized data: UPSERT ensures no duplicates
     - Checkpoint: **Not updated** (no successful completion)
     - Next run: Processes all records > `last_successful_timestamp` (including the 50)

**Recovery Guarantees:**
- ✅ **No data loss**: Raw data preserved even on failure
- ✅ **No duplicates**: UPSERT + UNIQUE constraints prevent duplicates
- ✅ **Consistent state**: Checkpoint only advances on success
- ✅ **Automatic cleanup**: Stale `RUNNING` runs cleaned on startup

### Rate Limiting & Backoff

The system implements **multi-layer rate control** to respect API limits and handle transient failures.

**Layer 1: Token Bucket Rate Limiting**

Prevents exceeding API rate limits:
```python
RateLimiter(rate=10, per=1.0)  # 10 requests/second
```

- **Algorithm**: Token bucket with refill
- **Behavior**: Smooth rate limiting (no bursts)
- **Scope**: Applied before each HTTP request

**Layer 2: Retry with Exponential Backoff**

Handles transient failures (429, 5xx):
```python
get_with_retry(
    http_client=http_client,
    url=url,
    source="coingecko",
    max_retries=3
)
```

**Retry Strategy:**
- **Max retries**: 3 (4 total attempts: 1 initial + 3 retries)
- **Backoff sequence**: 1s → 2s → 4s (2^0, 2^1, 2^2)
- **Retry conditions**: HTTP 429 (Too Many Requests), HTTP 5xx (Server Errors)
- **No retry on**: HTTP 4xx (except 429), network timeouts (handled by HTTPClient)

**Retry Flow:**
```
Attempt 1: Request → 429 → Log retry → Wait 1s
Attempt 2: Request → 429 → Log retry → Wait 2s
Attempt 3: Request → 429 → Log retry → Wait 4s
Attempt 4: Request → 429 → Raise exception → ETL run marked FAILED
```

**Logging:**
Each retry attempt logs:
```json
{
  "event": "Retrying API request",
  "source": "coingecko",
  "attempt_number": 1,
  "wait_time": 1,
  "status_code": 429,
  "url": "https://api.coingecko.com/..."
}
```

**Combined Behavior:**
1. Rate limiter ensures requests don't exceed limit
2. If 429/5xx occurs, retry with exponential backoff
3. After max retries, ETL run fails (checkpoint not updated)
4. Next ETL cycle retries from checkpoint

## 🧪 Demo: Failure, Restart & Recovery

### Demo 1: Simulate API Failure (429 Rate Limit)

**Objective**: Demonstrate retry logic and checkpoint preservation on API failures.

**Steps:**

1. **Trigger rate limiting** (if CoinGecko API is available):
   ```bash
   # Monitor ETL logs
   docker compose logs -f etl
   
   # Wait for ETL run - if 429 occurs, you'll see:
   # "Retrying API request" with attempt_number, wait_time, status_code
   ```

2. **Verify retry behavior**:
   ```bash
   # Check logs for retry attempts
   docker compose logs etl | grep "Retrying API request"
   
   # Expected output:
   # {"event": "Retrying API request", "source": "coingecko", 
   #  "attempt_number": 1, "wait_time": 1, "status_code": 429}
   ```

3. **Verify checkpoint preserved**:
   ```bash
   docker compose exec db psql -U postgres -d kasparoo_db -c \
     "SELECT source_name, last_successful_timestamp, last_run_id \
      FROM etl_checkpoints WHERE source_name = 'coingecko';"
   
   # Checkpoint should remain unchanged (not updated on failure)
   ```

4. **Verify ETL run marked as failed**:
   ```bash
   docker compose exec db psql -U postgres -d kasparoo_db -c \
     "SELECT id, source_name, status, error_message \
      FROM etl_runs WHERE status = 'FAILED' \
      ORDER BY started_at DESC LIMIT 1;"
   ```

### Demo 2: Simulate Process Interruption

**Objective**: Demonstrate automatic cleanup of interrupted runs on restart.

**Steps:**

1. **Start ETL and let it run**:
   ```bash
   docker compose up -d etl
   docker compose logs -f etl
   ```

2. **Interrupt ETL mid-run** (simulate crash):
   ```bash
   # Kill ETL container while it's running
   docker compose kill etl
   
   # Verify run is stuck in RUNNING state
   docker compose exec db psql -U postgres -d kasparoo_db -c \
     "SELECT id, source_name, status, completed_at \
      FROM etl_runs WHERE status = 'RUNNING' AND completed_at IS NULL;"
   ```

3. **Restart API container** (triggers cleanup):
   ```bash
   docker compose restart api
   
   # Check API logs for cleanup message
   docker compose logs api | grep "Cleaned up interrupted"
   
   # Expected output:
   # {"event": "Cleaned up interrupted ETL runs", 
   #  "count": 1, "run_ids": [X]}
   ```

4. **Verify interrupted run marked as failed**:
   ```bash
   docker compose exec db psql -U postgres -d kasparoo_db -c \
     "SELECT id, source_name, status, error_message \
      FROM etl_runs WHERE error_message = 'Interrupted due to restart';"
   ```

5. **Verify /api/stats shows no stale running runs**:
   ```bash
   # PowerShell
   (Invoke-WebRequest -Uri http://localhost:8000/api/stats).Content | ConvertFrom-Json | Select-Object -ExpandProperty runs | Where-Object {$_.status -eq "running"}
   
   # Linux/Mac (with jq)
   curl http://localhost:8000/api/stats | jq '.runs[] | select(.status == "running")'
   
   # Should return empty (no running runs)
   ```

### Demo 3: Demonstrate Incremental Ingestion Recovery

**Objective**: Show that failed runs don't advance checkpoint, and next run resumes correctly.

**Steps:**

1. **Check current checkpoint state**:
   ```bash
   docker compose exec db psql -U postgres -d kasparoo_db -c \
     "SELECT source_name, last_successful_timestamp, last_run_id \
      FROM etl_checkpoints WHERE source_name = 'coingecko';"
   ```

2. **Trigger a failure** (kill ETL during run):
   ```bash
   docker compose kill etl
   ```

3. **Verify checkpoint unchanged**:
   ```bash
   # Checkpoint timestamp should be same as before
   docker compose exec db psql -U postgres -d kasparoo_db -c \
     "SELECT source_name, last_successful_timestamp \
      FROM etl_checkpoints WHERE source_name = 'coingecko';"
   ```

4. **Restart ETL** (resume from checkpoint):
   ```bash
   docker compose up -d etl
   docker compose logs -f etl
   
   # Look for: "Starting incremental ingestion" with last_timestamp
   # Expected log:
   # {"event": "Starting incremental ingestion", 
   #  "source": "coingecko", 
   #  "last_timestamp": "2025-12-28T..."}
   ```

5. **Verify only new records processed**:
   ```bash
   # Check ETL logs for records processed
   docker compose logs etl | grep "ingested\|normalized"
   
   # Should only process records newer than last_successful_timestamp
   ```

6. **Verify checkpoint updated after success**:
   ```bash
   # After successful run, checkpoint should advance
   docker compose exec db psql -U postgres -d kasparoo_db -c \
     "SELECT source_name, last_successful_timestamp, last_run_id \
      FROM etl_checkpoints WHERE source_name = 'coingecko';"
   ```

### Demo 4: Verify Idempotency

**Objective**: Demonstrate that re-processing same data doesn't create duplicates.

**Steps:**

1. **Note current record count**:
   ```bash
   docker compose exec db psql -U postgres -d kasparoo_db -c \
     "SELECT COUNT(*) FROM market_data WHERE source = 'coingecko';"
   ```

2. **Manually reset checkpoint to earlier timestamp** (simulate re-processing):
   ```bash
   docker compose exec db psql -U postgres -d kasparoo_db -c \
     "UPDATE etl_checkpoints \
      SET last_successful_timestamp = '2025-12-28 00:00:00' \
      WHERE source_name = 'coingecko';"
   ```

3. **Trigger ETL run**:
   ```bash
   docker compose exec etl python run_etl.py
   ```

4. **Verify no duplicates created**:
   ```bash
   # Count should be same (UPSERT prevents duplicates)
   docker compose exec db psql -U postgres -d kasparoo_db -c \
     "SELECT COUNT(*) FROM market_data WHERE source = 'coingecko';"
   
   # Verify UNIQUE constraint working
   docker compose exec db psql -U postgres -d kasparoo_db -c \
     "SELECT coin_id, timestamp, source, COUNT(*) \
      FROM market_data \
      GROUP BY coin_id, timestamp, source \
      HAVING COUNT(*) > 1;"
   # Should return 0 rows (no duplicates)
   ```

### Quick Verification Commands

```bash
# Check all checkpoints
docker compose exec db psql -U postgres -d kasparoo_db -c \
  "SELECT source_name, last_successful_timestamp, last_run_id \
   FROM etl_checkpoints ORDER BY source_name;"

# Check recent ETL runs
docker compose exec db psql -U postgres -d kasparoo_db -c \
  "SELECT id, source_name, status, records_ingested, \
   records_normalized, started_at, completed_at \
   FROM etl_runs ORDER BY started_at DESC LIMIT 10;"

# Check for any running runs (should be 0 after cleanup)
docker compose exec db psql -U postgres -d kasparoo_db -c \
  "SELECT COUNT(*) FROM etl_runs \
   WHERE status = 'RUNNING' AND completed_at IS NULL;"

# View retry logs (Linux/Mac)
docker compose logs etl | grep "Retrying API request"

# PowerShell alternative
docker compose logs etl | Select-String -Pattern "Retrying API request"
```

## 🔒 Security

- **No hardcoded secrets**: All API keys via environment variables
- **SQL injection protection**: SQLAlchemy ORM prevents SQL injection
- **Input validation**: Pydantic models validate all inputs

## 📊 Monitoring

- **Health endpoint**: Monitor system health
- **Stats endpoint**: Track ETL performance
- **Structured logs**: Easy integration with log aggregation tools

## 🛠️ Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database (requires local PostgreSQL)
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/kasparoo_db

# Run migrations
alembic upgrade head

# Run API
uvicorn api.main:app --reload

# Run ETL
python run_etl.py
```

### Makefile Commands

```bash
make up              # Start all services
make down            # Stop all services
make test            # Run tests
make migrate         # Run database migrations
make logs            # View all logs
make logs-api        # View API logs
make logs-etl        # View ETL logs
make db-shell        # Access database shell
```

## 🐛 Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running: `docker-compose ps`
- Check DATABASE_URL in environment variables
- Verify database credentials

### ETL Not Running
- Check ETL container logs: `make logs-etl`
- Verify API keys are set (if required)
- Check checkpoint table for last processed items

### API Not Responding
- Check API container logs: `make logs-api`
- Verify database connectivity: `curl http://localhost:8000/api/health`
- Check if migrations have run: `make migrate`

## 📝 License

[Your License Here]

## 👥 Contributors

[Your Name/Team]

---

**Note**: This is a production-grade system designed for scalability and reliability. For production deployments, consider:
- Setting up proper secrets management
- Configuring log aggregation (ELK, Datadog, etc.)
- Setting up monitoring and alerting
- Implementing API authentication/authorization
- Configuring backup strategies for the database

