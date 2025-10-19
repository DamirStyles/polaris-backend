# config.py - Configuration for Flask app and LLM analyzer
# Handles development, production, and testing environments

import os
from pathlib import Path


class Config:
    """Base configuration"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    
    MAX_RESULTS_PER_REQUEST = 100
    
    CORS_ENABLED = True
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS') or '*'
    
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    
    @staticmethod
    def init_app(app):
        """Initialize app-specific config"""
        pass


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    @staticmethod
    def init_app(app):
        import logging
        logging.basicConfig(level=logging.DEBUG)


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    SECRET_KEY = os.environ.get('SECRET_KEY')
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    
    @staticmethod
    def init_app(app):
        if not ProductionConfig.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set in production")
        if not ProductionConfig.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY must be set in production")
        
        import logging
        from logging.handlers import RotatingFileHandler
        
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        handler = RotatingFileHandler(
            logs_dir / 'app.log',
            maxBytes=10485760,
            backupCount=10
        )
        handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    GOOGLE_API_KEY = 'test-key'
    
    @staticmethod
    def init_app(app):
        import logging
        logging.basicConfig(level=logging.WARNING)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def validate_config():
    """Validate configuration for current environment"""
    errors = []
    
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        if not os.environ.get('SECRET_KEY'):
            errors.append("SECRET_KEY not set")
        if not os.environ.get('GOOGLE_API_KEY'):
            errors.append("GOOGLE_API_KEY not set")
    
    if env == 'development':
        if not os.environ.get('GOOGLE_API_KEY'):
            errors.append("GOOGLE_API_KEY not set (required for LLM analyzer)")
    
    return errors