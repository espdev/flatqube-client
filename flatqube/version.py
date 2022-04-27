# -*- coding: utf-8 -*-

from importlib.metadata import PackageNotFoundError, version

from .constants import APP_NAME


try:
    __version__ = version(APP_NAME)
except PackageNotFoundError:  # pragma: no cover
    __version__ = '0.0.0.dev0'
