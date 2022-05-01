# -*- coding: utf-8 -*-

from decimal import Decimal
from typing import Optional

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


def styled_text(text: str, style: str):
    return f'[{style}]{text}'
