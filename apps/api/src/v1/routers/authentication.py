from controllers.user import SignUp, Login, UserList
from v1.routers.products import ProductRoutes


class AuthenticationRoutes(object):

    @staticmethod
    def router():
        from v1.routers.routes import v1

        v1.add_url_rule('users/',
                        view_func=SignUp.as_view('signup'),
                        methods=['POST'],
                        endpoint='should_be_v1_only_signup'
                        )
        v1.add_url_rule('users/login/',
                        view_func=Login.as_view('login'),
                        methods=['POST'],
                        endpoint='should_be_v1_only_login'
                        )
        v1.add_url_rule('users/',
                        view_func=UserList.as_view('user_list'),
                        methods=['GET'],
                        endpoint='should_be_v1_only_user_list'
                        )
        ProductRoutes.router()
