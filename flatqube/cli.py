# -*- coding: utf-8 -*-

from typing import Optional
import sys
import time

import click

from .client import CurrencySortBy, FlatQubeClient, SortOrder
from .config import DEFAULT_LIST, WHITE_LIST, add_currency_list_to_config, add_currency_to_config, config, config_paths
from .constants import CLI_NAME
from .fmt import print_config_currencies, print_currencies_info, styled_text
from .version import __version__


cli_cfg = config.cli
cli_styles = config.console.styles
tb_ch = config.console.table.border

sort_options = tuple(item.value for item in CurrencySortBy)  # noqa
sort_orders = tuple(item.value for item in SortOrder)  # noqa


def fail(ctx: click.Context, message: str, err: Optional[Exception] = None):
    """Print an error message and exit
    """

    message = f'{message}: {err}' if err else message
    styled_message = styled_text(message, cli_styles.error, rendered=True)

    ctx.fail(styled_message)


def warn(message: str):
    """Print a warning message
    """

    styled_message = styled_text(message, cli_styles.warning, rendered=True)
    click.echo(styled_message)


@click.group(name=CLI_NAME)
@click.version_option(version=__version__, prog_name=CLI_NAME)
@click.pass_context
def cli(ctx: click.Context):
    """FlatQube client CLI tool
    """

    ctx.ensure_object(dict)
    ctx.obj['client'] = FlatQubeClient()


config_help = f"""
Configuration and setting management

The user config file is here:

{config_paths.user_path}
"""


@cli.group(name='config', help=config_help)
def cli_config():
    pass


@cli_config.group(name='currency')
def currency_config():
    """Currency info config
    """


@currency_config.command()
@click.pass_context
def update_whitelist(ctx: click.Context):
    """Update Broxus whitelist currencies in the config
    """

    client: FlatQubeClient = ctx.obj['client']

    try:
        currencies = {
            cr.name.upper(): cr.address for cr in client.whitelist_currencies()
        }
    except Exception as err:
        fail(ctx, f"Failed to get whitelist currencies", err=err)
        return

    add_currency_list_to_config(WHITE_LIST, currencies)

    click.echo(f'The whitelist was updated with {len(currencies)} currencies')


@currency_config.command(name='show')
@click.option('-l', '--list', 'currency_list', help='Show tokens from the given list')
@click.pass_context
def show_currencies(ctx: click.Context, currency_list: str):
    """Show currencies in the config or given list
    """

    if currency_list:
        if currency_list not in config.currencies:
            fail(ctx, f"'{currency_list}' does not exist.")
        currencies = {name: address for name, address in config.currencies[currency_list].items()}
    else:
        currencies = config.currencies[WHITE_LIST]

    if not currencies:
        warn("There is nothing to show.")
        return

    print_config_currencies(currencies)


@currency_config.command()
def lists():
    """Show all currency lists in the config
    """

    s = ''
    for currency_list in config.currencies:
        if not currency_list.startswith('_'):
            s += f'{currency_list}\n'

    click.echo(s, nl=False)


@currency_config.command(name='add')
@click.argument('address')
@click.option('-l', '--list', 'list_name', default=None, help='The list name to add currency')
@click.pass_context
def add_currency(ctx: click.Context, address: str, list_name: Optional[str]):
    """Add a new currency by the contract address to the config
    """

    client: FlatQubeClient = ctx.obj['client']

    try:
        currency_info = client.currency(address)
    except Exception as err:
        fail(ctx, 'Cannot get currency by address', err=err)
        return

    if list_name and list_name.startswith('_'):
        fail(ctx, f"Invalid list name: '{list_name}'. It is not allowed to start a list name with underscore.")

    add_currency_to_config(currency_info.name, currency_info.address, list_name)

    name = styled_text(currency_info.name, cli_styles.name, rendered=True)
    address = styled_text(currency_info.address, cli_styles.address, rendered=True)

    if list_name:
        list_name_s = styled_text(list_name, cli_styles.name, rendered=True)
        click.echo(f"Currency {address} ({name}) was added to '{list_name_s}' list to the user config")
    else:
        click.echo(f"Currency {address} ({name}) was added to the user config")


@cli.group()
def currency():
    """FlatQube currencies (tokens) info

    The CLI shows currency prices, price changes, TVL, volume and more info.
    """


@currency.command()
@click.argument('currency_names', nargs=-1)
@click.option('-l', '--list', 'currency_lists', default=(), multiple=True,
              help="The list(s) of tokens to show from the config")
@click.option('-s', '--sort', type=click.Choice(sort_options), default=cli_cfg.currency.show.sort,
              show_default=True, help="Sort displayed currencies")
@click.option('-o', '--sort-order', type=click.Choice(sort_orders), default=cli_cfg.currency.show.sort_order,
              show_default=True, help='Sort order')
@click.option('-t', '--show-trans-count', is_flag=True, default=False, help='Show 24h transaction count')
@click.option('-f', '--show-fee', is_flag=True, default=False, help='Show 24h fee')
@click.option('-u', '--update', is_flag=True, default=False, show_default=True, help='Auto update data')
@click.option('-i', '--update-interval', type=float, default=cli_cfg.currency.show.update_interval, show_default=True,
              help='Auto update interval in seconds')
@click.pass_context
def show(ctx: click.Context,
         currency_names: tuple[str],
         currency_lists: Optional[tuple[str]],
         sort: str, sort_order: str,
         show_trans_count: bool,
         show_fee: bool,
         update: bool,
         update_interval: float):
    """Show currencies info
    """

    sort = CurrencySortBy(sort)
    sort_order = SortOrder(sort_order)

    client: FlatQubeClient = ctx.obj['client']

    if not config.currencies[WHITE_LIST]:
        try:
            currencies = {
                cr.name.upper(): cr.address for cr in client.whitelist_currencies()
            }
        except Exception as err:
            fail(ctx, f"Failed to get whitelist currencies", err=err)
            return
        add_currency_list_to_config(WHITE_LIST, currencies)

    if not currency_names and not currency_lists:
        currency_lists = [cli_cfg.currency.show.default_list]

    currency_addresses = []

    if currency_names:
        whitelist = config.currencies[WHITE_LIST]
        default = config.currencies[DEFAULT_LIST]

        for name in currency_names:
            name = name.upper()

            if name in whitelist:
                currency_addresses.append(whitelist[name])
            elif name in default:
                currency_addresses.append(default[name])
            else:
                warn(f"'{name}' currency name does not exist in white list and default list in the config.")

    for currency_list in currency_lists:
        if currency_list.startswith('_') or currency_list not in config.currencies:
            warn(f"'{currency_list}' currency list does not exist in the config.")
            continue

        list_currencies = config.currencies[currency_list]
        currency_addresses.extend(list_currencies.values())

    currency_addresses = set(currency_addresses)

    if not currency_addresses:
        warn('There is nothing to show.')
        return

    lines = 0

    while True:
        # Clear previous currency info in auto-update mode
        for _ in range(lines):
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")

        try:
            currencies_info = client.currencies(currency_addresses, sort_by=sort, sort_order=sort_order)
        except Exception as err:
            fail(ctx, f"Failed to get currencies info", err=err)
            return

        print_currencies_info(currencies_info, sort, sort_order, show_trans_count, show_fee)

        if not update:
            break

        time.sleep(update_interval)
        lines = len(currencies_info) + 1
