from configuration.db_routing import db, session_rollback
from models.user import User
from werkzeug.exceptions import HTTPException
from sqlalchemy import func
from flask import abort
from utils.constants import USER_TYPE
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import logging


class IndefiniteUserProfileData(HTTPException):
    code = 400
    description = 'User data is indefinite. provide specific details'

    def __init__(self, msg=None):
        super().__init__()
        self.description = msg if msg else self.description

class DuplicateUser(HTTPException):
    code = 400
    description = 'User data is duplicate'

    def __init__(self, msg=None):
        super().__init__()
        self.description = msg if msg else self.description


class UserSerializer(object):
    def __init__(self, data=None):
        self.data = data or {}
        self.is_valid = False
        self.username = None
        self.uuid = None
        self.user_type = None

    def create_username(self, email, first_name, last_name):
        return first_name

    def validate_create_data(self, validated_data):
        first_name = validated_data.get('first_name') or validated_data.get('firstname')
        last_name = validated_data.get('last_name') or validated_data.get('lastname')
        email = validated_data.get('email', '')
        password = validated_data.get('password')

        if not (first_name or last_name):
            raise IndefiniteUserProfileData('first_name/last_name is required')
        if not email:
            raise IndefiniteUserProfileData('Email is required')
        if not password:
            raise IndefiniteUserProfileData('Password is required')

        return first_name, last_name, email, password

    def prepare_create_data(self, validated_data):
        first_name, last_name, email, password = self.validate_create_data(validated_data)

        validated_data['uuid'] = f"user::{uuid.uuid4()}"
        validated_data['username'] = validated_data.get('username') or self.create_username(
            email, first_name, last_name
        )
        if not validated_data['username']:
            raise IndefiniteUserProfileData('Unable to generate username')

        if 'firstname' in validated_data and 'first_name' not in validated_data:
            validated_data['first_name'] = validated_data.pop('firstname')
        if 'lastname' in validated_data and 'last_name' not in validated_data:
            validated_data['last_name'] = validated_data.pop('lastname')

        validated_data['email'] = str(email).lower()
        validated_data['user_type'] = validated_data.get('user_type') or USER_TYPE.CUSTOMER
        validated_data['password'] = generate_password_hash(password)

        return validated_data

    @session_rollback(db)
    def create(self, validated_data=None):
        validated_data = dict(validated_data or self.data)
        validated_data = self.prepare_create_data(validated_data)

        if User.query.filter(func.lower(User.username) == func.lower(validated_data['username'])).\
                filter(User.uuid != validated_data['uuid']).first():
            logging.warning(f'user already exists {validated_data["username"]}')
            raise DuplicateUser(f'user already exists {validated_data["username"]}')

        user = User(**validated_data)
        db.session.add(user)
        
        try:
            db.session.commit()
            logging.info('User created Successfully')
        except Exception as e:
            logging.error(f'::Exception in User Creation Serializer :: Exception: {e}')
            abort(400)

        self.is_valid = True
        self.username = user.username
        self.uuid = user.uuid
        self.user_type = user.user_type
        return user

    @session_rollback(db)
    def put(self, validated_data=None):
        validated_data = dict(validated_data or self.data)
        user_uuid = validated_data.get('uuid')

        if not user_uuid:
            raise IndefiniteUserProfileData('uuid is required for update')

        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            raise IndefiniteUserProfileData('User not found')

        if 'firstname' in validated_data:
            validated_data['first_name'] = validated_data.pop('firstname')
        if 'lastname' in validated_data:
            validated_data['last_name'] = validated_data.pop('lastname')
        if 'email' in validated_data:
            validated_data['email'] = str(validated_data['email']).lower()
        if 'password' in validated_data and validated_data['password']:
            validated_data['password'] = generate_password_hash(validated_data['password'])
        if not validated_data.get('user_type'):
            validated_data['user_type'] = user.user_type or USER_TYPE.CUSTOMER

        for key, value in validated_data.items():
            if key != 'uuid' and hasattr(user, key):
                setattr(user, key, value)

        try:
            db.session.commit()
        except Exception as e:
            logging.error(f'::Exception in User Update Serializer :: Exception: {e}')
            abort(400)
        return user

    def login(self, validated_data=None):
        validated_data = dict(validated_data or self.data)
        username = validated_data.get('username')
        password = validated_data.get('password')

        if not username:
            raise IndefiniteUserProfileData('username is required')
        if not password:
            raise IndefiniteUserProfileData('password is required')

        user = User.query.filter(func.lower(User.username) == func.lower(username)).first()
        if not user:
            raise IndefiniteUserProfileData('Invalid username or password')

        if not check_password_hash(user.password, password):
            raise IndefiniteUserProfileData('Invalid username or password')

        return user
