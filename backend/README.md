# Coinfrs Backend

## Overview

This directory contains the backend for the Coinfrs platform, a B2B SaaS for digital asset accounting.

## Current Status

The project is in active development. We've implemented:
- ✅ Core data models (staging and canonical layers)
- ✅ Data-source-first service architecture
- ✅ Binance API client
- ✅ Daily reconciliation service for completeness checks
- ✅ Position snapshot models for audit trail
- ✅ ETL service structure for data transformation
- ✅ Encryption service for API credentials

## Project Structure

```
app/
├── api/               # API endpoints
├── core/              # Core utilities
│   ├── celery_app.py  # Celery configuration
│   └── security.py    # Encryption utilities
├── models/            # Database models
│   ├── canonical.py   # Canonical layer models
│   ├── onboarding.py  # User and DataSource models
│   └── staging.py     # Staging layer models with position snapshots
├── services/          # Business logic (data-source-first organization)
│   ├── common/        # Base classes for all exchanges
│   ├── binance/       # All Binance-specific code
│   └── fireblocks/    # All Fireblocks-specific code
└── main.py            # FastAPI application

## Next Steps

### 1. Complete Binance Integration

- **Database Integration:** Add database session management to save raw payloads
- **API Validation:** Implement read-only permission checks
- **Sub-accounts:** Add support for fetching sub-account data

### 2. Implement Fireblocks Integration

- **API Client:** Create Fireblocks client with JWT authentication
- **Ingestion Service:** Implement data fetching from Fireblocks API
- **Reconciliation:** Add Fireblocks-specific reconciliation logic

### 3. Set Up Database and Infrastructure

- **PostgreSQL:** Configure database with proper JSONB indexes
- **Alembic:** Set up database migrations
- **Redis:** Configure for Celery task queue
- **Environment:** Create .env.example with all required variables

### 4. Build API Endpoints

- **Authentication:** User registration, login, Google OAuth
- **Data Sources:** Endpoint to add and manage data sources
- **Reconciliation:** API to trigger and view reconciliation results

## Running the Application

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Edit with your values

# Start Redis (for Celery)
redis-server

# Start PostgreSQL
# (Platform-specific commands)
```

### Running Services
```bash
# Start FastAPI server
uvicorn app.main:app --reload

# Start Celery worker (in another terminal)
celery -A app.core.celery_app worker --loglevel=info

# Start Celery beat for scheduled tasks (in another terminal)
celery -A app.core.celery_app beat --loglevel=info
```

## Adding a New Exchange

To add support for a new exchange:

1. Create a new directory under `app/services/` (e.g., `app/services/coinbase/`)
2. Implement the required files:
   - `client.py` - API client inheriting from `BaseAPIClient`
   - `ingestion.py` - Data fetching inheriting from `BaseIngestionService`
   - `reconciliation.py` - Completeness checks inheriting from `BaseReconciliationService`
   - `etl.py` - Data transformation inheriting from `BaseETLService`
3. Add new staging models to `app/models/staging.py`
4. Update the `DataSourceType` enum in `app/models/onboarding.py`
