# -*- coding: utf-8 -*-

from typing import Optional

import requests

from .config import config
from .models import CurrencyInfo


class FlatQubeClientError(Exception):
    pass


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
            raise FlatQubeClientError(f"'{name}' currency address is unknown. The currency does not exist in the config.")

        return self.currency_by_address(address=currency_address)

    def currencies(self, *names: str) -> list[CurrencyInfo]:
        """Get currencies info
        """

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

        return [
            CurrencyInfo.parse_obj(currency_info) for currency_info in currencies_info
        ]