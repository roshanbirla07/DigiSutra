from sqlalchemy import create_engine
from sqlalchemy import scoped_session,sessionmaker
from flask_sqlalchemy import SQLAlchemy
from configuration.variables import POSTGRES_DB_URI 

engines = {
    'primary': create_engine(POSTGRES_DB_URI , logging_name='primary'),
}

class SessionSQLAlchemy(SQLAlchemy):

    def create_session(self, options):
    
        engine =engines['primary']
        s = scoped_session(sessionmaker(bind=engine))
        return s()

db = SessionSQLAlchemy()


