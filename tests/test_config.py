from config import Config


class TestConfig(Config):
    TESTING = True
    ALCHEMICAL_DATABASE_URL = "sqlite://"
    DATABASE_URL = ALCHEMICAL_DATABASE_URL
    SECRET_KEY = "test-secret-key"
    WTF_CSRF_ENABLED = False
    ITEMS_PER_PAGE = 20
