# Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Start the System

```bash
# Start all services (database, API, ETL)
make up
```

This will:
- Start PostgreSQL database
- Start FastAPI server on port 8000
- Start ETL pipeline (runs continuously)
- Automatically run database migrations

### 2. Verify It's Working

```bash
# Check health
curl http://localhost:8000/api/health

# View API documentation
open http://localhost:8000/docs
```

### 3. Test the API

```bash
# Get market data
curl http://localhost:8000/api/data

# Get stats
curl http://localhost:8000/api/stats
```

## 📝 Optional: Configure API Key

If you have a CoinPaprika API key:

1. Create `.env` file:
```bash
COINPAPRIKA_API_KEY=your_key_here
```

2. Restart services:
```bash
make down
make up
```

## 🧪 Run Tests

```bash
# Run all tests
make test
```

## 📊 View Logs

```bash
# All logs
make logs

# API logs only
make logs-api

# ETL logs only
make logs-etl
```

## 🛑 Stop Services

```bash
make down
```

## 🔧 Common Commands

```bash
make up              # Start services
make down            # Stop services
make test            # Run tests
make migrate         # Run migrations
make db-shell        # Access database
make logs            # View logs
```

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API at http://localhost:8000/docs
- Check ETL status at http://localhost:8000/api/stats

