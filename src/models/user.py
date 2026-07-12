import datetime
from sqlalchemy import func
from configuration.db_routing import db
from utils.constants import USER_TYPE

class User(db.Model):
    __tablename__ = 'user'
    
    USER_TYPES = [
        ('CS', USER_TYPE.CUSTOMER),
        ('SL', USER_TYPE.SELLER),
        ('AD', USER_TYPE.ADMIN)
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(50))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50))
    phone_number = db.Column(db.String(13))
    uuid = db.Column(db.String(50), unique=True, nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_on = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    changed_by = db.Column(db.String(50))
    is_active = db.Column(db.String(15))
    user_type = db.Column(db.String(50))

    __table_args__ = (
        db.Index('user_func_lower_email_idx', func.lower(email)),
        db.Index('user_func_lower_username_idx', func.lower(username))
    )


class SELLERUser(db.Model):
    __tablename__ = 'sellers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship('User', backref=db.backref('sellers', lazy='dynamic'))
