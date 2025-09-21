#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."

# Wait for PostgreSQL to be ready
while ! nc -z postgres 5432; do
  sleep 1
done

echo "PostgreSQL is ready!"

# Run database migrations if needed
echo "Checking database..."
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database initialized')
"

# Start the application
echo "Starting application..."
exec "$@"
