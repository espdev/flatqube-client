# -*- coding: utf-8 -*-

from typing import Optional
from decimal import Decimal

from pydantic import BaseModel, Field, Extra


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


class RewardTokenInfo(BaseModel):
    """Reward token info
    """

    class Config:
        extra: Extra.ignore

    currency_address: str = Field(alias='reward_root_address')
    currency_name: str = Field(alias='reward_currency')
    reward_per_second: Decimal


class RewardTokenInfo1(BaseModel):
    """Reward token info
    """

    class Config:
        extra: Extra.ignore

    currency_address: str = Field(alias='rewardTokenRootAddress')
    currency_name: str = Field(alias='rewardTokenCurrency')
    reward_per_second: Decimal = Field(alias='rewardPerSec')


class RoundInfo(BaseModel):
    """Round info
    """

    start_time: int
    end_time: Optional[int]
    reward_info: list[RewardTokenInfo1]


class PoolInfo(BaseModel):
    """Pool info
    """

    vesting_period: int
    vesting_ratio: int

    round_info: list[RoundInfo] = Field(alias='rounds_info')

    class Config:
        extra: Extra.ignore


class HistoryInfo(BaseModel):
    """History info
    """

    left_amount: Decimal
    right_amount: Decimal
    usdt_amount: Decimal


class FarmingPoolInfo(BaseModel):
    """Farming pool info
    """

    class Config:
        extra: Extra.ignore

    pool_address: str

    left_currency_address: str = Field(alias='left_address')
    right_currency_address: str = Field(alias='right_address')
    left_currency_name: str = Field(alias='left_currency')
    right_currency_name: str = Field(alias='right_currency')

    pool_balance: Decimal
    left_balance: Decimal
    right_balance: Decimal

    tvl: Decimal
    tvl_change: Decimal

    apr: Decimal
    apr_change: Decimal

    user_share: Decimal = Field(alias='share')
    user_share_change: Decimal = Field(alias='share_change')

    user_token_balance: Decimal
    user_usdt_balance: Decimal

    lp_token_address: str = Field(alias='token_root_address')
    lp_token_name: str = Field(alias='token_root_currency')

    farm_start_time: int
    farm_end_time: Optional[int]
    is_active: bool
    is_low_balance: bool

    reward_info: list[RewardTokenInfo] = Field(alias='reward_token_root_info')
    pool_info: PoolInfo
    history_info: HistoryInfo
