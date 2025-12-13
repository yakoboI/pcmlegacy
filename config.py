import os
from datetime import timedelta
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    if not os.environ.get('SECRET_KEY') and os.environ.get('FLASK_ENV', '').lower() == 'production':
        raise ValueError("SECRET_KEY environment variable must be set in production!")
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///pcm_store.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'connect_args': {'check_same_thread': False} if 'sqlite' in (os.environ.get('DATABASE_URL') or 'sqlite:///pcm_store.db') else {}
    }
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 512 * 1024 * 1024
    MAX_FORM_MEMORY_SIZE = 512 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'txt', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v', '3gp', 'ppt', 'pptx', 'xls', 'xlsx', 'zip', 'rar', '7z'}
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@pcmlegacy.store'
    MPESA_API_KEY = os.environ.get('MPESA_API_KEY')
    MPESA_PUBLIC_KEY = os.environ.get('MPESA_PUBLIC_KEY')
    MPESA_SERVICE_PROVIDER_CODE = os.environ.get('MPESA_SERVICE_PROVIDER_CODE')
    MPESA_COUNTRY = os.environ.get('MPESA_COUNTRY', 'TZN')
    MPESA_CURRENCY = os.environ.get('MPESA_CURRENCY', 'TZS')
    MPESA_ENV = os.environ.get('MPESA_ENV', 'sandbox')
    MPESA_IPG_ADDRESS = os.environ.get('MPESA_IPG_ADDRESS', 'openapi.m-pesa.com')
    MPESA_IPG_PORT = int(os.environ.get('MPESA_IPG_PORT', 443))
    MPESA_IPG_ORIGIN = os.environ.get('MPESA_IPG_ORIGIN', '*')
    MPESA_SESSION_PATH = os.environ.get('MPESA_SESSION_PATH')
    MPESA_C2B_SINGLE_STAGE_PATH = os.environ.get('MPESA_C2B_SINGLE_STAGE_PATH')
    MPESA_SESSION_READY_DELAY = os.environ.get('MPESA_SESSION_READY_DELAY', 30)
    MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL')
    ITEMS_PER_PAGE = 12
    ADMIN_ITEMS_PER_PAGE = 20
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    RATELIMIT_DEFAULT = "100 per hour"
    POSTS_PER_PAGE = 10
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///pcm_store_dev.db'
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///pcm_store.db'
    SESSION_COOKIE_SECURE = True
    SERVER_NAME = os.environ.get('SERVER_NAME') or 'pcmlegacy.store'
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME') or 'https'
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
