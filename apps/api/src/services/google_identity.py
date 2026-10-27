"""Verify Google ID tokens and map them to local accounts."""
import uuid

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from configuration.db_routing import db
from configuration.variables import GOOGLE_CLIENT_ID
from models.user import User
from utils.constants import USER_TYPE


class GoogleIdentityError(ValueError):
    pass


def verify_google_credential(credential):
    if not GOOGLE_CLIENT_ID:
        raise GoogleIdentityError("Google sign-in is not configured")
    if not isinstance(credential, str) or not credential or len(credential) > 8192:
        raise GoogleIdentityError("Invalid Google credential")
    try:
        claims = id_token.verify_oauth2_token(credential, Request(), GOOGLE_CLIENT_ID)
    except (ValueError, GoogleAuthError) as exc:
        raise GoogleIdentityError("Invalid Google credential") from exc
    sub = claims.get("sub")
    email = claims.get("email")
    if not sub or not email or claims.get("email_verified") is not True:
        raise GoogleIdentityError("A verified Google email is required")
    if len(sub) > 255 or len(email) > 50:
        raise GoogleIdentityError("Google account details exceed supported length")
    return {"sub": sub, "email": email.lower(), "first_name": (claims.get("given_name") or claims.get("name") or "Google user")[:50], "last_name": (claims.get("family_name") or "")[:50]}


def sign_in_with_google(identity):
    user = User.query.filter_by(google_sub=identity["sub"]).first()
    if user:
        if str(user.is_active).lower() in ("false", "0", "inactive"):
            raise GoogleIdentityError("Account is inactive")
        return user
    if User.query.filter(func.lower(User.email) == identity["email"]).first():
        raise GoogleIdentityError("An account uses this email. Sign in with your password and link Google in account settings.")
    user = User(
        uuid=f"user::{uuid.uuid4()}",
        username=f"g_{uuid.uuid4().hex}",
        google_sub=identity["sub"],
        email=identity["email"],
        first_name=identity["first_name"],
        last_name=identity["last_name"],
        password=generate_password_hash(uuid.uuid4().hex + uuid.uuid4().hex),
        user_type=USER_TYPE.CUSTOMER.value,
        is_active="true",
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise GoogleIdentityError("Google sign-in could not be completed. Please try again.") from exc
    return user


def link_google(user, identity):
    existing = User.query.filter_by(google_sub=identity["sub"]).first()
    if existing and existing.id != user.id:
        raise GoogleIdentityError("This Google account is already linked")
    if user.google_sub and user.google_sub != identity["sub"]:
        raise GoogleIdentityError("This account already has a different Google sign-in")
    user.google_sub = identity["sub"]
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise GoogleIdentityError("This Google account is already linked") from exc
    return user
