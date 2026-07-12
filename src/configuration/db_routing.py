from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_sqlalchemy import SQLAlchemy
from configuration.variables import POSTGRES_DB_URI
from functools import wraps
from functools import lru_cache

@lru_cache(maxsize=1)
def get_primary_engine():
    return create_engine(POSTGRES_DB_URI, logging_name='primary')

class SessionSQLAlchemy(SQLAlchemy):

    def create_session(self, options):
        engine = get_primary_engine()
        s = scoped_session(sessionmaker(bind=engine))
        return s()

db = SessionSQLAlchemy()


def session_rollback(db_instance):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except IntegrityError:
                raise
            except Exception:
                db_instance.session.rollback()
                raise
        return wrapped
    return wrapper
