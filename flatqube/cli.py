# -*- coding: utf-8 -*-

from typing import Optional, Literal, cast
from decimal import Decimal
import time
import sys

import click
from rich import print as rich_print
from rich.table import Table

from .config import config, add_currency_to_config, config_paths, add_currency_list_to_config
from .constants import CLI_NAME
from .client import FlatQubeClient, CurrencySortBy, SortOrder
from .models import CurrencyInfo
from .utils import quantize_value, humanize_value, styled_text
from .version import __version__


cli_cfg = config.cli
cli_styles = config.cli_styles
tb_ch = config.cli_table.border

sort_options = tuple(item.value for item in CurrencySortBy)  # noqa
sort_orders = tuple(item.value for item in SortOrder)  # noqa


def print_currencies_info(currencies_info: list[CurrencyInfo],
                          sort: CurrencySortBy,
                          sort_order: SortOrder,
                          show_trans_count: bool):

    def quantize_value_change(value_change: Decimal) -> Decimal:
        return quantize_value(value_change,
                              decimal_digits=config.quantize.value_change_decimal_digits,
                              normalize=config.quantize.value_change_normalize)

    usd_prefix = '$'
    pct_suffix = '%'

    name_title = 'Name'
    price_title = 'Price'
    price_change_title = pct_suffix
    tvl_title = 'TVL'
    tvl_change_title = pct_suffix
    vol_24h_title = '24h Volume'
    vol_24h_change_title = pct_suffix
    vol_7d_title = '7d Volume'
    trans_24h_title = '24h Tr-s'

    if len(currencies_info) > 1:
        if sort_order == SortOrder.ascend:
            sort_indicator = config.cli_table.sort_ascend
        else:
            sort_indicator = config.cli_table.sort_descend
    else:
        sort_indicator = ''

    def add_sort_indicator(title):
        return f'{sort_indicator} {title.strip()}'

    if sort == CurrencySortBy.price:
        price_title = add_sort_indicator(price_title)
    elif sort == CurrencySortBy.price_change:
        price_change_title = add_sort_indicator(price_change_title)
    elif sort == CurrencySortBy.tvl:
        tvl_title = add_sort_indicator(tvl_title)
    elif sort == CurrencySortBy.tvl_change:
        tvl_change_title = add_sort_indicator(tvl_change_title)
    elif sort == CurrencySortBy.volume_24h:
        vol_24h_title = add_sort_indicator(vol_24h_title)
    elif sort == CurrencySortBy.volume_change_24h:
        vol_24h_change_title = add_sort_indicator(vol_24h_change_title)
    elif sort == CurrencySortBy.volume_7d:
        vol_7d_title = add_sort_indicator(vol_7d_title)
    elif sort == CurrencySortBy.transaction_count_24h:
        trans_24h_title = add_sort_indicator(trans_24h_title)

    def indent_text(title: str, indent: int = 1):
        indent_s = ' ' * indent
        return f'{indent_s}{title}'

    currencies_table = Table.grid()

    currencies_table.show_header = True
    currencies_table.header_style = cli_styles.table

    indent_border = indent_text(tb_ch)
    justify = cast(Literal, 'right')

    currencies_table.add_column(header=indent_text(name_title), justify=justify)
    currencies_table.add_column(header=indent_border, justify=justify)
    currencies_table.add_column(header=indent_text(price_title), justify=justify)
    currencies_table.add_column(header=price_change_title, justify=justify)
    currencies_table.add_column(header=indent_border, justify=justify)
    currencies_table.add_column(header=indent_text(tvl_title), justify=justify)
    currencies_table.add_column(header=tvl_change_title, justify=justify)
    currencies_table.add_column(header=indent_border, justify=justify)
    currencies_table.add_column(header=indent_text(vol_24h_title), justify=justify)
    currencies_table.add_column(header=vol_24h_change_title, justify=justify)
    currencies_table.add_column(header=indent_border, justify=justify)
    currencies_table.add_column(header=indent_text(vol_7d_title), justify=justify)

    if show_trans_count:
        currencies_table.add_column(header=indent_border, justify=justify)
        currencies_table.add_column(header=indent_text(trans_24h_title), justify=justify)

    def format_value(value, prefix=usd_prefix, style=cli_styles.value):
        if isinstance(value, Decimal):
            value = quantize_value(value)
        else:
            value = quantize_value(Decimal(value), decimal_digits=0, normalize=True)
        value = humanize_value(value)
        value = f'{prefix}{value}'
        return styled_text(indent_text(value), style)

    def format_value_change(value_change, suffix=pct_suffix):
        qh_value_change = humanize_value(quantize_value_change(value_change))
        prefix = ''
        if value_change == 0:
            style = cli_styles.value_change_zero
        elif value_change > 0:
            prefix = '+'
            style = cli_styles.value_change_plus
        else:
            style = cli_styles.value_change_minus

        value = f'{prefix}{qh_value_change}{suffix}'
        return styled_text(indent_text(value, indent=2), style)

    border = styled_text(indent_border, cli_styles.table)

    for currency_info in currencies_info:
        currency_row = (
            styled_text(indent_text(currency_info.name), cli_styles.name),
            border,
            format_value(currency_info.price),
            format_value_change(currency_info.price_change),
            border,
            format_value(currency_info.tvl),
            format_value_change(currency_info.tvl_change),
            border,
            format_value(currency_info.volume_24h),
            format_value_change(currency_info.volume_change_24h),
            border,
            format_value(currency_info.volume_7d),
        )

        if show_trans_count:
            currency_row += (
                border,
                format_value(currency_info.transaction_count_24h, prefix=''),
            )

        currencies_table.add_row(*currency_row)

    rich_print(currencies_table)


def fail(ctx: click.Context, message: str, err: Optional[Exception] = None):
    """Print an error message and exit
    """

    message = f'{message}: {err}' if err else message
    styled_message = click.style(message, fg=cli_styles.error.fg, bold=cli_styles.error.bold)

    ctx.fail(styled_message)


def warn(message: str):
    styled_message = click.style(message, fg=cli_styles.warning.fg, bold=cli_styles.warning.bold)
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

    add_currency_list_to_config('_whitelist', currencies)

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
        currencies = config.currencies['_whitelist']

    title_name = 'Name'
    title_address = 'Address'

    if currencies:
        names, addresses = zip(*currencies.items())
    else:
        names = ()
        addresses = ()

    name_max_len = max(len(name) for name in names + (title_name,))

    s = click.style(f' {title_name:>{name_max_len}} {tb_ch} {title_address}\n',
                    fg=cli_styles.table.fg, bold=cli_styles.table.bold)

    for name, address in zip(names, addresses):
        s += click.style(f' {name:>{name_max_len}} ', fg=cli_styles.name.fg, bold=cli_styles.name.bold)
        s += click.style(f'{tb_ch} ', fg=cli_styles.table.fg, bold=cli_styles.table.bold)
        s += click.style(f'{address}\n', fg=cli_styles.value.fg, bold=cli_styles.value.bold)

    click.echo(s, nl=False)


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

    name = click.style(f'{currency_info.name}', fg=cli_styles.name.fg, bold=cli_styles.name.bold)
    address = click.style(f'{currency_info.address}', fg=cli_styles.address.fg, bold=cli_styles.address.bold)

    if list_name:
        list_name_s = click.style(f'{list_name}', fg=cli_styles.name.fg, bold=cli_styles.name.bold)
        click.echo(f"{name} {address} was added to '{list_name_s}' list to the user config")
    else:
        click.echo(f"{name} {address} was added to the user config")


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
@click.option('-u', '--update', is_flag=True, default=False, show_default=True, help='Auto update data')
@click.option('-i', '--update-interval', type=float, default=cli_cfg.currency.show.update_interval, show_default=True,
              help='Auto update interval in seconds')
@click.pass_context
def show(ctx: click.Context,
         currency_names: tuple[str],
         currency_lists: Optional[tuple[str]],
         sort: str, sort_order: str,
         show_trans_count: bool,
         update: bool, update_interval: float):
    """Show currencies info
    """

    sort = CurrencySortBy(sort)
    sort_order = SortOrder(sort_order)

    client: FlatQubeClient = ctx.obj['client']

    if not config.currencies['_whitelist']:
        try:
            currencies = {
                cr.name.upper(): cr.address for cr in client.whitelist_currencies()
            }
        except Exception as err:
            fail(ctx, f"Failed to get whitelist currencies", err=err)
            return
        add_currency_list_to_config('_whitelist', currencies)

    if not currency_names and not currency_lists:
        currency_lists = [cli_cfg.currency.show.default_list]

    currency_addresses = []

    if currency_names:
        whitelist = config.currencies['_whitelist']
        default = config.currencies['_default']

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
        for _ in range(lines):
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")

        try:
            currencies_info = client.currencies(currency_addresses, sort_by=sort, sort_order=sort_order)
        except Exception as err:
            fail(ctx, f"Failed to get currencies info", err=err)
            return

        print_currencies_info(currencies_info, sort, sort_order, show_trans_count)

        if not update:
            break

        time.sleep(update_interval)
        lines = len(currencies_info) + 1
