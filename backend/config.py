import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Enhanced database configuration with PostgreSQL support
    use_postgresql = os.environ.get('USE_POSTGRESQL', 'false').lower() == 'true'

    if use_postgresql:
        # Use PostgreSQL configuration
        pg_user = os.environ.get('POSTGRES_USER', 'erp_user')
        pg_password = os.environ.get('POSTGRES_PASSWORD', '271828')
        pg_host = os.environ.get('POSTGRES_HOST', 'localhost')
        pg_port = os.environ.get('POSTGRES_PORT', '5432')
        pg_db = os.environ.get('POSTGRES_DB', 'erp_database')

        SQLALCHEMY_DATABASE_URI = f'postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}'
        print(f"[DB] Using PostgreSQL: {pg_host}:{pg_port}/{pg_db}")
    else:
        # Fallback to SQLite
        _database_url = os.environ.get('DATABASE_URL')
        _fallback_url = os.environ.get('DATABASE_URL_FALLBACK', 'sqlite:///erp_development.db')

        if _database_url:
            SQLALCHEMY_DATABASE_URI = _database_url
            print(f"[DB] Using primary database: {_database_url}")
        else:
            SQLALCHEMY_DATABASE_URI = _fallback_url
            print(f"[DB] Using fallback database: {_fallback_url}")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database Performance Configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # CORS - Support both localhost and network access
    # Read from environment variable first, fallback to hardcoded values
    _cors_origins_env = os.environ.get('CORS_ORIGINS')
    if _cors_origins_env:
        CORS_ORIGINS = [origin.strip() for origin in _cors_origins_env.split(',')]
    else:
        CORS_ORIGINS = [
            # Localhost origins
            'http://localhost:3000', 
            'http://localhost:5173', 
            'http://localhost:5174', 
            'http://localhost:5175', 
            'http://localhost:5176', 
            'http://localhost:5177',
            'http://localhost:5178',
            # Network IP origins for WiFi access (updated to current network config)
            'http://172.20.10.10:3000',
            'http://172.20.10.10:5173',
            'http://172.20.10.10:5174',
            'http://172.20.10.10:5175',
            'http://172.20.10.10:5176',
            'http://172.20.10.10:5177',
            'http://172.20.10.10:5178',
            # Legacy network IP support (keeping for compatibility)
            'http://192.168.0.106:3000',
            'http://192.168.0.106:5173',
            'http://192.168.0.106:5174',
            'http://192.168.0.106:5175',
            'http://192.168.0.106:5176',
            'http://192.168.0.106:5177',
            'http://192.168.0.106:5178'
        ]
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}