import datetime

from configuration.db_routing import SessionSQLAlchemy
from sqlalchemy import func


db=SessionSQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    
    USER_TYPES= [('Buyer', 'Buyer'),
                ('SELLER', 'Seller'),
                ('ADMIN', 'Admin')
                ]
    
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(50),unique=True,nullable=False)
    password = db.Coumn(db.String(50),nullable=False)
    email = db.Coumn(db.String(50))
    first_name=db.Column(db.String(50),nullable=False)
    last_name=db.Column(db.String(50))
    phone_number=db.Column(db.String(13))
    uuid = db.Column(db.String(50),unique=True,nullable=False)
    created_on = db.Column(db.DateTime)
    modified_on = db.Column(db.DateTime)
    changed_by = db.Column(db.String(50))
    is_active = db.Column(db.String(15))
    user_type = db.Column(db.String(50))

    __table_args__ = (
        db.Index('user_func_lower_email_idx',func.lower(email)),
        db.Index('user_func_lower_username_idx',func.lower(username))
    )
    





    class SELLERUser(db.Model):
        __tablename__ = 'sellers'

        id = db.Column(db.Integer, primary_key=True)
        user = db.relationship('User',backref=db.backref('sellers', lazy='dynamic'))
        user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
