import os
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
