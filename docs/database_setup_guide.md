# Database Setup Guide for Binance Reconciliation

This guide will help you set up PostgreSQL and run the Binance reconciliation database migrations.

## Prerequisites
- Docker Desktop installed (for Option 1)
- PostgreSQL installed (for Option 2)
- Python environment activated

## Option 1: Using Docker (Recommended)

### Step 1: Start PostgreSQL with Docker

```bash
# Run PostgreSQL in a Docker container
docker run --name coinfrs-postgres \
  -e POSTGRES_DB=coinfrs \
  -e POSTGRES_USER=coinfrs \
  -e POSTGRES_PASSWORD=coinfrs123 \
  -p 5432:5432 \
  -d postgres:14-alpine
```

### Step 2: Verify PostgreSQL is Running

```bash
# Check if container is running
docker ps

# Test connection (optional)
docker exec -it coinfrs-postgres psql -U coinfrs -d coinfrs
```

### Step 3: Configure Environment Variables

```bash
cd backend

# Copy the example environment file
cp .env.example .env

# Edit .env file and update DATABASE_URL
# Change this line:
DATABASE_URL=postgresql://coinfrs:coinfrs123@localhost:5432/coinfrs
```

### Step 4: Run Migrations

```bash
# Make sure you're in the backend directory
cd backend

# Run the migrations
alembic upgrade head
```

### Step 5: Verify Tables Were Created

```bash
# Connect to PostgreSQL
docker exec -it coinfrs-postgres psql -U coinfrs -d coinfrs

# In PostgreSQL prompt, list tables
\dt

# Check Binance tables specifically
\dt binance*

# Check the view
\dv v_binance_user_assets

# Exit PostgreSQL
\q
```

## Option 2: Using Local PostgreSQL

### Step 1: Create Database and User

```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql

# Create database and user
CREATE DATABASE coinfrs;
CREATE USER coinfrs WITH PASSWORD 'coinfrs123';
GRANT ALL PRIVILEGES ON DATABASE coinfrs TO coinfrs;
\q
```

### Step 2: Update .env File

Same as Option 1, Step 3.

### Step 3: Run Migrations

Same as Option 1, Step 4.

## Common Commands

### Managing Docker PostgreSQL

```bash
# Stop the database
docker stop coinfrs-postgres

# Start the database
docker start coinfrs-postgres

# Remove the database (WARNING: This deletes all data!)
docker rm -f coinfrs-postgres

# View logs
docker logs coinfrs-postgres
```

### Alembic Migration Commands

```bash
# Check current migration status
alembic current

# See migration history
alembic history

# Upgrade to latest migration
alembic upgrade head

# Downgrade one migration
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade 745089f4539e
```

## Troubleshooting

### Issue: Connection Refused

```
sqlalchemy.exc.OperationalError: connection to server at "localhost"
```

**Solution**: 
- Make sure PostgreSQL is running
- Check if port 5432 is available: `lsof -i :5432`
- Verify DATABASE_URL in .env file

### Issue: Role Does Not Exist

```
FATAL: role "coinfrs" does not exist
```

**Solution**:
- Create the user as shown in Option 2, Step 1
- Or use Docker option which creates user automatically

### Issue: Database Does Not Exist

```
FATAL: database "coinfrs" does not exist
```

**Solution**:
- Create the database as shown in setup steps
- Make sure you're connecting to the right database

### Issue: Permission Denied

```
permission denied for schema public
```

**Solution**:
```sql
-- Grant permissions (run as superuser)
GRANT ALL ON DATABASE coinfrs TO coinfrs;
GRANT ALL ON SCHEMA public TO coinfrs;
```

## Verifying Your Setup

After successful migration, you should see these tables:

```
- binancereconciliationtransfer
- binancereconciliationtrade
- binancereconciliationbalance
- binanceexchangeinfo
- binancetradedsymbols
- binancereconciliationerror
- binancerawdailysnapshot
- binancerawdeposithistory
- binancerawwithdrawhistory
- binancerawtransferbetweenaccountmainspot
- binancerawtransferbetweenaccountsub
- binancerawtransferbetweenwallets
- binancerawtrades
- binancerawconverthistory
```

And one view:
- v_binance_user_assets

## Next Steps

Once your database is set up:
1. The tables are ready to store reconciliation data
2. You can proceed with implementing the API client enhancements
3. Start collecting data from Binance API

## Quick Test Query

To test if everything is working, run this query:

```sql
-- Connect to database
docker exec -it coinfrs-postgres psql -U coinfrs -d coinfrs

-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'binance%'
ORDER BY table_name;

-- Check the view
SELECT * FROM v_binance_user_assets LIMIT 1;
```

## Security Notes

1. **Never commit .env files** - They contain sensitive database credentials
2. **Use strong passwords** in production
3. **Restrict database access** - Only allow connections from your application
4. **Regular backups** - Set up automated backups for production data

## Docker Compose Alternative

For a more permanent setup, create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    container_name: coinfrs-postgres
    environment:
      POSTGRES_DB: coinfrs
      POSTGRES_USER: coinfrs
      POSTGRES_PASSWORD: coinfrs123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Then run:
```bash
docker-compose up -d
```

This preserves your data even if the container is removed.