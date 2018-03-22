from treadmill.aws.server.services import AWSClient
from treadmill.aws.server.services import IPAClient
from time import time


class HostManager():
    def __init__(self):
        self.awsclient = AWSClient()
        self.ipaclient = IPAClient()

    def generate_hostname(self, manifest):
        timestamp = str(time()).replace('.', '')
        return 'tm{}-{}.{}'.format(manifest['role'].lower(), 
                                   timestamp, 
                                   manifest['domain'])

    def createHost(self, manifest):
        for host in range(manifest['count']):
            manifest['hostname'] = self.generate_hostname(manifest)
            ipa_host = self.ipaclient.enroll_ipa_host(manifest['hostname'])
            
            manifest['otp'] = ipa_host['result']['result']['randompassword']
            
            self.awsclient.create_instance(manifest)
            print(manifest['hostname'])
            
    def deleteHost(self, hostname):
        self.ipaclient.unenroll_ipa_host(hostname)
        self.awsclient.delete_instance(hostname)

    def findHost(self, pattern=''):
        return self.ipaclient.get_ipa_hosts(pattern)

