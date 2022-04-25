# -*- coding: utf-8 -*-

from decimal import Decimal

from pydantic import BaseModel, Field


class CurrencyInfo(BaseModel):
    """Currency info
    """

    name: str = Field(alias='currency')
    address: str
    price: Decimal
    price_change: Decimal = Field(alias='priceChange')
    tvl: Decimal
    tvl_change: Decimal = Field(alias='tvlChange')
    volume_24h: Decimal = Field(alias='volume24h')
    volume_change_24h: Decimal = Field(alias='volumeChange24h')
    volume_7d: Decimal = Field(alias='volume7d')
    fee_24h: Decimal = Field(alias='fee24h')
    transaction_count_24h: int = Field(alias='transactionsCount24h')
