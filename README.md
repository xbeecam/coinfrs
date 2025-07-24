# Coinfrs - Digital Asset Accounting Platform

## Overview

Coinfrs is a B2B SaaS platform that provides automated accounting and reporting for digital assets. It aggregates transaction data from multiple cryptocurrency exchanges and wallet providers, normalizes the data, applies accounting logic, and generates audit-ready reports and ERP-compatible files.

### Key Features
- **Multi-Exchange Support**: Integrate with Binance, Fireblocks, and more
- **Two-Layer Architecture**: Immutable raw data storage with processed canonical layer
- **Daily Reconciliation**: Automated completeness checks ensure data integrity
- **Flexible Accounting**: Support for FIFO, LIFO, and Average Cost methods
- **Enterprise Ready**: Audit trails, encryption, and role-based access control

## Project Status

🚧 **Current Phase**: Building Backend Foundation for Phase 1 MVP

### Completed ✅
- Core data models (staging and canonical layers)
- Data-source-first service architecture
- Binance API client and constants
- Daily reconciliation framework
- Encryption service for API credentials
- Database configuration
- Project restructuring

### In Progress 🔄
- Authentication API endpoints
- Core API framework
- Portfolio and entity management
- Database migrations setup

### Blocked 🔴
- Binance implementation (awaiting review)
- Fireblocks implementation (awaiting guidelines)

## Architecture Overview

```
┌─────────────────────┐     ┌─────────────────────┐
│   External APIs     │     │    Frontend (TBD)   │
│ (Binance/Fireblocks)│     │   React/Vue/Next    │
└──────────┬──────────┘     └──────────┬──────────┘
           │                           │
           ▼                           ▼
┌─────────────────────────────────────────────────┐
│              FastAPI Application                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   Auth API  │  │Portfolio API│  │Data API │ │
│  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────┬───────────────────────┘
                          │
           ┌──────────────┴──────────────┐
           ▼                             ▼
┌─────────────────────┐       ┌─────────────────────┐
│   Service Layer     │       │    Celery Workers   │
│  ┌──────────────┐   │       │  ┌───────────────┐  │
│  │   Binance    │   │       │  │  Ingestion    │  │
│  │   Services   │   │       │  │     Tasks     │  │
│  └──────────────┘   │       │  └───────────────┘  │
│  ┌──────────────┐   │       │  ┌───────────────┐  │
│  │  Fireblocks  │   │       │  │      ETL      │  │
│  │   Services   │   │       │  │     Tasks     │  │
│  └──────────────┘   │       │  └───────────────┘  │
└─────────────────────┘       └─────────────────────┘
           │                             │
           ▼                             ▼
┌─────────────────────────────────────────────────┐
│              PostgreSQL Database                 │
│  ┌─────────────┐           ┌─────────────────┐  │
│  │   Staging   │           │    Canonical    │  │
│  │    Layer    │ ──ETL──>  │     Layer       │  │
│  │  (Raw Data) │           │ (Processed Data)│  │
│  └─────────────┘           └─────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Docker (optional, for containerized development)

### Setup
```bash
# Clone the repository
git clone https://github.com/your-org/coinfrs.git
cd coinfrs

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -m alembic upgrade head

# Run the application
uvicorn app.main:app --reload
```

For detailed setup instructions, see [Development Setup Guide](docs/development_setup.md).

## Documentation

### Core Documentation
- 📋 [Product Requirements Document](docs/prd.md) - Business requirements and user stories
- 🏗️ [Technical Specification](docs/tech_spec.md) - Architecture and technical details
- 📝 [Development Rules](rules.md) - Coding standards and workflow
- ✅ [Current Tasks](todo.md) - Sprint planning and progress tracking

### Developer Guides
- 🚀 [Development Setup](docs/development_setup.md) - Environment setup guide
- 🏛️ [Architecture Decisions](docs/architecture/decisions.md) - Key design choices
- 🔌 [API Development](docs/api_development.md) - API guidelines and examples
- 🧪 [Testing Strategy](docs/testing_strategy.md) - Testing approach and tools

### Exchange Documentation
- 📊 [Binance Integration](docs/data_sources/binance.md) - Binance API implementation
- 🔥 [Fireblocks Integration](docs/data_sources/fireblocks.md) - Fireblocks API (planned)

## Project Structure

```
coinfrs/
├── backend/              # Backend application
│   ├── app/             # Application code
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core utilities
│   │   ├── db/          # Database configuration
│   │   ├── models/      # Data models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── tests/           # Test suite
│   └── requirements.txt # Python dependencies
├── docs/                # Documentation
├── frontend/            # Frontend application (TBD)
└── reference/           # Reference materials
```

## Development Workflow

1. **Check Current Tasks**: Review [todo.md](todo.md) for current sprint
2. **Pick a Task**: Choose an unassigned task marked as `pending`
3. **Update Status**: Mark task as `in_progress` in todo.md
4. **Implement**: Follow guidelines in [rules.md](rules.md)
5. **Test**: Write tests for your code
6. **Update Docs**: Update relevant documentation
7. **Mark Complete**: Update task status to `completed`

## Contributing

Please read [rules.md](rules.md) for our development guidelines and workflow.

### Key Principles
- 🎯 Simplicity over complexity
- 🔒 Security-first approach
- 📊 Data integrity is paramount
- 🧪 Test-driven development
- 📝 Document as you code

## Support

- **Issues**: GitHub Issues (when repository is set up)
- **Documentation**: See `/docs` directory
- **Contact**: [Contact information to be added]

## License

[License information to be added]

---

**Note**: This project is in active development. Some features and documentation are still being implemented.