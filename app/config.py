import os


class Config:
    SECRET_KEY = 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:admin123@localhost/coffeedb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
