import click

from srecli.group.platform_k8s import k8s


@click.group(name='platform')
def platform():
    """
    Manages Custodian Service platforms
    """


platform.add_command(k8s)
