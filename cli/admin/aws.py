import os
import click
from pprint import pprint
import logging

from treadmill.infra import connection
from treadmill.infra.utils import cli_callbacks
from treadmill.infra.utils import security_group
from treadmill import cli
from treadmill.aws.manager import HostManager


_LOGGER = logging.getLogger(__name__)
_OPTIONS_FILE = 'manifest'


def init():
    """AWS CLI module"""

    @click.group()
    @click.option('--domain', required=True,
                  envvar='TREADMILL_DNS_DOMAIN',
                  callback=cli_callbacks.validate_domain,
                  help='Domain for hosted zone')
    @click.pass_context
    def aws(ctx, domain):
        """Manage AWS instances"""
        ctx.obj['DOMAIN'] = domain
        ctx.obj['host_manager'] = HostManager()

    @aws.group()
    @click.pass_context
    def host(ctx):
        """Configure EC2 Objects"""

    @host.command(name='create')
    @click.option('--name', required=True, help='FQDN name', callback=cli_callbacks.validate_hostname)
    @click.option('--region', help='Region for the instance')
    @click.option('--subnet', help='instance subnet-id')
    @click.option('--security-group', help='instance security group')
    @click.option('--ami', help='instance ami-id')
    @click.option('--key', default="tm-internal", help='instance SSH key name')
    @click.option('--role', default="Node", help='instance role name')
    @click.option('--count', default=1, type=int, help='number of instances')
    @click.option('--size', default='t2.micro', help='instance type')
    @click.pass_context
    @cli.ON_CLI_EXCEPTIONS
    def create_host(ctx, name, region, subnet, ami, key, role, count, size):
        """Configure Treadmill Host"""
        domain = ctx.obj['DOMAIN']
        manager = ctx.obj['host_manager']

        if region:
            connection.Connection.context.region_name = region

        connection.Connection.context.domain = domain

        manager.createHost(
            {'image_id': ami,
            'count': count,
            'instance_type': size,
            'secgroup_ids': security_group,
            'fqdn': '{}.{}'.format(name, domain),
            'cell': subnet,
            'key': key,
            'role': role
            }
        )

    @host.command(name='delete')
    @click.option('--hostname', required=True, help='FQDN name')
    @click.option('--force', is_flag=True, help='remove without safety prompt')
    @click.pass_context
    @cli.ON_CLI_EXCEPTIONS
    def delete_host(ctx, hostname, force):
        manager = ctx.obj['host_manager']
        if not force:
            click.confirm("Are you sure you want to terminate {}? [yes/NO]: ".format(hostname), abort=True)
        manager.deleteHost(hostname)


    @host.command(name='list')
    @click.option('--hostname', required=True, help='FQDN name')
    @click.pass_context
    @cli.ON_CLI_EXCEPTIONS
    def get_host(ctx, hostname):
        manager = ctx.obj['host_manager']
        click.echo(
            pprint(manager.awsclient.get_instances_by_hostname(hostname))
        )


    return aws
