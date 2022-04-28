# -*- coding: utf-8 -*-

from enum import Enum
from operator import attrgetter
from typing import Optional, Union, Iterable, Generic, TypeVar

import requests
from pydantic import ValidationError

from .config import config
from .models import CurrencyInfo, FarmingPoolInfo


class FlatQubeClientError(Exception):
    pass


class SortOrder(str, Enum):
    ascend = 'ascend'
    descend = 'descend'


TData = TypeVar('TData', bound=Union[CurrencyInfo])


class SortBy(Generic[TData]):
    """Generic sort by
    """

    def __call__(self: Enum,
                 iterable: Iterable[TData],
                 *,
                 order: SortOrder = SortOrder.descend,
                 inplace: bool = False) -> Optional[list[TData]]:
        """Sort the given sequency of data by the sort option
        """

        key = attrgetter(self.name)
        reverse = True if order == SortOrder.descend else False

        if inplace:
            if isinstance(iterable, list):
                iterable.sort(key=key, reverse=reverse)
            else:
                raise TypeError("The argument must be a list for sorting inplace.")
            return None
        else:
            return sorted(iterable, key=key, reverse=reverse)


class CurrencySortBy(SortBy[CurrencyInfo], str, Enum):
    """Currency sort by
    """

    price = 'price'
    price_change = 'price-ch'
    tvl = 'tvl'
    tvl_change = 'tvl-ch'
    volume_24h = 'vol24h'
    volume_24h_change = 'vol24h-ch'
    volume_7d = 'vol7d'
    transaction_count_24h = 'trans24h'


class FlatQubeClient:
    """FlatQube REST API client
    """

    def __init__(self):
        self._swap_api_url = config.api_urls.swap_indexer.rstrip('/')
        self._farming_api_url = config.api_urls.farming_indexer.rstrip('/')
        self._session: Optional[requests.Session] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            self._session.close()
            self._session = None

    @property
    def session(self) -> requests.Session:
        if not self._session:
            self._session = requests.Session()
        return self._session

    def currency_by_address(self, address: str) -> CurrencyInfo:
        """Get currency info by address
        """

        api_url = f'{self._swap_api_url}/currencies/{address}'
        currency_info = self._request(self.session.post, api_url)

        try:
            return CurrencyInfo.parse_obj(currency_info)
        except ValidationError as err:
            raise FlatQubeClientError(f'Cannot parse currency info\n{err}') from err

    def currency_by_name(self, name: str) -> CurrencyInfo:
        """Get currency info by name
        """

        name = name.upper()
        currency_address = config.currencies.get(name)

        if not currency_address:
            raise FlatQubeClientError(
                f"'{name}' currency address is unknown. The currency does not exist in the config.")

        return self.currency_by_address(address=currency_address)

    def currencies(self,
                   names: Iterable[str],
                   sort_by: Union[str, CurrencySortBy] = CurrencySortBy.tvl,
                   sort_order: Union[str, SortOrder] = SortOrder.ascend) -> list[CurrencyInfo]:
        """Get currencies info
        """

        sort_by = CurrencySortBy(sort_by)
        sort_order = SortOrder(sort_order)

        currency_addresses = []

        for name in names:
            currency_address = config.currencies.get(name.upper())

            if not currency_address:
                raise FlatQubeClientError(
                    f"'{name.upper()}' currency address is unknown. The currency does not exist in the config.")

            currency_addresses.append(currency_address)

        api_url = f'{self._swap_api_url}/currencies'

        data = {
            'currencyAddresses': currency_addresses,
            "limit": len(currency_addresses),
            "offset": 0,
        }

        info = self._request(self.session.post, api_url, data=data)
        currencies_info = info.get('currencies', [])

        try:
            currencies = [
                CurrencyInfo.parse_obj(currency_info) for currency_info in currencies_info
            ]
        except ValidationError as err:
            raise FlatQubeClientError(f'Cannot parse currency info\n{err}') from err

        sort_by(currencies, order=sort_order, inplace=True)

        return currencies

    def farmin_pool(self,
                    pool_address: str,
                    user_address: Optional[str] = None,
                    after_zero_balance: bool = True) -> FarmingPoolInfo:
        """Get info about farming pool
        """

        api_url = f'{self._farming_api_url}/farming_pools/{pool_address}'

        data = {
            'afterZeroBalance': after_zero_balance,
            'userAddress': user_address,
        }

        farming_pool_info = self._request(self.session.post, api_url, data=data)

        try:
            return FarmingPoolInfo.parse_obj(farming_pool_info)
        except ValidationError as err:
            raise FlatQubeClientError(f'Cannot parse farming pool info\n{err}') from err

    @staticmethod
    def _request(method, api_url, data=None):
        try:
            with method(api_url, json=data) as resp:
                resp.raise_for_status()
                return resp.json()
        except Exception as err:
            raise FlatQubeClientError(f'{err}') from err
