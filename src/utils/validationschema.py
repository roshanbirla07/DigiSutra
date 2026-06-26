
UserCreateSchema = {

    'firstname': {'type': 'string', 'maxlength': 50, 'nullable':False, 'required': True},
    'lastname': {'type': 'string', 'maxlength': 50, 'nullable':False, 'required': False},
    'email': {'type': 'string', 'maxlength': 100, 'nullable':False, 'required': True},
}