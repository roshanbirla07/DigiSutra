import datetime
from functools import wraps

import jwt
from flask import g, jsonify, request
from werkzeug.exceptions import HTTPException

from configuration.variables import AUTH_EDDSA_PRIVATE_KEY_PEM, AUTH_EDDSA_PUBLIC_KEY_PEM
from models.user import User


class AuthError(HTTPException):
    code = 401
    description = "Authentication failed"

    def __init__(self, msg=None):
        super().__init__()
        self.description = msg if msg else self.description


def _get_private_key():
    if not AUTH_EDDSA_PRIVATE_KEY_PEM:
        raise AuthError("AUTH_EDDSA_PRIVATE_KEY_PEM is required")
    return AUTH_EDDSA_PRIVATE_KEY_PEM


def _get_public_key():
    if not AUTH_EDDSA_PUBLIC_KEY_PEM:
        raise AuthError("AUTH_EDDSA_PUBLIC_KEY_PEM is required")
    return AUTH_EDDSA_PUBLIC_KEY_PEM


def create_access_token(user, expires_in_seconds=86400):
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": user.uuid,
        "username": user.username,
        "role": user.user_type,
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(seconds=expires_in_seconds)).timestamp()),
    }
    return jwt.encode(payload, _get_private_key(), algorithm="EdDSA")


def verify_access_token(token):
    payload = jwt.decode(
        token,
        _get_public_key(),
        algorithms=["EdDSA"],
        options={"require": ["sub", "exp", "iat"]},
    )
    user_uuid = payload.get("sub")
    user = User.query.filter_by(uuid=user_uuid).first()
    if not user or str(user.is_active).lower() in {"false", "0", "inactive"}:
        raise AuthError("User is inactive or not found")
    return user, payload


def get_bearer_token():
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip()
    return None


def require_auth(roles=None, methods=None):
    allowed_roles = {str(role).lower() for role in roles} if roles else None
    allowed_methods = {str(method).upper() for method in methods} if methods else None

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if allowed_methods and request.method.upper() not in allowed_methods:
                return view_func(*args, **kwargs)

            token = get_bearer_token()
            if not token:
                return jsonify({"error": "Authorization token required"}), 401

            try:
                user, payload = verify_access_token(token)
            except Exception as exc:
                return jsonify({"error": str(exc)}), 401

            if allowed_roles and str(user.user_type).lower() not in allowed_roles:
                return jsonify({"error": "Forbidden"}), 403

            g.user = user
            g.auth_payload = payload
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
