#!/bin/bash
echo "========================================="
echo "🚀 Starting CrownieVerse on Railway"
echo "========================================="
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"

# Start healthcheck server in background
echo "📊 Starting healthcheck server on port 8081"
python healthcheck_server.py &
HEALTH_PID=$!
echo "✅ Healthcheck server started with PID: $HEALTH_PID"

# Wait a moment for healthcheck server to start
sleep 2

# Test healthcheck server
echo "Testing healthcheck server..."
curl -s http://localhost:8081/health -o /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Healthcheck server is responding"
else
    echo "⚠️ Healthcheck server test failed"
fi

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput
if [ $? -eq 0 ]; then
    echo "✅ Migrations completed"
else
    echo "❌ Migrations failed"
    exit 1
fi

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput
if [ $? -eq 0 ]; then
    echo "✅ Static files collected"
else
    echo "❌ Static files collection failed"
    exit 1
fi

# Start main application
echo "🚀 Starting Gunicorn on port $PORT"
echo "========================================="
exec gunicorn crwn.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 1 \
    --timeout 120 \
    --log-level debug \
    --access-logfile - \
    --error-logfile -