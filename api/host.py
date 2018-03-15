from treadmill import authz


class API(object):
    """Treadmill Host REST API."""

    def __init__(self):

        def create_server():
            return ''

        def delete_server():
            return ''

        self.create_server = create_server
        self.delete_server = delete_server


def init(authorizer):
    """Returns module API wrapped with authorizer function."""
    api = API()
    return authz.wrap(api, authorizer)
