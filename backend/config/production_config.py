# Enhanced Production Configuration
# Comprehensive production-ready configuration with performance optimization

import os
import redis
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class ProductionConfig:
    """Production configuration with advanced features"""
    
    # Core Application Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-in-production-use-vault'
    DEBUG = False
    TESTING = False
    
    # Database Configuration with Connection Pooling
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://erp_user:secure_password@postgres-primary:5432/erp_system'
    
    # Advanced Database Engine Options
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,                    # Base connection pool size
        'max_overflow': 30,                 # Additional connections beyond pool_size
        'pool_pre_ping': True,              # Validate connections before use
        'pool_recycle': 3600,               # Recycle connections every hour
        'echo': False,                      # Disable SQL logging in production
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'ERP_Backend_Production',
            'options': '-c default_transaction_isolation=read_committed'
        }
    }
    
    # Read Replica Configuration
    SQLALCHEMY_BINDS = {
        'read_replica': os.environ.get('READ_REPLICA_URL') or \
            'postgresql://erp_readonly:password@postgres-replica:5432/erp_system'
    }
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://redis-cluster:6379/0'
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
    
    # Cache Configuration
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = 'erp_cache:'
    
    # Session Configuration
    SESSION_TYPE = 'redis'
    SESSION_REDIS = redis.from_url(REDIS_URL)
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'erp_session:'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    JWT_ALGORITHM = 'HS256'
    
    # Celery Configuration (Async Processing)
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or \
        'redis://redis-cluster:6379/1'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or \
        'redis://redis-cluster:6379/2'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'Asia/Taipei'
    CELERY_ENABLE_UTC = True
    
    # API Configuration
    API_RATE_LIMIT = os.environ.get('API_RATE_LIMIT', '1000 per hour')
    API_RATE_LIMIT_STORAGE_URL = REDIS_URL
    
    # CORS Configuration
    CORS_ORIGINS = [
        'https://erp.company.com',
        'https://app.erp.company.com'
    ]
    CORS_ALLOW_HEADERS = [
        'Accept',
        'Accept-Language',
        'Content-Language',
        'Content-Type',
        'Authorization'
    ]
    CORS_METHODS = ['GET', 'HEAD', 'POST', 'OPTIONS', 'PUT', 'PATCH', 'DELETE']
    CORS_SUPPORTS_CREDENTIALS = True
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    UPLOAD_FOLDER = '/app/uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'docx'}
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(name)s %(levelname)s %(message)s'
    LOG_FILE = '/app/logs/erp.log'
    LOG_MAX_BYTES = 10485760  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Security Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT')
    SECURITY_CONFIRMABLE = True
    SECURITY_REGISTERABLE = False
    SECURITY_RECOVERABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_PASSWORDLESS = False
    SECURITY_CHANGEABLE = True
    
    # Monitoring and Observability
    PROMETHEUS_METRICS = True
    JAEGER_AGENT_HOST = os.environ.get('JAEGER_AGENT_HOST', 'jaeger-agent')
    JAEGER_AGENT_PORT = int(os.environ.get('JAEGER_AGENT_PORT', '6831'))
    
    # Business Logic Configuration
    DEFAULT_TIMEZONE = 'Asia/Taipei'
    DEFAULT_CURRENCY = 'TWD'
    DEFAULT_TAX_RATE = 0.05
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Feature Flags
    FEATURE_FLAGS = {
        'async_processing': True,
        'real_time_notifications': True,
        'advanced_reporting': True,
        'audit_logging': True,
        'performance_monitoring': True
    }
    
    # Email Configuration (for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Vault Configuration (Secrets Management)
    VAULT_URL = os.environ.get('VAULT_URL', 'https://vault.company.com')
    VAULT_ROLE_ID = os.environ.get('VAULT_ROLE_ID')
    VAULT_SECRET_ID = os.environ.get('VAULT_SECRET_ID')
    
    # Health Check Configuration
    HEALTH_CHECK_ENABLED = True
    HEALTH_CHECK_ENDPOINT = '/health'
    
    @staticmethod
    def init_app(app):
        """Initialize application with production configuration"""
        # Set up logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            if not os.path.exists('/app/logs'):
                os.mkdir('/app/logs')
            
            file_handler = RotatingFileHandler(
                ProductionConfig.LOG_FILE,
                maxBytes=ProductionConfig.LOG_MAX_BYTES,
                backupCount=ProductionConfig.LOG_BACKUP_COUNT
            )
            file_handler.setFormatter(logging.Formatter(ProductionConfig.LOG_FORMAT))
            file_handler.setLevel(getattr(logging, ProductionConfig.LOG_LEVEL))
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(getattr(logging, ProductionConfig.LOG_LEVEL))
            app.logger.info('ERP System startup - Production Configuration')


class StagingConfig(ProductionConfig):
    """Staging configuration - similar to production but with debug features"""
    DEBUG = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        **ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS,
        'echo': True  # Enable SQL logging in staging
    }
    LOG_LEVEL = 'DEBUG'


class TestingConfig(ProductionConfig):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


# Configuration mapping
config = {
    'development': ProductionConfig,  # Use production config as base
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}