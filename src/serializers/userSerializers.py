from configuration.db_routing import db, session_rollback
from models.user import User
from werkzeug.exceptions import HTTPException
from sqlalchemy import func
from utils.user import set_uuid
from flask import abort
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
    is_valid = False
    username = None
    uuid = None

    def create_username(self, email, first_name, last_name):
        return first_name

    def __init__(self, data=None):
        email = ''
        first_name = None
        last_name = None
        _uuid = None
        _username = None
        user_type = None

        if data:
            email = data.get('email', '')
            first_name = data.get('first_name') or data.get('firstname')
            last_name = data.get('last_name') or data.get('lastname')
            _uuid = data.get('uuid', None)
            _username = data.get('username', None)
            user_type = data.get('user_type', )

        if not _uuid:
            set_uuid(data, 'uuid')
            if data:
                _uuid = data.get('uuid', None)

            if not _uuid:
                logging.warning('Unable to generate UUID')
                raise IndefiniteUserProfileData('Unable to generate UUID')
            
            if not (first_name or last_name):
                logging.error("first_name/last_name is required")
                raise IndefiniteUserProfileData('first_name/last_name is required')
        
            if not email:
                logging.error('Email is required')
                raise IndefiniteUserProfileData('Email is required')

            if not _username:
                _username = self.create_username(email, first_name, last_name)
                if not _username:
                    logging.warning('Unable to generate username')
                    raise IndefiniteUserProfileData('Unable to generate username')

            if User.query.filter(func.lower(User.username) == func.lower(_username)).\
                    filter(User.uuid != _uuid).first():
                logging.warning(f'user already exists {_username}')
                raise DuplicateUser(f'user already exists {_username}')
            
            self.__setattr__('is_valid', True)
            self.__setattr__('username', _username)
            self.__setattr__('uuid', _uuid)


    @session_rollback(db)
    def create(self, validated_data):
        # Align keys if firstname/lastname are used in input but model needs first_name/last_name
        if 'firstname' in validated_data and 'first_name' not in validated_data:
            validated_data['first_name'] = validated_data.pop('firstname')
        if 'lastname' in validated_data and 'last_name' not in validated_data:
            validated_data['last_name'] = validated_data.pop('lastname')

        validated_data.update({'email': str(validated_data.get('email')).lower()})
        user = User(**validated_data)
        db.session.add(user)
        
        try:
            db.session.commit()
            logging.info('User created Successfully')
        except Exception as e:
            logging.error(f'::Exception in User Creation Serializer :: Exception: {e}')
            abort(400)
        return user
