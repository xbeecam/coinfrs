# Development Setup Guide

This guide will help you set up your development environment for the Coinfrs project.

## Prerequisites

### Required Software
- **Python 3.11+**: [Download Python](https://www.python.org/downloads/)
- **PostgreSQL 14+**: [Download PostgreSQL](https://www.postgresql.org/download/)
- **Redis 6+**: [Download Redis](https://redis.io/download/)
- **Git**: [Download Git](https://git-scm.com/downloads/)

### Optional Software
- **Docker Desktop**: [Download Docker](https://www.docker.com/products/docker-desktop/) (for containerized development)
- **VS Code**: [Download VS Code](https://code.visualstudio.com/) (recommended IDE)
- **Postman**: [Download Postman](https://www.postman.com/downloads/) (for API testing)

## Step-by-Step Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/coinfrs_v2.git
cd coinfrs_v2
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database

#### Option A: Local PostgreSQL
```bash
# Create database and user
psql -U postgres

CREATE DATABASE coinfrs;
CREATE USER coinfrs WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE coinfrs TO coinfrs;
\q
```

#### Option B: Docker PostgreSQL
```bash
docker run --name coinfrs-postgres \
  -e POSTGRES_DB=coinfrs \
  -e POSTGRES_USER=coinfrs \
  -e POSTGRES_PASSWORD=your-secure-password \
  -p 5432:5432 \
  -d postgres:14
```

### 5. Set Up Redis

#### Option A: Local Redis
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
```

#### Option B: Docker Redis
```bash
docker run --name coinfrs-redis \
  -p 6379:6379 \
  -d redis:6-alpine
```

### 6. Configure Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
# Use your favorite editor (vim, nano, code, etc.)
code .env
```

**Key variables to configure:**
```env
# Generate SECRET_KEY
# Run: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-generated-secret-key

# Generate ENCRYPTION_KEY
# Run: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=your-generated-encryption-key

# Update database connection
DATABASE_URL=postgresql://coinfrs:your-secure-password@localhost:5432/coinfrs

# Redis connection (usually default is fine)
REDIS_URL=redis://localhost:6379/0
```

### 7. Initialize Database
```bash
# Run database migrations
alembic upgrade head

# Verify database setup
python -c "from app.db.session import init_db; init_db(); print('Database initialized!')"
```

### 8. Run the Application

#### Terminal 1: FastAPI Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2: Celery Worker
```bash
celery -A app.core.celery_app worker --loglevel=info
```

#### Terminal 3: Celery Beat (Scheduler)
```bash
celery -A app.core.celery_app beat --loglevel=info
```

### 9. Verify Installation
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Database Check**: http://localhost:8000/health/db
- **Redis Check**: http://localhost:8000/health/redis

## Docker Development (Alternative)

If you prefer containerized development:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Common Issues & Solutions

### Issue: Database Connection Error
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution**: 
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify username/password

### Issue: Redis Connection Error
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```
**Solution**:
- Ensure Redis is running
- Check REDIS_URL in .env
- Try `redis-cli ping` to test connection

### Issue: Module Import Errors
```
ModuleNotFoundError: No module named 'app'
```
**Solution**:
- Ensure you're in the `backend` directory
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

### Issue: Alembic Migration Error
```
alembic.util.exc.CommandError: Can't locate revision identified by 'head'
```
**Solution**:
- Initialize Alembic: `alembic init alembic`
- Create initial migration: `alembic revision --autogenerate -m "Initial migration"`

## IDE Setup

### VS Code Extensions
Recommended extensions for VS Code:
- Python
- Pylance
- Black Formatter
- SQLTools
- Thunder Client (API testing)
- GitLens

### VS Code Settings
Create `.vscode/settings.json`:
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "88"],
  "editor.formatOnSave": true,
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

## Next Steps

1. **Run Tests**: `pytest` to ensure everything is working
2. **Review Documentation**: Read through `/docs` directory
3. **Check Tasks**: Review `todo.md` for current tasks
4. **Start Developing**: Pick a task and start coding!

## Getting Help

- Check existing documentation in `/docs`
- Review code examples in the codebase
- Look for similar patterns in existing code
- Ask questions (when communication channels are set up)

---

**Note**: This guide assumes a Unix-like environment (macOS/Linux). Windows users may need to adjust some commands.