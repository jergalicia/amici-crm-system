import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-amici-magazine-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///amici.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folders
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    MANUALS_FOLDER = os.path.join(os.getcwd(), 'static', 'manuals')
    EMBASSIES_FOLDER = os.path.join(os.getcwd(), 'static', 'embassies')
    USERS_FOLDER = os.path.join(os.getcwd(), 'static', 'users')
