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
    @click.option('-d', '--domain', required=True,
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
    @click.option('--region', envvar='AWS_DEFAULT_REGION', help='AWS Region')
    @click.option('--subnet', required=True, envvar='TREADMILL_CELL', 
                  help='Subnet ID/Treadmill cell name')
    @click.option('--secgroup', help='Instance security group ID')
    @click.option('--ami', help='AMI image ID')
    @click.option('--key', default="tm-internal", help='Instance SSH key name')
    @click.option('--role', default="Node", help='Instance role')
    @click.option('--count', default=1, type=int, help='Number of instances')
    @click.option('--size', default='t2.micro', help='Instance EC2 size')
    @click.pass_context
    @cli.ON_CLI_EXCEPTIONS
    def create_host(ctx, region, subnet, secgroup,
                    ami, key, role, count, size):
        """Configure Treadmill Host"""
        domain = ctx.obj['DOMAIN']
        manager = ctx.obj['host_manager']

        if region:
            connection.Connection.context.region_name = region
        connection.Connection.context.domain = domain
        
        click.echo(pprint(manager.createHost({'subnet_id': subnet,
                                              'secgroup_ids': secgroup,
                                              'image_id': ami,
                                              'key': key,
                                              'role': role,
                                              'count': count,
                                              'instance_type': size,
                                              'domain': domain,
                                              })))
        

    @host.command(name='delete')
    @click.option('-h', '--hostnames', multiple=True,  required=True, 
                  help='Hostnames for removal')
    @click.option('-f', '--force', is_flag=True, help='Force removal')
    @click.pass_context
    @cli.ON_CLI_EXCEPTIONS
    def delete_host(ctx, hostnames, force):
        manager = ctx.obj['host_manager']
        
        if not force:
            click.confirm("Are you sure you want to terminate:\n{}\n"
                          .format(hostnames), abort=True
                          )
                          
        for hostname in hostnames:
            click.echo(manager.deleteHost(hostname))
            

    @host.command(name='list')
    @click.option('-p', '--pattern', help='Whole or partial hostname')
    @click.pass_context
    @cli.ON_CLI_EXCEPTIONS
    def get_host(ctx, pattern):
        manager = ctx.obj['host_manager']
        
        if pattern:
            click.echo(pprint(manager.findHost(pattern)))
        else:
            click.echo(pprint(manager.findHost()))

    return aws

