UserCreateSchema = {
    'firstname': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': True},
    'lastname': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': False},
    'email': {'type': 'string', 'maxlength': 100, 'nullable': False, 'required': True},
    'password': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': True},
}

UserLoginSchema = {
    'username': {'type': 'string', 'maxlength': 50, 'nullable': False, 'required': True},
    'password': {'type': 'string', 'maxlength': 128, 'nullable': False, 'required': True},
}

validationschema = {
    'UserCreate': UserCreateSchema,
    'UserLogin': UserLoginSchema,
}
