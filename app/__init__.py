import os
from flask import Flask, request, current_app
from sqlalchemy import String, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_migrate import Migrate
from alchemical.flask import Alchemical
from config import Config

# TODO: logger here


def get_locale():
    return request.accept_languages.best_match(current_app.config)


migrate = Migrate()
db = Alchemical()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)

    from app.errors import bp as errors_bp

    app.register_blueprint(errors_bp)

    from app.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    from app.cli import register_cli

    register_cli(app)
    return app


from app.models import IngestionRun, AuctionUnitResult
