# -*- coding: utf-8 -*-

from typing import Optional, Union
from enum import Enum
from itertools import count

import requests

from .config import config
from .models import CurrencyInfo


class FlatQubeClientError(Exception):
    pass


class CurrencySortOptions(str, Enum):
    none = 'none'
    price = 'price'
    price_change = 'price-ch'
    tvl = 'tvl'
    tvl_change = 'tvl-ch'
    volume24h = 'vol24h'
    volume24h_change = 'vol24h-ch'
    volume7d = 'vol7d'


class CurrencySortOrders(str, Enum):
    ascend = 'ascend'
    descend = 'descend'


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

        try:
            with self.session.post(api_url) as resp:
                resp.raise_for_status()
        except Exception as err:
            raise FlatQubeClientError(f'{err}') from err

        currency_info = resp.json()
        return CurrencyInfo.parse_obj(currency_info)

    def currency(self, name: str) -> CurrencyInfo:
        """Get currency info by name
        """

        currency_address = config.currencies.get(name.upper())

        if not currency_address:
            raise FlatQubeClientError(
                f"'{name}' currency address is unknown. The currency does not exist in the config.")

        return self.currency_by_address(address=currency_address)

    def currencies(self, *names: str,
                   sort: Union[str, CurrencySortOptions] = CurrencySortOptions.none,
                   sort_order: Union[str, CurrencySortOrders] = CurrencySortOrders.ascend) -> list[CurrencyInfo]:
        """Get currencies info
        """

        sort = CurrencySortOptions(sort)
        sort_order = CurrencySortOrders(sort_order)

        currency_addresses = []

        for name in names:
            currency_address = config.currencies.get(name.upper())

            if not currency_address:
                raise FlatQubeClientError(
                    f"'{name}' currency address is unknown. The currency does not exist in the config.")

            currency_addresses.append(currency_address)

        api_url = f'{self._swap_api_url}/currencies'

        data = {
            'currencyAddresses': currency_addresses,
            "limit": len(currency_addresses),
            "offset": 0,
            'ordering': 'tvlascending',
        }

        try:
            with self.session.post(api_url, json=data) as resp:
                resp.raise_for_status()
        except Exception as err:
            raise FlatQubeClientError(f'{err}') from err

        currencies_info = resp.json().get('currencies', [])

        currencies = [
            CurrencyInfo.parse_obj(currency_info) for currency_info in currencies_info
        ]

        name_indices = {name: index for name, index in zip(names, count())}

        def _sort_currencies_key(currency: CurrencyInfo):
            if sort == CurrencySortOptions.none:
                return name_indices[currency.name]
            elif sort == CurrencySortOptions.price:
                return currency.price
            elif sort == CurrencySortOptions.price_change:
                return currency.price_change
            elif sort == CurrencySortOptions.tvl:
                return currency.tvl
            elif sort == CurrencySortOptions.tvl_change:
                return currency.tvl_change
            elif sort == CurrencySortOptions.volume24h:
                return currency.volume_24h
            elif sort == CurrencySortOptions.volume24h_change:
                return currency.volume_change_24h
            elif sort == CurrencySortOptions.volume7d:
                return currency.volume_7d

        reverse = True if sort_order == CurrencySortOrders.descend else False
        currencies.sort(key=_sort_currencies_key, reverse=reverse)

        return currencies
