import logging
import json
from flask import request, Response
from flask.views import View
from models.user import User
from serializers.userSerializers import UserSerializer
from utils.user import schema_validation

class SignUp(View):
    methods = ['POST']

    @schema_validation('UserCreate')
    def dispatch_request(self, *args, **kwargs):
        data = request.get_json()
        serializer = UserSerializer(data)
        username = serializer.username
        data.update({'username': username, 'uuid': serializer.uuid})

        try:
            user = serializer.create(data)
        except Exception as e:
            logging.error(f"User Signup Error creating user on UMS :: {data.get('uuid')} :: {e} :: {data}")

            return Response(
                response=json.dumps({"error": f"Error creating user on UMS {str(e)}"}),
                status=400,
                mimetype="application/json"
            )

        return Response(
            response=json.dumps({'uuid': user.uuid}),
            status=201,
            mimetype='application/json'
        )
