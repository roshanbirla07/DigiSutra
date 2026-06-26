import logging
from models.user import User
from flask.view import MethodView, View
from flask import g
from serializers.userSerializers import UserSerializer

class SignUp(View):
    mothod = ['POST']

    @schema_validation('UserCreate')
    def dispatch_request(self, *args , **kwargs):

        serializer = UserSerializer(request.get_json())
        username = serializer.username
        request.get_json().update({'username': username, 'uuid': serializer.uuid})

        try:
            user = serializer.create(data)

        except Exception as e:
            logging.error(f"User Signup Error creating user on UMS :: {data.get('uuid')} :: {e} :: {data}")

            return Response(response = json.dumps(
                {"error": f"Error creating user on UMS {e.message if e.message else ""}"}),
                status = 400,
                mimetype = "application/json"
            )


        return Response(response=json.dumps({'uuid': user.uuid}),
                        status = 201,
                        mimetype = 'application/json'
                        )
