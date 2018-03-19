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

if __name__ == '__main__':
    client = HostManager()
    manifest = {'image_id': 'ami-c96175b3',
                'count': 1,
                'instance_type': 't2.micro',
                'secgroup_ids': 'sg-b233a0c0',
                'fqdn': 'host01.mstreadmill.com',
                'cell': 'subnet-8f465dd5',
                'key': 'tm-internal',
                'role': 'Node'
                }
    client.createHost(manifest)
    client.deleteHost(manifest['fqdn'])
