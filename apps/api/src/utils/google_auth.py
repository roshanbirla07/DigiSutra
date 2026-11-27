import secrets

import jwt
from sqlalchemy import func
from werkzeug.security import generate_password_hash

from configuration import variables
from configuration.db_routing import db, session_rollback
from models.user import User
from utils.auth import AuthError
from utils.constants import USER_TYPE


google_keys = jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs", timeout=5)


def google_client_id():
    return getattr(variables, "CLIENT_ID", "")


def verify_google_token(credential):
    try:
        key = google_keys.get_signing_key_from_jwt(credential).key
        claims = jwt.decode(
            credential, key, algorithms=["RS256"], audience=google_client_id(),
            issuer=["https://accounts.google.com", "accounts.google.com"],
            options={"require": ["sub", "exp", "iat", "iss", "aud", "email"]},
        )
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise AuthError("Invalid or expired Google credential") from exc
    subject = claims["sub"]
    if not isinstance(subject, str) or not subject.isascii() or not subject.isdigit() or len(subject) > 40:
        raise AuthError("Invalid Google account ID")
    if claims.get("email_verified") is not True:
        raise AuthError("Google email must be verified")
    return claims


@session_rollback(db)
def google_user(claims):
    # The provider subject stays stable even when the account email changes.
    user_uuid = f"google::{claims['sub']}"
    user = User.query.filter_by(uuid=user_uuid).first()
    if user:
        if str(user.is_active).lower() in {"false", "0", "inactive"}:
            raise AuthError("User is inactive")
        return user
    email = claims["email"]
    if not isinstance(email, str) or not email or len(email) > 50:
        raise AuthError("Google email is unsupported")
    if User.query.filter(func.lower(User.email) == email.lower()).first():
        raise AuthError("An account with this email already exists. Sign in with your password.")
    user = User(
        uuid=user_uuid, username=f"google_{secrets.token_hex(12)}", email=email.lower(),
        first_name=str(claims.get("given_name") or claims.get("name") or "Google user")[:50],
        last_name=str(claims.get("family_name") or "")[:50],
        password=generate_password_hash(secrets.token_urlsafe(48)),
        user_type=USER_TYPE.CUSTOMER.value, is_active="true",
    )
    db.session.add(user)
    db.session.commit()
    return user
