from utils.constants import USER_TYPE

UserCreateSchema = {
    'firstname': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': True},
    'lastname': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': False},
    'email': {'type': 'string', 'maxlength': 100, 'nullable': False, 'required': True},
    'password': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': True},
    'user_type': {'type': 'string', 'allowed': USER_TYPE.values() + ['creator'], 'nullable': True, 'required': False},
}

UserLoginSchema = {
    'username': {'type': 'string', 'maxlength': 50, 'nullable': True, 'required': False},
    'email': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'password': {'type': 'string', 'maxlength': 128, 'nullable': False, 'required': True},
}

ProductCreateSchema = {
    'owner_uuid': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': True},
    'title': {'type': 'string', 'maxlength': 150, 'nullable': False, 'required': True},
    'description': {'type': 'string', 'maxlength': 5000, 'nullable': True, 'required': False},
    'price': {'type': ['string', 'integer', 'float'], 'nullable': False, 'required': True},
    'currency': {'type': 'string', 'maxlength': 10, 'nullable': True, 'required': False},
    'category': {'type': 'string', 'maxlength': 100, 'nullable': True, 'required': False},
    'is_active': {'type': 'boolean', 'nullable': True, 'required': False},
    'is_public': {'type': 'boolean', 'nullable': True, 'required': False},
}

validationschema = {
    'UserCreate': UserCreateSchema,
    'UserLogin': UserLoginSchema,
    'ProductCreate': ProductCreateSchema,
}
