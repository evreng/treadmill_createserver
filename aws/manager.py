import logging
from treadmill.aws.server.services import AWSClient
from treadmill.aws.server.services import IPAClient
_LOGGER = logging.getLogger(__name__)


class HostManager():
    def __init__(self):
        self.awsclient = AWSClient()
        self.ipaclient = IPAClient()

    def createHost(self, hostname, manifest):
        instance = self.awsclient.create_instance(hostname,
                                                  manifest)
        self.ipaclient.enroll_ipa_host(hostname,
                                       instance['ip_address'])

    def deleteHost(self, hostname):
        self.ipaclient.unenroll_ipa_host(hostname)
        self.awsclient.delete_instance(hostname)
