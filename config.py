import os

class Config:
    """Configuración base para la aplicación Flask"""
    
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = 'sqlite:///asplot_database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de seguridad
    SECRET_KEY = 'asplot-center-secret-key-2025'
    
    # Configuración de archivos
    UPLOAD_FOLDER = os.path.join('static', 'uploads', 'planos')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB máximo por archivo
    
    # Tipos de archivos permitidos para planos
    ALLOWED_EXTENSIONS = {'pdf', 'dwg', 'dxf', 'jpg', 'jpeg', 'png'}
    
    # Configuración de sesión
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora
    
    @staticmethod
    def init_app(app):
        """Inicializar configuración específica de la aplicación"""
        pass

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False

# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
