# -*- coding: utf-8 -*-

from typing import Any, Optional, Union, Iterable, Generic, TypeVar, Type
from enum import Enum
from operator import attrgetter
from decimal import Decimal

import requests
from pydantic import ValidationError

from .config import config
from .models import CurrencyInfo, PairInfo, FarmingPoolInfo


class FlatQubeClientError(Exception):
    pass


class SortOrder(str, Enum):
    ascend = 'ascend'
    descend = 'descend'


TData = TypeVar('TData', bound=Union[CurrencyInfo, PairInfo])


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
    """Currencies sort by
    """

    price = 'price'
    price_change = 'price-ch'
    tvl = 'tvl'
    tvl_change = 'tvl-ch'
    volume_24h = 'vol24h'
    volume_change_24h = 'vol24h-ch'
    volume_7d = 'vol7d'
    transaction_count_24h = 'trans24h'
    fee_24h = 'fee24h'


class PairSortBy(SortBy[PairInfo], str, Enum):
    """Pairs sort by
    """

    fee_24h = 'fee24h'
    fee_7d = 'fee7d'
    fee_all_time = 'fee-all-time'
    left_locked = 'left-locked'
    right_locked = 'right-locked'
    left_price = 'left-price'
    right_price = 'right-price'
    tvl = 'tvl'
    tvl_change = 'tvl-ch'
    volume_24h = 'vol24h'
    volume_24h_change = 'vol24h-ch'
    volume_7d = 'vol7d'


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

    def currency_total_count(self, white_list_url: Optional[str] = None) -> int:
        """Return total currencies on the service or a white list
        """

        return self._get_total_count('currencies', white_list_url=white_list_url)

    def all_currencies(self, white_list_url: Optional[str] = None) -> Iterable[CurrencyInfo]:
        """Generator for all currencies from the service or a white list
        """

        yield from self._get_currencies(white_list_url=white_list_url)

    def whitelist_currencies(self) -> Iterable[CurrencyInfo]:
        """Return Broxus white list currencies
        """

        yield from self._get_currencies(white_list_url=config.token_white_list_url)

    def currencies(self,
                   addresses: Iterable[str],
                   white_list_url: Optional[str] = None,
                   sort_by: Union[str, CurrencySortBy] = CurrencySortBy.tvl,
                   sort_order: Union[str, SortOrder] = SortOrder.ascend) -> list[CurrencyInfo]:
        """Get currencies info by addresses
        """

        sort_by = CurrencySortBy(sort_by)
        sort_order = SortOrder(sort_order)

        params = {
            'currencyAddresses': list(addresses)
        }

        currencies = self._get_currencies(
            params=params,
            white_list_url=white_list_url
        )

        return sort_by(
            currencies,
            order=sort_order,
            inplace=False,
        )

    def currency(self, address: str) -> CurrencyInfo:
        """Get currency info by address
        """

        api_url = f'{self._swap_api_url}/currencies/{address}'

        return self._parse_currency_data(
            self._request(self.session.post, api_url)
        )

    def pair_total_count(self, white_list_url: Optional[str] = None) -> int:
        """Return total pairs on the service or a white list
        """

        return self._get_total_count('pairs', white_list_url=white_list_url)

    def all_pairs(self,
                  tvl_ge: Union[None, float, Decimal] = None,
                  tvl_le: Union[None, float, Decimal] = None,
                  white_list_url: Optional[str] = None) -> Iterable[PairInfo]:
        """Get info about all pairs on FlatQube
        """

        tvl_ge = str(tvl_ge) if tvl_ge else None
        tvl_le = str(tvl_le) if tvl_le else None

        params = {
            'tvlAmountGe': tvl_ge,
            'tvlAmountLe': tvl_le,
        }

        yield from self._get_pairs(params=params, white_list_url=white_list_url)

    def whitelist_pairs(self,
                        tvl_ge: Union[None, float, Decimal] = None,
                        tvl_le: Union[None, float, Decimal] = None) -> Iterable[PairInfo]:
        """Return Broxus white list pairs
        """

        yield from self.all_pairs(
            tvl_ge=tvl_ge,
            tvl_le=tvl_le,
            white_list_url=config.token_white_list_url
        )

    def pairs(self,
              currency_address: str,
              currency_addresses: Union[None, str, Iterable[str]] = None,
              tvl_ge: Union[None, float, Decimal] = None,
              tvl_le: Union[None, float, Decimal] = None,
              white_list_url: Optional[str] = None,
              sort_by: Union[str, PairSortBy] = PairSortBy.tvl,
              sort_order: Union[str, SortOrder] = SortOrder.ascend) -> list[PairInfo]:
        """Get pairs info by given currency addresses
        """

        sort_by = PairSortBy(sort_by)
        sort_order = SortOrder(sort_order)

        if isinstance(currency_addresses, str):
            currency_addresses = [currency_addresses]
        elif isinstance(currency_addresses, Iterable):
            currency_addresses = list(currency_addresses)

        tvl_ge = str(tvl_ge) if tvl_ge else None
        tvl_le = str(tvl_le) if tvl_le else None

        params = {
            'currencyAddress': currency_address,
            'currencyAddresses': currency_addresses,
            'tvlAmountGe': tvl_ge,
            'tvlAmountLe': tvl_le,
        }

        pairs = self._get_pairs(
            params=params,
            white_list_url=white_list_url
        )

        return sort_by(
            pairs,
            order=sort_order,
            inplace=False,
        )

    def pair(self, left_address: str, right_address: Optional[str] = None) -> PairInfo:
        """Get pair info by pool address or left/right currency addresses
        """

        base_url = f'{self._swap_api_url}/pairs'

        if right_address is None:
            api_url = f'{base_url}/address/{left_address}'
        else:
            api_url = f'{base_url}/left/{left_address}/right/{right_address}'

        return self._parse_pair_data(
            self._request(self.session.post, api_url)
        )

    def farmin_pool(self,
                    pool_address: str,
                    user_address: Optional[str] = None,
                    after_zero_balance: bool = True) -> FarmingPoolInfo:
        """Get info about a farming pool
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

    def _get_total_count(self, name: str, white_list_url: Optional[str] = None):
        api_url = f'{self._swap_api_url}/{name}'

        data = {
            "limit": 0,
            "offset": 0,
            "whiteListUri": white_list_url,
        }

        result = self._request(self.session.post, api_url, data=data)
        return result['totalCount']

    @staticmethod
    def _parse_data(name: str, data: dict[str, Any], model_cls: Type[TData]) -> TData:
        try:
            return model_cls.parse_obj(data)
        except ValidationError as err:
            raise FlatQubeClientError(f'Cannot parse {name} data "{data}"\n{err}') from err

    def _parse_currency_data(self, data: dict[str, Any]) -> CurrencyInfo:
        return self._parse_data('currency', data, CurrencyInfo)

    def _parse_pair_data(self, data: dict[str, Any]) -> PairInfo:
        return self._parse_data('pair', data, PairInfo)

    def _get_data(self,
                  name: str,
                  params: Optional[dict[str, Any]] = None,
                  white_list_url: Optional[str] = None) -> Iterable[dict[str, Any]]:
        api_url = f'{self._swap_api_url}/{name}'

        if not params:
            params = {}

        data = {
            **params,
            "limit": config.api_bulk_limit,
            "offset": 0,
            "whiteListUri": white_list_url,
        }

        while True:
            result = self._request(self.session.post, api_url, data=data)

            for info in result[name]:
                yield info

            offset = data['offset'] + len(result[name])
            if offset == result['totalCount']:
                break
            data['offset'] = offset

    def _get_currencies(self,
                        params: Optional[dict[str, Any]] = None,
                        white_list_url: Optional[str] = None) -> Iterable[CurrencyInfo]:
        for currency_data in self._get_data('currencies', params, white_list_url):
            yield self._parse_currency_data(currency_data)

    def _get_pairs(self,
                   params: Optional[dict[str, Any]] = None,
                   white_list_url: Optional[str] = None) -> Iterable[PairInfo]:
        for pair_data in self._get_data('pairs', params, white_list_url):
            yield self._parse_pair_data(pair_data)
