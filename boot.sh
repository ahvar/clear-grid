#!/bin/bash
export PYTHONPATH=/opt/pipeline:$PYTHONPATH

# Maximum number of retries
MAX_RETRIES=30
RETRY_COUNT=0

if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "POSTGRES_PASSWORD is required. Exiting."
    exit 1
fi

echo "Attempting to connect to PostgreSQL..."

echo "Waiting for database to be ready..."

# Try running migrations with retries
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    flask db upgrade
    if [ $? -eq 0 ]; then
        echo "Database migrations completed successfully!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "Database not ready, retrying in 5 seconds... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 5

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "Failed to connect to database after $MAX_RETRIES attempts. Exiting."
        exit 1
    fi
done

if [ "$INGEST_ON_STARTUP" = "true" ]; then
    echo "Running startup ingestion..."
    flask ingest-unit-results --date "$INGEST_DELIVERY_DATE"
    if [ $? -ne 0 ]; then
        echo "Startup ingestion failed. Exiting."
        exit 1
    fi
fi

# Start the application
echo "Starting Gunicorn server..."
exec gunicorn -b :5000 --access-logfile - --error-logfile - clear_grid_flask_shell_ctx:app
