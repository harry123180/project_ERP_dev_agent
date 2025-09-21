"""
PostgreSQL 配置檔案
用於從 SQLite 遷移到 PostgreSQL
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """基礎配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # PostgreSQL 配置
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'erp_user')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'your_secure_password')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'erp_database')

    # 構建 PostgreSQL 連接字串
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # 備用 SQLite 配置（用於比較和回滾）
    SQLITE_DATABASE_URI = 'sqlite:///erp_development.db'

    # 選擇使用的資料庫（可通過環境變數切換）
    USE_POSTGRESQL = os.environ.get('USE_POSTGRESQL', 'true').lower() == 'true'

    if not USE_POSTGRESQL:
        SQLALCHEMY_DATABASE_URI = SQLITE_DATABASE_URI
        print("[DB] Using SQLite database")
    else:
        print(f"[DB] Using PostgreSQL database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 資料庫效能配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20,
        'echo': False  # 設為 True 可看到 SQL 語句
    }

    # JWT 配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']

    # CORS 配置
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
            # Network IP origins
            'http://192.168.1.104:3000',
            'http://192.168.1.104:5173',
            'http://192.168.1.104:5174',
            'http://192.168.1.104:5175',
            'http://192.168.1.104:5176',
            'http://192.168.1.104:5177',
            'http://192.168.1.104:5178'
        ]

    # 分頁設定
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

class DevelopmentConfig(Config):
    """開發環境配置"""
    DEBUG = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        'echo': True  # 開發環境顯示 SQL
    }

class ProductionConfig(Config):
    """生產環境配置"""
    DEBUG = False
    # 使用環境變數中的資料庫 URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Heroku 使用 postgres://，但 SQLAlchemy 需要 postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = database_url

    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        'echo': False
    }

class TestingConfig(Config):
    """測試環境配置"""
    TESTING = True
    POSTGRES_DB = 'erp_test_database'
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@"
        f"{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # 測試環境可選擇使用 SQLite
    if os.environ.get('TEST_WITH_SQLITE', 'false').lower() == 'true':
        SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'

    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}