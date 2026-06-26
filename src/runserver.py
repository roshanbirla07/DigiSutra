
from flask import Flask, jsonify, request
from configuration.config import create_app

app = create_app()

@app.route('/api/hello', methods=['GET'])
def hello():    
    name = request.args.get('name', 'World')
    return jsonify({'message': f'Hello, {name}!'})  

