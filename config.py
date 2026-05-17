import os
from pathlib import Path

base_dir = Path(__file__).resolve().parent
data_dir = base_dir / "data"
env_file = base_dir / ".env"
from dotenv import load_dotenv

load_dotenv(str(env_file))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "hard-to-guess"
    POSTGRES_USER = os.environ.get("POSTGRES_USER") or "clear_grid"
    POSTGRES_DB = os.environ.get("POSTGRES_DB") or "clear_grid"
    PGADMIN_DEFAULT_EMAIL = (
        os.environ.get("PGADMIN_DEFAULT_EMAIL") or "pgadmin@example.com"
    )
    DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///" + str(
        base_dir / "app" / "app.db"
    )
    DRY_RUN_DATA_PATH = os.getenv("DRY_RUN_DATA_PATH")
    ITEMS_PER_PAGE = 20
    LANGUAGES = ["en"]
