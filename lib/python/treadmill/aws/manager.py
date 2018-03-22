from treadmill.aws.server.services import AWSClient
from treadmill.aws.server.services import IPAClient
from time import time


class HostManager():
    def __init__(self):
        self.awsclient = AWSClient()
        self.ipaclient = IPAClient()

    def generate_hostname(self, manifest):
        ''' Generates hostname from manifest role, domain and timestamp. '''
        timestamp = str(time()).replace('.', '')
        return 'tm{}-{}.{}'.format(manifest['role'].lower(),
                                   timestamp,
                                   manifest['domain'])

    def createHost(self, manifest):
        ''' Adds host defined in manifest to IPA, then adds the OTP from the
            IPA reply to the manifest and creates instance in AWS.
        '''
        hosts = []

        for host in range(manifest['count']):
            manifest['hostname'] = self.generate_hostname(manifest)
            ipa_host = self.ipaclient.enroll_ipa_host(manifest['hostname'])

            manifest['otp'] = ipa_host['result']['result']['randompassword']
            self.awsclient.create_instance(manifest)
            hosts.append(manifest['hostname'])

        return hosts

    def deleteHost(self, hostname):
        ''' Unenrolls host from IPA and AWS '''
        self.ipaclient.unenroll_ipa_host(hostname)
        self.awsclient.delete_instance(hostname)
        return hostname

    def findHost(self, pattern=''):
        ''' Returns list of matching hosts from IPA.
            If pattern is null, returns all hosts.
        '''
        return self.ipaclient.get_ipa_hosts(pattern)

