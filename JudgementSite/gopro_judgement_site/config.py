# config.py
import secrets
import os
from datetime import timedelta

class Config:
    # Use environment variables or secure default for secret key
    SECRET_KEY = secrets.token_hex(128)
    
    # Use environment variables for database credentials
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST')
    DB_NAME = os.environ.get('DB_NAME')
    
    SQLALCHEMY_DATABASE_URI = f'mysql+mysqldb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secure cookie settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Content size limits
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE', 100)) * 1024 * 1024
    
    # Debug and environment
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
