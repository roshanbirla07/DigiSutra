from functools import wraps
from flask import request, jsonify
from cerberus import Validator
from utils.validationschema import validationschema

def schema_validation(schema):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json() if request.method != 'GET' else request.args.to_dict()

            if not data and request.method != 'GET':
                return jsonify({'error': 'No data provided'}), 400
            
            schema_dict = validationschema.get(schema)
            if not schema_dict:
                return jsonify({'error': f'Schema {schema} not found'}), 500
                
            validator = Validator(schema_dict)
            if validator.validate(data):
                return f(*args, **kwargs)
            return jsonify({'error': 'Invalid data', 'details': validator.errors}), 400
        return decorated_function
    return decorator
