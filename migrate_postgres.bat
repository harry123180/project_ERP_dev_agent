@echo off
echo PostgreSQL Migration Script
echo ==========================

REM Set environment variables for PostgreSQL
set USE_POSTGRESQL=true
set POSTGRES_USER=erp_user
set POSTGRES_PASSWORD=271828
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
set POSTGRES_DB=erp_database

cd backend

echo.
echo Step 1: Creating initial migration...
flask db migrate -m "Initial migration for PostgreSQL"

echo.
echo Step 2: Applying migration to database...
flask db upgrade

echo.
echo Migration complete!
pause