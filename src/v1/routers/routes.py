from flask import Blueprint
from v1.routers.authentication import AuthenticationRoutes

v1 = Blueprint('v1', __name__, url_prefix = '/v1/')

#routes for authentication
AuthenticationRoutes.router()