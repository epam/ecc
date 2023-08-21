import click

from c7ncli.group import ViewCommand, cli_response, ContextObj, customer_option


@click.group(name='rabbitmq')
def rabbitmq():
    """
    Manages Job submit action
    """


@rabbitmq.command(cls=ViewCommand, name='add')
@click.option('--maestro_user', '-mr', type=str, required=True,
              help='Maestro user')
@click.option('--rabbit_exchange', '-re', type=str,
              help='Rabbit exchange')
@click.option('--request_queue', '-req', type=str, required=True,
              help='Request queue')
@click.option('--response_queue', '-res', type=str, required=True,
              help='Response queue')
@click.option('--sdk_access_key', '-sak', type=str, required=True,
              help='SDK Access key')
@click.option('--connection_url', '-url', type=str, required=True,
              help='Rabbit connection url')
@click.option('--sdk_secret_key', '-ssk', type=str, required=True,
              help='SDK Secret key')
@customer_option
@cli_response(secured_params=['sdk_secret_key'])
def add(ctx: ContextObj, **kwargs):
    """
    Creates rabbitMQ configuration for your customer
    """
    kwargs['customer'] = kwargs.pop('customer_id', None)
    return ctx['api_client'].rabbitmq_post(**kwargs)


@rabbitmq.command(cls=ViewCommand, name='describe')
@customer_option
@cli_response()
def describe(ctx: ContextObj, **kwargs):
    """
    Describes rabbitMQ configuration for your customer
    """
    kwargs['customer'] = kwargs.pop('customer_id', None)
    return ctx['api_client'].rabbitmq_get(**kwargs)


@rabbitmq.command(cls=ViewCommand, name='delete')
@customer_option
@cli_response()
def delete(ctx: ContextObj, **kwargs):
    """
    Removes rabbitMQ configuration for your customer
    """
    kwargs['customer'] = kwargs.pop('customer_id', None)
    return ctx['api_client'].rabbitmq_delete(**kwargs)
