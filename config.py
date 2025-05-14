import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'images'))
    MAX_IMAGE_WIDTH = int(os.environ.get('MAX_IMAGE_WIDTH', 800))
    MAX_IMAGE_HEIGHT = int(os.environ.get('MAX_IMAGE_HEIGHT', 600))