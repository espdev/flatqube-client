# -*- coding: utf-8 -*-

from typing import Optional
from decimal import Decimal
import time
import sys

import click

from .config import config, add_currency_to_config
from .constants import CLI_NAME
from .client import FlatQubeClient, CurrencySortOptions, CurrencySortOrders
from .models import CurrencyInfo
from .utils import quantize_value, humanize_value, len_decimal
from .version import __version__


cli_cfg = config.cli
cli_colors = config.cli_colors

sort_options = tuple(item.value for item in CurrencySortOptions)  # noqa
sort_orders = tuple(item.value for item in CurrencySortOrders)  # noqa


def format_value(title: str,
                 value_max_len: int, value: Decimal,
                 value_change_max_len: Optional[int] = None,
                 value_change: Optional[Decimal] = None) -> tuple[str, int]:

    value_h = f'${humanize_value(value)}'
    vs = f' {value_h:>{value_max_len+1}} '
    value_len = len(vs)

    s = click.style(vs, fg=cli_colors.value.fg, bold=cli_colors.value.bold)

    if value_change_max_len is not None and value_change is not None:
        if value_change.is_zero():
            value_change_sign, value_change_color, value_change_bold = (
                ' ', cli_colors.value_change_zero.fg, cli_colors.value_change_zero.bold
            )
        elif value_change.is_signed():
            value_change_sign, value_change_color, value_change_bold = (
                '', cli_colors.value_change_minus.fg, cli_colors.value_change_minus.bold
            )
        else:
            value_change_sign, value_change_color, value_change_bold = (
                '+', cli_colors.value_change_plus.fg, cli_colors.value_change_plus.bold
            )

        value_change_h = f'{value_change_sign}{humanize_value(value_change)}'
        vs = f' {value_change_h:>{value_change_max_len}}% '
        value_len += len(vs)

        s += click.style(vs, fg=value_change_color, bold=value_change_bold)

    title_len = len(title)

    if value_len < title_len:
        indent_sz = title_len - value_len + 1
        s = ' ' * indent_sz + s
        value_len += indent_sz

    s = click.style(f'│', fg=cli_colors.table.fg, bold=cli_colors.table.bold) + s

    return s, value_len - 1


def print_currencies_info(currencies_info: list[CurrencyInfo],
                          sort: CurrencySortOptions, sort_order: CurrencySortOrders):

    def quantize_value_change(value_change: Decimal) -> Decimal:
        return quantize_value(value_change,
                              decimal_digits=config.quantize.value_change_decimal_digits,
                              normalize=config.quantize.value_change_normalize)

    def max_lens(values: list[tuple[Decimal, Decimal]]) -> tuple[int, int]:
        value_max_len = max(len_decimal(value) for value, _ in values)
        value_change_max_len = max(len_decimal(value_change, plus=True) for _, value_change in values)
        return value_max_len, value_change_max_len

    names = []
    price_values = []
    tvl_values = []
    volume_24h_values = []
    volume_7d_values = []

    for currency_info in currencies_info:
        names.append(currency_info.name)

        price_values.append((
            quantize_value(currency_info.price),
            quantize_value_change(currency_info.price_change),
        ))

        tvl_values.append((
            quantize_value(currency_info.tvl),
            quantize_value_change(currency_info.tvl_change),
        ))

        volume_24h_values.append((
            quantize_value(currency_info.volume_24h),
            quantize_value_change(currency_info.volume_change_24h),
        ))

        volume_7d_values.append(
            quantize_value(currency_info.volume_7d),
        )

    if len(currencies_info) > 1:
        sort_indicator = ' ▴' if sort_order == CurrencySortOrders.ascend else ' ▾'
        change_sort_indicator = '%'
    else:
        sort_indicator = ''
        change_sort_indicator = ''

    if sort == CurrencySortOptions.price:
        price_sort_indicator = sort_indicator
    elif sort == CurrencySortOptions.price_change:
        price_sort_indicator = sort_indicator + change_sort_indicator
    else:
        price_sort_indicator = ''

    if sort == CurrencySortOptions.tvl:
        tvl_sort_indicator = sort_indicator
    elif sort == CurrencySortOptions.tvl_change:
        tvl_sort_indicator = sort_indicator + change_sort_indicator
    else:
        tvl_sort_indicator = ''

    if sort == CurrencySortOptions.volume24h:
        volume_24h_sort_indicator = sort_indicator
    elif sort == CurrencySortOptions.volume24h_change:
        volume_24h_sort_indicator = sort_indicator + change_sort_indicator
    else:
        volume_24h_sort_indicator = ''

    volume_7d_sort_indicator = sort_indicator if sort == CurrencySortOptions.volume7d else ''

    name_title = 'Name'
    price_title = ' Price' + price_sort_indicator
    tvl_title = ' TVL' + tvl_sort_indicator
    vol_24h_title = ' 24h Volume' + volume_24h_sort_indicator
    vol_7d_title = ' 7d Volume' + volume_7d_sort_indicator

    name_max_len = max(len(name) for name in names + [name_title])
    price_max_len, price_change_max_len = max_lens(price_values)
    tvl_max_len, tvl_change_max_len = max_lens(tvl_values)
    vol_24h_max_len, vol_24h_change_max_len = max_lens(volume_24h_values)
    vol_7d_max_len = max(len_decimal(volume_7d) for volume_7d in volume_7d_values)

    s = ''
    price_sl = 0
    tvl_sl = 0
    vol_24h_sl = 0
    vol_7d_sl = 0

    for name, (price, price_change), (tvl, tvl_change), (vol_24h, vol_24h_change), vol_7d in \
            zip(names, price_values, tvl_values, volume_24h_values, volume_7d_values):

        name_s = click.style(f'{name:>{name_max_len}} ', fg=cli_colors.name.fg, bold=cli_colors.name.bold)

        price_s, price_sl = format_value(price_title, price_max_len, price, price_change_max_len, price_change)
        tvl_s, tvl_sl = format_value(tvl_title, tvl_max_len, tvl, tvl_change_max_len, tvl_change)
        vol_24h_s, vol_24h_sl = format_value(
            vol_24h_title, vol_24h_max_len, vol_24h, vol_24h_change_max_len, vol_24h_change)
        vol_7d_s, vol_7d_sl = format_value(vol_7d_title, vol_7d_max_len, vol_7d)

        s += f' {name_s}{price_s}{tvl_s}{vol_24h_s}{vol_7d_s}\n'

    header = click.style(
        f' {name_title:>{name_max_len}} │{price_title:>{price_sl}} │{tvl_title:>{tvl_sl}} │'
        f'{vol_24h_title:>{vol_24h_sl}} │{vol_7d_title:>{vol_7d_sl}}\n',
        fg=cli_colors.table.fg, bold=cli_colors.table.bold)

    s = header + s
    click.echo(s, nl=False)


def fail(ctx: click.Context, message: str, err: Optional[Exception] = None):
    """Print an error message and exit
    """

    message = f'{message}: {err}' if err else message
    styled_message = click.style(message, fg=cli_colors.error.fg, bold=cli_colors.error.bold)

    ctx.fail(styled_message)


@click.group(name=CLI_NAME)
@click.version_option(version=__version__, prog_name=CLI_NAME)
@click.pass_context
def cli(ctx: click.Context):
    """FlatQube client CLI tool
    """

    ctx.ensure_object(dict)
    ctx.obj['client'] = FlatQubeClient()


@cli.group()
def currency():
    """FlatQube currencies info
    """


@currency.group(name='config')
def currency_config():
    """Currency config tools
    """


@currency_config.command(name='show')
@click.option('-l', '--list', 'currency_list', help='Show tokens from the given list')
@click.pass_context
def show_currencies(ctx: click.Context, currency_list: str):
    """Show currencies in the config or given list
    """

    if currency_list:
        if currency_list not in config.currency_lists:
            fail(ctx, f"'{currency_list}' does not exist.")

        names = config.currency_lists[currency_list]
        currencies = {name: address for name, address in config.currencies.items() if name in names}
    else:
        currencies = config.currencies

    title_name = 'Name'
    title_address = 'Address'

    names, addresses = zip(*currencies.items())
    name_max_len = max(len(name) for name in names + (title_name,))

    s = click.style(f'{title_name:>{name_max_len}} │ {title_address}\n',
                    fg=cli_colors.table.fg, bold=cli_colors.table.bold)

    for name, address in zip(names, addresses):
        s += click.style(f'{name:>{name_max_len}} ', fg=cli_colors.name.fg, bold=cli_colors.name.bold)
        s += click.style('│ ', fg=cli_colors.table.fg, bold=cli_colors.table.bold)
        s += click.style(f'{address}\n', fg=cli_colors.value.fg, bold=cli_colors.value.bold)

    click.echo(s, nl=False)


@currency_config.command()
def lists():
    """Show all currency lists
    """

    s = ''
    for c_list in config.currency_lists:
        s += f'{c_list}\n'

    click.echo(s, nl=False)


@currency_config.command()
@click.argument('address')
@click.pass_context
def add_currency(ctx: click.Context, address: str):
    """Add a new currency by the contract address to the config
    """

    client: FlatQubeClient = ctx.obj['client']

    try:
        info = client.currency_by_address(address)
    except Exception as err:
        fail(ctx, 'Cannot get currency by address', err=err)
        return

    add_currency_to_config(info.name, info.address)

    name = click.style(f'{info.name}', fg=cli_colors.name.fg, bold=cli_colors.name.bold)
    address = click.style(f'{info.address}', fg=cli_colors.address.fg, bold=cli_colors.address.bold)

    click.echo(f"{name} {address} was added to the user config")


@currency.command()
@click.argument('names', nargs=-1)
@click.option('-l', '--list', 'currency_list', default=None, help="The list of tokens to show from the config")
@click.option('-s', '--sort', type=click.Choice(sort_options), default=cli_cfg.currency.show.sort,
              show_default=True, help="Sort displayed currencies")
@click.option('-o', '--sort-order', type=click.Choice(sort_orders), default=cli_cfg.currency.show.sort_order,
              show_default=True, help='Sort order')
@click.option('-u', '--update', is_flag=True, default=False, show_default=True, help='Auto update data')
@click.option('-i', '--update-interval', type=float, default=cli_cfg.currency.show.update_interval, show_default=True,
              help='Auto update interval in seconds')
@click.pass_context
def show(ctx: click.Context, names: list[str],
         currency_list: Optional[str],
         sort: str, sort_order: str,
         update: bool, update_interval: float):
    """Show currencies info
    """

    sort = CurrencySortOptions(sort)
    sort_order = CurrencySortOrders(sort_order)

    if not names and not currency_list:
        names = config.currency_lists[cli_cfg.currency.show.default_list]
    elif not names and currency_list:
        if currency_list not in config.currency_lists:
            fail(ctx, f"'{currency_list}' currency list does not exist in the config.")
        names = config.currency_lists[currency_list]
    elif names and currency_list:
        fail(ctx, "'-l/--list' option is not allowed if NAMES were set.")

    client: FlatQubeClient = ctx.obj['client']

    lines = 0

    while True:
        for _ in range(lines):
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")

        try:
            currencies_info = client.currencies(*names, sort=sort, sort_order=sort_order)
        except Exception as err:
            fail(ctx, f"Failed to get currencies info", err=err)
            return

        print_currencies_info(currencies_info, sort, sort_order)

        if not update:
            break

        time.sleep(update_interval)
        lines = len(currencies_info) + 1
