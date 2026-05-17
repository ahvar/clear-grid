import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from config import Config

# print(f"Database URL: {os.environ['DATABASE_URL']}")


class Model(DeclarativeBase):
    metadata = MetaData(
        naming_convention={  # configure naming conventions for indexes and constraints
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


engine = create_engine(Config.DATABASE_URL, echo=True)

Session = sessionmaker(engine)
