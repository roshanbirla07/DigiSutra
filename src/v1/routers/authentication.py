from controllers.user import SignUp


class AuthenticationRoutes(object):

    @staticmethod
    def router():
        from v1.routers.routes import v1

        v1.add_url_rule('users/',
                        view_func=SignUp.as_view('signup'),
                        methods=['POST'],
                        endpoint='should_be_v1_only_signup'
                        )