# ERP System Docker Deployment Guide

## Overview
This guide explains how to deploy the ERP system using Docker with PostgreSQL database.

## Prerequisites
- Docker Engine 20.10+ installed
- Docker Compose 2.0+ installed
- At least 4GB RAM available for containers

## Quick Start

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd project_ERP_dev_agent
```

### 2. Configure Environment Variables
Copy the example environment file and modify as needed:
```bash
cp .env.example .env
```

Edit `.env` file with your production values:
```env
# PostgreSQL Configuration
POSTGRES_DB=erp_database
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=your-secure-password-here

# Backend Configuration
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Frontend Port (default: 80)
FRONTEND_PORT=80
```

### 3. Build and Run with Docker Compose
```bash
# Build all services
docker-compose build

# Start all services in detached mode
docker-compose up -d

# Check logs
docker-compose logs -f
```

The system will be available at:
- Frontend: http://localhost (or port specified in FRONTEND_PORT)
- Backend API: Internal only (accessed through frontend proxy)
- PostgreSQL: Internal only (port 5432 within Docker network)

### 4. Initial Setup
The database will be automatically initialized with:
- Admin user: username=`admin`, password=`admin123`
- Default categories and storage locations

## Docker Architecture

```
┌─────────────────────┐
│   Frontend (Nginx)  │ ← Port 80 (exposed)
│   Vue.js Static     │
└──────────┬──────────┘
           │ /api/*
           ↓
┌─────────────────────┐
│   Backend (Flask)   │ ← Port 5000 (internal)
│   Gunicorn WSGI     │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  PostgreSQL DB      │ ← Port 5432 (internal)
│   Data Volume       │
└─────────────────────┘
```

## Common Commands

### Container Management
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: Deletes database!)
docker-compose down -v

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Database Operations
```bash
# Access PostgreSQL shell
docker-compose exec postgres psql -U erp_user -d erp_database

# Backup database
docker-compose exec postgres pg_dump -U erp_user erp_database > backup.sql

# Restore database
docker-compose exec -T postgres psql -U erp_user erp_database < backup.sql
```

### Backend Shell Access
```bash
# Access backend container
docker-compose exec backend /bin/bash

# Run database migrations
docker-compose exec backend python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

## Production Deployment

### Security Considerations
1. **Change default passwords** in production
2. **Use strong SECRET_KEY and JWT_SECRET_KEY**
3. **Enable HTTPS** with SSL certificates
4. **Restrict database access** to internal network only
5. **Regular backups** of PostgreSQL data

### Performance Optimization
1. Adjust PostgreSQL settings in `docker-compose.yml`
2. Configure Gunicorn workers based on CPU cores
3. Enable Redis caching (optional)
4. Use CDN for static assets

### Monitoring
- Backend logs: `/app/logs/` in backend container
- Nginx access logs: Check frontend container logs
- PostgreSQL logs: Check postgres container logs

## Troubleshooting

### Container won't start
```bash
# Check logs for errors
docker-compose logs backend
docker-compose logs postgres

# Verify environment variables
docker-compose config
```

### Database connection issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Test connection from backend
docker-compose exec backend python -c "from app import db; print(db.engine.url)"
```

### Port conflicts
If port 80 is already in use, change FRONTEND_PORT in `.env`:
```env
FRONTEND_PORT=8080
```

### Reset everything
```bash
# Stop all containers and remove data
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

## Updates and Maintenance

### Updating the Application
```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Apply database migrations if any
docker-compose exec backend python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# Restart services
docker-compose down
docker-compose up -d
```

### Backup Strategy
Create automated backups using cron:
```bash
# Add to crontab
0 2 * * * docker-compose exec -T postgres pg_dump -U erp_user erp_database > /backups/erp_$(date +\%Y\%m\%d).sql
```

## Support
For issues or questions, please check:
- Application logs in Docker containers
- PostgreSQL connection status
- Environment variable configuration
