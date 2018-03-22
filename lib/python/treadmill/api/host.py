# from treadmill import authz
from treadmill.aws.manager import HostManager

class API(object):
    """Treadmill Host REST API."""

    def __init__(self, ):
        host_manager = HostManager()

        def list_servers(hostname=""):
            return host_manager.getHost(hostname)

        def create_server(name, domain, ami, subnet, proxy, secgroup, size="t2.micro", key="tm-internal", role="Node", count=1):
            host_manager.createHost(
                {'image_id': ami,
                 'count': count,
                 'instance_type': size,
                 'secgroup_ids': secgroup,
                 'fqdn': '{}.{}'.format(name, domain),
                 'cell': subnet,
                 'key': key,
                 'role': role,
                 'proxy': proxy
                 }
            )

        def delete_server(hostname):
            host_manager.deleteHost(hostname)

        self.list_servers = list_servers
        self.create_server = create_server
        self.delete_server = delete_server


def init(authorizer):
    """Returns module API wrapped with authorizer function."""
    api = API()
    #return authz.wrap(api, authorizer)
    return api