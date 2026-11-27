import logging
import json
from flask import g, request, Response, jsonify
from flask.views import View
from serializers.userSerializers import UserSerializer
from utils.auth import AuthError, create_access_token, require_auth
from utils.google_auth import google_client_id, google_user, verify_google_token
from utils.constants import USER_TYPE
from utils.user import schema_validation

class SignUp(View):
    methods = ['POST']

    @schema_validation('UserCreate')
    def dispatch_request(self, *args, **kwargs):
        data = request.get_json()
        data["user_type"] = USER_TYPE.CUSTOMER.value
        serializer = UserSerializer(data)

        try:
            user = serializer.create()
        except Exception as e:
            logging.error("event=%s error_type=%s", 'User Signup Error creating user on service', type(e).__name__)

            return Response(
                response=json.dumps({"error": "Request could not be completed"}),
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
            user, token = serializer.login_with_token()
        except Exception as e:
            logging.error("event=%s error_type=%s", 'User Login Error on service', type(e).__name__)
            return Response(
                response=json.dumps({"error": "Request could not be completed"}),
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
                'token': token,
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


class GoogleLogin(View):
    methods = ['GET', 'POST']

    def dispatch_request(self):
        client_id = google_client_id()
        if request.method == 'GET':
            return jsonify({'client_id': client_id})
        if not client_id:
            return jsonify({'error': 'Google sign-in is not configured'}), 503
        data = request.get_json(silent=True)
        credential = data.get('credential') if isinstance(data, dict) else None
        if not isinstance(credential, str) or not credential:
            return jsonify({'error': 'Google credential is required'}), 400
        try:
            user = google_user(verify_google_token(credential))
            token = create_access_token(user)
        except AuthError as exc:
            return jsonify({'error': exc.description}), 401
        return jsonify({**serialize_user(user), 'token': token})


class UserList(View):
    methods = ['GET']

    @require_auth(roles=["admin"], methods=["GET"])
    def dispatch_request(self, *args, **kwargs):
        serializer = UserSerializer()
        users = serializer.list_users()

        return Response(
            response=json.dumps([serialize_user(user) for user in users]),
            status=200,
            mimetype='application/json'
        )
