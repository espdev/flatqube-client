# -*- coding: utf-8 -*-

from decimal import Decimal
from typing import Optional, Union

import humanize

from flatqube.config import config


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


def humanize_value(value: Decimal) -> str:
    return humanize.intcomma(f'{value:f}')


def len_decimal(value: Decimal, plus: bool = False) -> int:
    value_len = len(humanize_value(value))
    if plus and not value.is_signed():
        value_len += 1
    return value_len


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
