from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from config import Config

# Initialize app and API
app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
db = SQLAlchemy(app)
api = Api(app)


if __name__ == '__main__':
    db.create_all()  # Create tables
    app.run(debug=True)