# -*- coding: utf-8 -*-

from decimal import Decimal
from typing import cast, Literal, Optional

import humanize
from rich import print as rich_print
from rich.table import Table

from flatqube import CurrencyInfo, CurrencySortBy, SortOrder
from flatqube.config import config


USD_PREFIX = '$'
PCT_SUFFIX = '%'

console_styles = config.console.styles
console_table = config.console.table
border_ch = console_table.border


def indent_text(title: str, indent: int = 1):
    indent_s = ' ' * indent
    return f'{indent_s}{title}'


def humanize_value(value: Decimal) -> str:
    return humanize.intcomma(f'{value:f}')


def styled_text(text: str, style: str):
    return f'[{style}]{text}'


def quantize_value(value: Decimal, decimal_digits: Optional[int] = None, normalize: bool = True) -> Decimal:
    if not decimal_digits:
        value_int = value.to_integral_value()
        num_int_digits = len(value_int.as_tuple().digits)
        decimal_digits = config.quantize.value_decimal_digits.get(num_int_digits, 0)

    exponent = Decimal('1.{}'.format('0' * decimal_digits))
    value = value.quantize(exponent)

    if normalize:
        value = value.normalize()

    return value


def quantize_value_change(value_change: Decimal) -> Decimal:
    return quantize_value(value_change,
                          decimal_digits=config.quantize.value_change_decimal_digits,
                          normalize=config.quantize.value_change_normalize)


def format_value(value, prefix=USD_PREFIX, style=console_styles.value):
    if isinstance(value, Decimal):
        value = quantize_value(value)
    else:
        value = quantize_value(Decimal(value), decimal_digits=0, normalize=True)
    value = humanize_value(value)
    value = f'{prefix}{value}'
    return styled_text(indent_text(value), style)


def format_value_change(value_change, suffix=PCT_SUFFIX):
    qh_value_change = humanize_value(quantize_value_change(value_change))
    prefix = ''
    if value_change == 0:
        style = console_styles.value_change_zero
    elif value_change > 0:
        prefix = '+'
        style = console_styles.value_change_plus
    else:
        style = console_styles.value_change_minus

    value = f'{prefix}{qh_value_change}{suffix}'
    return styled_text(indent_text(value, indent=2), style)


def print_currencies_info(currencies_info: list[CurrencyInfo],
                          sort: CurrencySortBy,
                          sort_order: SortOrder,
                          show_trans_count: bool):
    """Print currency info in console
    """

    name_title = 'Name'
    price_title = 'Price'
    price_change_title = PCT_SUFFIX
    tvl_title = 'TVL'
    tvl_change_title = PCT_SUFFIX
    vol_24h_title = '24h Volume'
    vol_24h_change_title = PCT_SUFFIX
    vol_7d_title = '7d Volume'
    trans_24h_title = '24h Tr-s'

    if len(currencies_info) > 1:
        if sort_order == SortOrder.ascend:
            sort_indicator = console_table.sort_ascend
        else:
            sort_indicator = console_table.sort_descend
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

    currencies_table = Table.grid()

    currencies_table.show_header = True
    currencies_table.header_style = console_styles.table

    indent_border = indent_text(border_ch)
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

    border = styled_text(indent_border, console_styles.table)

    for currency_info in currencies_info:
        currency_row = (
            styled_text(indent_text(currency_info.name), console_styles.name),
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
