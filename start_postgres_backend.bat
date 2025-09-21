@echo off
echo Starting ERP Backend with PostgreSQL...
echo.
set USE_POSTGRESQL=true
set POSTGRES_USER=erp_user
set POSTGRES_PASSWORD=271828
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
set POSTGRES_DB=erp_database

echo Database: PostgreSQL (localhost:5432/erp_database)
echo.
cd backend
python app.py