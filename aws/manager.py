from treadmill.aws.server.services import AWSClient
from treadmill.aws.server.services import IPAClient


class HostManager():
    def __init__(self):
        self.awsclient = AWSClient()
        self.ipaclient = IPAClient()

    def createHost(self, manifest):
        new_ipa_host = self.ipaclient.enroll_ipa_host(manifest['fqdn'])
        manifest['otp'] = new_ipa_host['result']['result']['randompassword']
        self.awsclient.create_instance(manifest)

    def deleteHost(self, hostname):
        self.ipaclient.unenroll_ipa_host(hostname)
        self.awsclient.delete_instance(hostname)
