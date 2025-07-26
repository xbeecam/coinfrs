#!/bin/bash

# Database Setup Script for Coinfrs
# This script sets up PostgreSQL using Docker and runs migrations

set -e  # Exit on error

echo "🚀 Setting up Coinfrs Database..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "Visit: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check if container already exists
if [ "$(docker ps -aq -f name=coinfrs-postgres)" ]; then
    echo "⚠️  Container 'coinfrs-postgres' already exists."
    read -p "Do you want to remove it and start fresh? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing container..."
        docker rm -f coinfrs-postgres
    else
        echo "Using existing container..."
    fi
fi

# Start PostgreSQL container
echo "🐘 Starting PostgreSQL container..."
docker run --name coinfrs-postgres \
  -e POSTGRES_DB=coinfrs \
  -e POSTGRES_USER=coinfrs \
  -e POSTGRES_PASSWORD=coinfrs123 \
  -p 5432:5432 \
  -d postgres:14-alpine

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Check if PostgreSQL is ready
MAX_ATTEMPTS=30
ATTEMPT=1
while ! docker exec coinfrs-postgres pg_isready -U coinfrs > /dev/null 2>&1; do
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo "❌ PostgreSQL failed to start after $MAX_ATTEMPTS attempts"
        exit 1
    fi
    echo "Waiting for PostgreSQL... (attempt $ATTEMPT/$MAX_ATTEMPTS)"
    sleep 1
    ATTEMPT=$((ATTEMPT + 1))
done

echo "✅ PostgreSQL is ready!"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    
    # Update DATABASE_URL in .env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' 's|DATABASE_URL=.*|DATABASE_URL=postgresql://coinfrs:coinfrs123@localhost:5432/coinfrs|g' .env
    else
        # Linux
        sed -i 's|DATABASE_URL=.*|DATABASE_URL=postgresql://coinfrs:coinfrs123@localhost:5432/coinfrs|g' .env
    fi
else
    echo "ℹ️  .env file already exists, skipping..."
fi

# Run migrations
echo "🔄 Running database migrations..."
if alembic upgrade head; then
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Migration failed. Please check the error messages above."
    exit 1
fi

# Show created tables
echo ""
echo "📊 Verifying tables..."
docker exec coinfrs-postgres psql -U coinfrs -d coinfrs -c "\dt binance*" | head -20

echo ""
echo "🎉 Database setup complete!"
echo ""
echo "📌 Connection details:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: coinfrs"
echo "   Username: coinfrs"
echo "   Password: coinfrs123"
echo ""
echo "🔧 Useful commands:"
echo "   Stop database:    docker stop coinfrs-postgres"
echo "   Start database:   docker start coinfrs-postgres"
echo "   View logs:        docker logs coinfrs-postgres"
echo "   Connect to psql:  docker exec -it coinfrs-postgres psql -U coinfrs -d coinfrs"
echo ""