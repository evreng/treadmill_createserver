from os import environ
from random import choice
import logging
import dns.resolver
import requests
from requests_kerberos import HTTPKerberosAuth
from treadmill.infra import connection

_LOGGER = logging.getLogger(__name__)
_KERBEROS_AUTH = HTTPKerberosAuth()

API_VERSION = '2.28'


class IPAClient():
    ''' Interfaces with freeIPA API to register and deregister hosts '''

    def __init__(self):
        self.cell_name = environ.get('TREADMILL_CELL')
        self.domain = environ.get('TREADMILL_DNS_DOMAIN')
        self.ipa_cert_location = '/etc/ipa/ca.crt'

        # Strip trailing period as it breaks SSL
        self.ipa_server_hostn = self.get_ipa_server_from_dns(self.domain)[:-1]
        self.ipa_srv_address = 'https://{}/ipa'.format(self.ipa_server_hostn)
        self.ipa_srv_api_address = '{}/session/json'.format(
            self.ipa_srv_address)
        self.referer = {'referer': self.ipa_srv_address}

    def get_ipa_server_from_dns(self, tm_dns_domain):
        ''' Looks up random IPA server from DNS SRV records '''
        raw_results = [
            result.to_text() for result in
            dns.resolver.query('_kerberos._tcp.{}'.format(tm_dns_domain),
                               'SRV')
            ]
        return choice(raw_results).split()[-1]

    def _post(self, payload=None, auth=_KERBEROS_AUTH):
        ''' Submits formatted JSON to IPA server.
            Uses requests_kerberos module for Kerberos authentication with IPA.
        '''
        response = requests.post(self.ipa_srv_api_address,
                                 json=payload,
                                 auth=auth,
                                 headers=self.referer,
                                 verify=self.ipa_cert_location)
        return response

    def enroll_ipa_host(self, hostname):
        ''' Register new host with IPA server '''
        payload = {'method': 'host_add',
                   'params': [[hostname],
                              {'force': True,
                               'random': True,
                               'version': API_VERSION,
                               }
                              ],
                   'id': 0}
        r = self._post(payload)
        if r.json()['error']:
            raise KeyError(r.json()['error']['message'])
        return r.json()

    def unenroll_ipa_host(self, hostname):
        ''' Unregister host from IPA server '''
        payload = {'method': 'host_del',
                   'params': [[hostname],
                              {'updatedns': True,
                               'version': API_VERSION
                               }
                              ],
                   'id': 0}
        r = self._post(payload)
        if r.json()['error']:
            raise KeyError(r.json()['error']['message'])
        return r.json()

    def get_ipa_hosts(self, hostname=''):
        ''' Retrieve host records from IPA server '''
        payload = {'method': 'host_find',
                   'params': [[hostname],
                              {'version': API_VERSION}
                              ],
                   'id': 0}
        r = self._post(payload)
        if r.json()['error']:
            raise KeyError(r.json()['error']['message'])
        return r.json()


class AWSClient():
    ''' Interfaces with TM AWS connection '''

    def __init__(self):
        self.ec2_conn = connection.Connection()

    def sanitize_manifest(self, manifest):
        ''' Standardize manifest variables '''
        if manifest['fqdn']:
            manifest['fqdn'] = manifest['fqdn'].lower()

        if manifest['role']:
            manifest['role'] = manifest['role'].upper()

        return manifest

    def build_tags(self, manifest):
        ''' Create list of AWS tags from manifest '''
        tags = [{'Key': 'Name', 'Value': manifest['fqdn']},
                {'Key': 'Role', 'Value': manifest['role']},
                ]
        return [{'ResourceType': 'instance', 'Tags': tags}]

    def create_instance(self, manifest):
        ''' Add new instance to AWS using properties from manifest '''
        manifest = self.sanitize_manifest(manifest)
        tags = self.build_tags(manifest)
        user_data = self.render_manifest(manifest)

        self.ec2_conn.run_instances(
            TagSpecifications=tags,
            ImageId=manifest['image_id'],
            MinCount=manifest['count'],
            MaxCount=manifest['count'],
            InstanceType=manifest['instance_type'],
            KeyName=manifest['key'],
            UserData=user_data,
            NetworkInterfaces=[{
                'DeviceIndex': 0,
                'SubnetId': manifest['subnet_id'],
                'Groups': [manifest['secgroup_ids']]
            }],
        )

    def delete_instance(self, hostname):
        ''' Delete instances matching hostname from AWS '''
        instances = self.get_instances_by_hostname(hostname)

        for instance in instances:
            self.ec2_conn.terminate_instances(
                InstanceIds=[instance['InstanceId']],
                DryRun=False
                )

    def get_instances_by_hostname(self, hostname):
        ''' Returns list of AWS instances that match hostname
            AWS returns instances in nested list- flatten to simple list
        '''
        filters = [{'Name': 'tag:Name', 'Values': [hostname]},
                   {'Name': 'instance-state-name', 'Values': ['running']},
                   ]
        reservations = [
            x['Instances'] for x in
            self.ec2_conn.describe_instances(Filters=filters)['Reservations']
            ]
        return [result
                for reservation in reservations
                for result in reservation]

    def render_manifest(self, manifest):
        ''' Stub function to supply instance user_data during testing.
        '''
        template = '''#!/bin/bash
        hostnamectl set-hostname {fqdn}
        echo "export http_proxy=http://proxy.ms-aws-dev.ms.com:3128/" \
            >> /etc/profile.d/http_proxy.sh
        echo "export NO_PROXY=localhost,169.254.169.254,*.ms-aws-dev.ms.com" \
            >> /etc/profile.d/http_proxy.sh
        echo "proxy=http://proxy.ms-aws-dev.ms.com:3128" >> /etc/yum.conf
        yum install -y ipa-client
        ipa-client-install \
        --no-krb5-offline-password \
        --enable-dns-updates \
        --password='{otp}' \
        --mkhomedir \
        --no-ntp \
        --unattended'''.format(fqdn=manifest['fqdn'],
                               otp=manifest['otp'],
                               )
        return template
