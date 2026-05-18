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
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)

    from app.errors import bp as errors_bp

    app.register(errors_bp)

    from app.main import bp as main_bp

    app.register(main_bp)

    from app.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    return app


from app.models import IngestionRun, AuctionUnitResult
