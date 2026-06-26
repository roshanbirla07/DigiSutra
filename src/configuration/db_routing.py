from sqlalchemy import create_engine
from sqlalchemy import scoped_session,sessionmaker
from flask_sqlalchemy import SQLAlchemy
from configuration.variables import POSTGRES_DB_URI 
from functools import wraps
engines = {
    'primary': create_engine(POSTGRES_DB_URI , logging_name='primary'),
}

class SessionSQLAlchemy(SQLAlchemy):

    def create_session(self, options):
    
        engine =engines['primary']
        s = scoped_session(sessionmaker(bind=engine))
        return s()

db = SessionSQLAlchemy()


def session_rollback(db):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args,**kwargs):
            try:
                return f(*args,**kwargs)
            except IntegrityError:
                raise
            except:
                db.session.rollback()
                raise
        return wrapped
    return wrapper
