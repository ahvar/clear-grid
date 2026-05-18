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
    ALCHEMICAL_DATABASE_URL = (
        os.environ.get("ALCHEMICAL_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
        or "sqlite:///" + str(base_dir / "app" / "app.db")
    )
    DATABASE_URL = ALCHEMICAL_DATABASE_URL
    NESO_API_BASE_URL = (
        os.environ.get("NESO_API_BASE_URL") or "https://api.neso.energy/api/3/action"
    )
    NESO_RESOURCE_ID = (
        os.environ.get("NESO_RESOURCE_ID") or "a63ab354-7e68-44c2-ad96-c6f920c30e85"
    )
    INGEST_ON_STARTUP = os.environ.get("INGEST_ON_STARTUP") or "false"
    INGEST_DELIVERY_DATE = os.environ.get("INGEST_DELIVERY_DATE")
    INGEST_PARTICIPANT = os.environ.get("INGEST_PARTICIPANT")
    INGEST_RESOURCE_ID = os.environ.get("INGEST_RESOURCE_ID")
    DRY_RUN_DATA_PATH = os.getenv("DRY_RUN_DATA_PATH")
    ITEMS_PER_PAGE = 20
    LANGUAGES = ["en"]
