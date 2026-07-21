import logging
import json
from flask import request, Response
from flask.views import View
from serializers.userSerializers import UserSerializer
from utils.user import schema_validation

class SignUp(View):
    methods = ['POST']

    @schema_validation('UserCreate')
    def dispatch_request(self, *args, **kwargs):
        data = request.get_json()
        serializer = UserSerializer(data)

        try:
            user = serializer.create()
        except Exception as e:
            logging.error(f"User Signup Error creating user on service :: {data.get('uuid')} :: {e} :: {data}")

            return Response(
                response=json.dumps({"error": f"Error creating user  {str(e)}"}),
                status=400,
                mimetype="application/json"
            )

        return Response(
            response=json.dumps({'uuid': user.uuid}),
            status=201,
            mimetype='application/json'
        )


class Login(View):
    methods = ['POST']

    @schema_validation('UserLogin')
    def dispatch_request(self, *args, **kwargs):
        data = request.get_json()
        serializer = UserSerializer(data)

        try:
            user = serializer.login()
        except Exception as e:
            logging.error(f"User Login Error on service :: {e} :: {data}")
            return Response(
                response=json.dumps({"error": f"Error logging in user {str(e)}"}),
                status=400,
                mimetype="application/json"
            )

        return Response(
            response=json.dumps({
                'uuid': user.uuid,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'user_type': user.user_type,
                'is_active': user.is_active,
                'created_on': user.created_on.isoformat() if user.created_on else None,
                'modified_on': user.modified_on.isoformat() if user.modified_on else None,
            }),
            status=200,
            mimetype='application/json'
        )


def serialize_user(user):
    return {
        'uuid': user.uuid,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': user.phone_number,
        'user_type': user.user_type,
        'is_active': user.is_active,
        'created_on': user.created_on.isoformat() if user.created_on else None,
        'modified_on': user.modified_on.isoformat() if user.modified_on else None,
    }


class UserList(View):
    methods = ['GET']

    def dispatch_request(self, *args, **kwargs):
        serializer = UserSerializer()
        users = serializer.list_users()

        return Response(
            response=json.dumps([serialize_user(user) for user in users]),
            status=200,
            mimetype='application/json'
        )
