# Database Fixtures Management

This directory contains scripts and fixtures for managing standardized test data across different environments.

## 📁 Structure

```
database/
├── scripts/
│   ├── export_fixtures.py    # Export current database to JSON fixtures
│   └── import_fixtures.py    # Import fixtures to database
└── fixtures/
    ├── metadata.json          # Export metadata and statistics
    ├── users.json            # User accounts and profiles
    ├── suppliers.json        # Supplier information
    ├── categories.json       # Item categories
    └── system_settings.json  # System configuration
```

## 🚀 Usage

### Export Current Data
Export current database contents to fixture files:
```bash
cd database/scripts
python export_fixtures.py
```

### Import Test Data
Import standardized test data from fixtures:
```bash
cd database/scripts
python import_fixtures.py
```

## 🔄 Workflow for Remote Deployment

1. **Development Environment**: Export current test data
   ```bash
   python database/scripts/export_fixtures.py
   ```

2. **Version Control**: Commit fixtures to GitHub
   ```bash
   git add database/fixtures/
   git commit -m "Update database fixtures"
   git push
   ```

3. **Remote Environment**: Clone and import fixtures
   ```bash
   git clone <repository-url>
   cd project_ERP_dev_agent
   python database/scripts/import_fixtures.py
   ```

## ✨ Features

- **Duplicate Detection**: Import script skips existing records automatically
- **Timestamp Preservation**: Maintains original created_at/updated_at values
- **Incremental Updates**: System settings are updated rather than skipped
- **Metadata Tracking**: Includes export timestamp and record counts
- **Unicode Support**: Handles Chinese characters correctly

## 🛡️ Safety

- Import operations are transactional (all-or-nothing)
- Existing data is preserved unless explicitly updated
- Rollback on any import errors
- No destructive operations on existing records

## 📊 Current Fixtures

Last exported: `2025-09-23T01:11:07.237211`

- **Users**: 19 accounts (including admin and test users)
- **Suppliers**: 17 vendor records (domestic and international)
- **Categories**: Item classification system
- **System Settings**: Application configuration

## 🔧 Requirements

- Python 3.8+
- Flask application environment
- Database connection configured in `.env`
- SQLAlchemy models properly imported