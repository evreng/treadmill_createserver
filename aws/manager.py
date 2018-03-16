import logging
from treadmill.aws.server.services import AWSClient
from treadmill.aws.server.services import IPAClient
_LOGGER = logging.getLogger(__name__)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(message)s"))
_LOGGER.addHandler(console_handler)

class HostManager():
    def __init__(self):
        self.awsclient = AWSClient()
        self.ipaclient = IPAClient()
        
    def createHost(self, manifest):
        from pprint import pprint
        new_ipa_host = self.ipaclient.enroll_ipa_host(manifest['fqdn'])
        _LOGGER.info('Debugging: new IPA host: {}'.format(pprint(new_ipa_host)))
        manifest['otp'] = new_ipa_host['result']['result']['randompassword']
        new_aws_host = self.awsclient.create_instance(manifest)
        _LOGGER.info('Debugging: new AWS instance: {}'.format(pprint(new_aws_host)))

    def deleteHost(self, hostname):
        self.ipaclient.unenroll_ipa_host(hostname)
        self.awsclient.delete_instance(hostname)

if __name__ == '__main__':
    manifest = {'image_id': 'ami-c96175b3',
                'count': 1,
                'instance_type': 't2.micro',
                'subnet_id': 'subnet-8f465dd5',
                'secgroup_ids': 'sg-b233a0c0',
                'fqdn': 'host12.mstreadmill.com',
                'domain': 'mstreadmill.com',
                'realm': 'MSTREADMILL.COM',
                'key': 'tm-internal'
                }
    client = HostManager()
    client.createHost(manifest)
    client.deleteHost(manifest['fqdn'])
