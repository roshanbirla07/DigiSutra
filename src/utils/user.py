from validationschema import *

def schema_validation(schema):
    
    data = request.get_json() if request.method != 'GET' else request.args.to_dict()

    if not data and request.method != 'GET':
        return jsonify({'error': 'No data provided'}), 400
    
    validator = Validator(validationschema.get(schema))
    if validator.validate(data):
        return f(*args, **kwargs)
    return jsonify({'error': 'Invalid data'}), 400

def set_uuid(data, uuid_key):
    if data:
        import uuid
        key = uuid_key if uuid_key else 'uuid'
        data.update({key:f'user::{uuid.uuid1()}'})
    return data