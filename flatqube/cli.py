# -*- coding: utf-8 -*-

from typing import Optional, Union
from decimal import Decimal
import time
import sys

import click
from click_option_group import optgroup, MutuallyExclusiveOptionGroup
import humanize

from .config import config, add_currency
from .client import FlatQubeClient, CurrencySortOptions, CurrencySortOrders
from .models import CurrencyInfo


cli_cfg = config.cli
cli_colors = config.cli_colors


def quantize_value(value: Decimal, decimal_digits: Optional[int] = None, normalize: bool = True) -> Decimal:
    if not decimal_digits:
        value_int = value.to_integral_value()
        num_int_digits = len(value_int.as_tuple().digits)
        decimal_digits = config.quantize.decimal_digits.get(num_int_digits, 0)

    exponent = Decimal('1.{}'.format('0' * decimal_digits))
    value = value.quantize(exponent)

    if normalize:
        value = value.normalize()

    return value


def human_value(value: Decimal) -> str:
    return humanize.intcomma(f'{value:f}')


def len_decimal(value: Decimal, plus: bool = False) -> int:
    value_len = len(human_value(value))
    if plus and not value.is_signed():
        value_len += 1
    return value_len


def quantize_value_change(value: Decimal, value_change: Decimal) -> tuple[Decimal, Decimal]:
    value_q = quantize_value(value)
    value_change_q = quantize_value(value_change, decimal_digits=2, normalize=False)
    return value_q, value_change_q


def max_lens(values: list[tuple[Decimal, Decimal]]) -> tuple[int, int]:
    value_max_len = max(len_decimal(value) for value, _ in values)
    value_change_max_len = max(len_decimal(value_change, plus=True) for _, value_change in values)
    return value_max_len, value_change_max_len


def value_indent(value_max_len: int, value: Union[str, Decimal], plus: bool = False) -> str:
    if isinstance(value, str):
        value_len = len(value)
    else:
        value_len = len_decimal(value, plus=plus)

    return ' ' * (value_max_len - value_len)


def format_value(value_max_len: int, value: Decimal,
                 value_change_max_len: Optional[int] = None, value_change: Optional[Decimal] = None) -> tuple[str, int]:
    v_indent = value_indent(value_max_len, value)
    value_h = human_value(value)

    s = click.style(f'|', fg=cli_colors.table.fg, bold=cli_colors.table.bold)

    vs = f' {v_indent}${value_h} '
    value_len = len(vs)
    s += click.style(vs, fg=cli_colors.value.fg, bold=cli_colors.value.bold)

    if value_change_max_len is not None and value_change is not None:
        value_change_indent = value_indent(value_change_max_len, value_change, plus=True)

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

        value_change_h = human_value(value_change)

        vs = f' {value_change_indent}{value_change_sign}{value_change_h}% '
        value_len += len(vs)
        s += click.style(vs, fg=value_change_color, bold=value_change_bold)

    return s, value_len


def print_currencies_info(currencies_info: list[CurrencyInfo],
                          sort: CurrencySortOptions, sort_order: CurrencySortOrders):
    names = []
    price_values = []
    tvl_values = []
    volume_24h_values = []
    volume_7d_values = []

    for currency_info in currencies_info:
        names.append(currency_info.name)

        price_values.append(
            quantize_value_change(currency_info.price, currency_info.price_change)
        )

        tvl_values.append(
            quantize_value_change(currency_info.tvl, currency_info.tvl_change)
        )

        volume_24h_values.append(
            quantize_value_change(currency_info.volume_24h, currency_info.volume_change_24h)
        )

        volume_7d_values.append(
            quantize_value(currency_info.volume_7d)
        )

    sort_indicator = ' ▲' if sort_order == CurrencySortOrders.ascend else ' ▼'
    change_sort_indicator = '%'

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
    price_title = 'Price' + price_sort_indicator
    tvl_title = 'TVL' + tvl_sort_indicator
    vol_24h_title = '24h Volume' + volume_24h_sort_indicator
    vol_7d_title = '7d Volume' + volume_7d_sort_indicator

    name_max_len = max(len(name) for name in names + [name_title])
    price_max_len, price_change_max_len = max_lens(price_values)
    tvl_max_len, tvl_change_max_len = max_lens(tvl_values)
    vol_24h_max_len, vol_24h_change_max_len = max_lens(volume_24h_values)
    vol_7d_max_len = max(max(len_decimal(volume_7d) for volume_7d in volume_7d_values), len(vol_7d_title) - 1)

    s = ''
    price_sl = 0
    tvl_sl = 0
    vol_24h_sl = 0
    vol_7d_sl = 0

    for name, (price, price_change), (tvl, tvl_change), (vol_24h, vol_24h_change), vol_7d in \
            zip(names, price_values, tvl_values, volume_24h_values, volume_7d_values):

        name_indent = value_indent(name_max_len, name)
        name_s = click.style(f'{name_indent}{name} ', fg=cli_colors.name.fg, bold=cli_colors.name.bold)

        price_s, price_sl = format_value(price_max_len, price, price_change_max_len, price_change)
        tvl_s, tvl_sl = format_value(tvl_max_len, tvl, tvl_change_max_len, tvl_change)
        vol_24h_s, vol_24h_sl = format_value(vol_24h_max_len, vol_24h, vol_24h_change_max_len, vol_24h_change)
        vol_7d_s, vol_7d_sl = format_value(vol_7d_max_len, vol_7d)

        s += f'{name_s}{price_s}{tvl_s}{vol_24h_s}{vol_7d_s}\n'

    name_indent = value_indent(name_max_len, name_title)
    price_indent = value_indent(price_sl - 1, price_title)
    tvl_indent = value_indent(tvl_sl - 1, tvl_title)
    vol_24h_indent = value_indent(vol_24h_sl - 1, vol_24h_title)
    vol_7d_indent = value_indent(vol_7d_sl - 1, vol_7d_title)

    header = click.style(
        f'{name_indent}{name_title} |{price_indent}{price_title} |{tvl_indent}{tvl_title} |'
        f'{vol_24h_indent}{vol_24h_title} |{vol_7d_indent}{vol_7d_title}\n',
        fg=cli_colors.table.fg, bold=cli_colors.table.bold)

    s = header + s
    click.echo(s, nl=False)


def add(ctx: click.Context, address: str):
    """Add a new currency by the contract address to the config
    """

    client: FlatQubeClient = ctx.obj['client']

    try:
        info = client.currency_by_address(address)
    except Exception as err:
        fail(ctx, 'Cannot get currency by address', err=err)
        return

    add_currency(info.name, info.address)

    name = click.style(f'{info.name}', fg=cli_colors.name.fg, bold=cli_colors.name.bold)
    address = click.style(f'{info.address}', fg=cli_colors.value.fg, bold=cli_colors.value.bold)

    click.echo(f"Currency {name} added with address {address}")


def fail(ctx: click.Context, message: str, err: Optional[Exception] = None):
    """Print an error message and exit
    """

    message = f'{message}: {err}' if err else message
    styled_message = click.style(message, fg=cli_colors.error.fg, bold=cli_colors.error.bold)

    ctx.fail(styled_message)


@click.group()
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


@currency.command(name='config')
@optgroup.group('Config options', cls=MutuallyExclusiveOptionGroup)
@optgroup.option('--show-lists', is_flag=True, default=False, help='Show token lists')
@optgroup.option('-l', '--list', 'currency_list', help='Show tokens from the given list')
@optgroup.option('--add', 'address_to_add', help='Add a currency to the config by its contract address')
@click.pass_context
def config_(ctx: click.Context, show_lists: bool, currency_list: Optional[str], address_to_add: Optional[str]):
    """Currency config tools
    """

    if show_lists:
        s = ''
        for c_list in config.currency_lists:
            s += f'{c_list}\n'

        click.echo(s, nl=False)
        return

    if address_to_add:
        add(ctx, address_to_add)
        return

    if currency_list:
        if currency_list not in config.currency_lists:
            fail(ctx, f"'{currency_list}' does not exist.")

        names = config.currency_lists[currency_list]
        currencies = {name: address for name, address in config.currencies.items() if name in names}
    else:
        currencies = config.currencies

    names, addresses = zip(*currencies.items())
    name_max_len = max(len(name) for name in names)
    indents = [' ' * (name_max_len - len(name)) for name in names]

    title_name = 'Name'
    title_address = 'Address'

    title_name_indent = ' ' * (name_max_len - len(title_name))
    s = click.style(f'{title_name_indent}{title_name} | {title_address}\n',
                    fg=cli_colors.table.fg, bold=cli_colors.table.bold)

    for indent, name, address in zip(indents, names, addresses):
        s += click.style(f'{indent}{name} ', fg=cli_colors.name.fg, bold=cli_colors.name.bold)
        s += click.style('| ', fg=cli_colors.table.fg, bold=cli_colors.table.bold)
        s += click.style(f'{address}\n', fg=cli_colors.value.fg, bold=cli_colors.value.bold)

    click.echo(s, nl=False)


sort_options = tuple(item.value for item in CurrencySortOptions)
sort_orders = tuple(item.value for item in CurrencySortOrders)


@currency.command()
@click.argument('names', nargs=-1)
@click.option('-l', '--list', 'currency_list', default=None, help="The list of tokens to show from the config")
@click.option('-s', '--sort', type=click.Choice(sort_options), default=CurrencySortOptions.tvl.value,
              show_default=True, help="Sort displayed currencies")
@click.option('-o', '--sort-order', type=click.Choice(sort_orders), default=CurrencySortOrders.ascend.value,
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
        names = config.currency_lists['everscale']
    elif not names and currency_list:
        names = config.currency_lists[currency_list.lower()]
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
