from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)
    Migrate(app, db)

    # Import and register blueprints
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
