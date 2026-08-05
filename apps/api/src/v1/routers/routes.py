from flask import Blueprint
from v1.routers.authentication import AuthenticationRoutes
from v1.routers.payouts import PayoutRoutes
from v1.routers.support import SupportRoutes

v1 = Blueprint('v1', __name__, url_prefix = '/v1/')

#routes for authentication
AuthenticationRoutes.router()
PayoutRoutes.router()
SupportRoutes.router()
