import click
from pprint import pprint
import logging

from treadmill.infra import connection
from treadmill.infra.utils import cli_callbacks
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
    @click.option('--name', required=True,
                  callback=cli_callbacks.validate_hostname, help='FQDN name')
    @click.option('--region', help='AWS Region')
    @click.option('--subnet', help='Subnet ID/Treadmill cell name')
    @click.option('--secgroup', help='Instance security group ID')
    @click.option('--ami', help='AMI image ID')
    @click.option('--key', default="tm-internal", help='Instance SSH key name')
    @click.option('--role', default="Node", help='Instance role')
    @click.option('--count', default=1, type=int, help='Number of instances')
    @click.option('--size', default='t2.micro', help='Instance EC2 size')
    @click.option('--proxy', help='TEMP configuration')
    @click.pass_context
    @cli.ON_CLI_EXCEPTIONS
    def create_host(ctx, name, region, subnet, secgroup,
                    ami, key, role, count, size, proxy):
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
             'secgroup_ids': secgroup,
             'fqdn': '{}.{}'.format(name, domain),
             'cell': subnet,
             'key': key,
             'role': role,
             'proxy': proxy
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
            click.confirm("Are you sure you want to terminate {}? [yes/NO]: "
                          .format(hostname), abort=True
                          )
        manager.deleteHost(hostname)

    @host.command(name='list')
    @click.option('--hostname', help='FQDN name')
    @click.pass_context
    @cli.ON_CLI_EXCEPTIONS
    def get_host(ctx, hostname):
        manager = ctx.obj['host_manager']
        if hostname:
            click.echo(pprint(manager.findHost(hostname)))
        else:
            click.echo(pprint(manager.findHost()))

    return aws
