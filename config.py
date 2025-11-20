import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración base"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False
    
class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    
class TestingConfig(Config):
    """Configuración para testing"""
    DEBUG = True
    TESTING = True

# Seleccionar configuración según el ambiente
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
