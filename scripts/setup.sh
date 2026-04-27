#!/bin/bash
# InboxLift Setup Script for Ubuntu EC2
set -e

echo "🔥 Setting up InboxLift..."

# Check for required tools
command -v docker >/dev/null 2>&1 || { echo "Docker is required. Install: https://docs.docker.com/engine/install/ubuntu/"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1 || { echo "Docker Compose is required"; exit 1; }

# Copy .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example — please edit it with your values"
fi

# Generate secure keys if not set
if grep -q "your-secret-key" .env; then
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    ENC_KEY=$(python3 -c "import secrets; print(secrets.token_hex(16) + '!!' )")
    sed -i "s/your-secret-key-minimum-32-characters-long/$SECRET/" .env
    sed -i "s/your-encryption-key-exactly-32chars!!/$ENC_KEY/" .env
    echo "Generated secure keys in .env"
fi

echo "Starting services..."
docker-compose up -d mysql redis

echo "Waiting for database..."
sleep 10

echo "Running migrations..."
docker-compose run --rm backend alembic upgrade head

echo "Starting all services..."
docker-compose up -d

echo ""
echo "✅ InboxLift is running!"
echo "   Frontend: http://localhost:3000"
echo "   API:      http://localhost:8000"
echo "   API Docs: http://localhost:8000/api/docs"
echo "   Flower:   http://localhost:5555"
echo ""
echo "📧 Add your email accounts in the dashboard to start warming!"
