# -*- coding: utf-8 -*-

from typing import NamedTuple
from pathlib import Path

import appdirs
from omegaconf import DictConfig, OmegaConf


APP_NAME = 'flatqube-info'
ROOT_PATH = Path(__file__).parent
DEFAULT_CONFIG_PATH = ROOT_PATH / 'config.yaml'
USER_CONFIG_PATH = Path(appdirs.user_config_dir(APP_NAME)) / 'config.yaml'


class ConfigError(Exception):
    pass


class LoadConfigError(ConfigError):
    pass


class UpdateConfigError(ConfigError):
    pass


class SaveConfigError(ConfigError):
    pass


class ConfigFileDoesNotExistError(ConfigError):
    pass


class ConfigPaths(NamedTuple):
    """Ordered config paths
    """

    default_path: Path  # default config in the app package
    user_path: Path  # user config in user app dir


config_paths = ConfigPaths(
    default_path=DEFAULT_CONFIG_PATH,
    user_path=USER_CONFIG_PATH,
)


def update_config(cfg: DictConfig, config_path: Path, label: str, not_exist_error: bool = False) -> DictConfig:
    """Update the existing config object from new config file

    Parameters
    ----------
    cfg: DictConfig
        Configuration object to update.
    config_path : Path
        Config file path from which to update the config.
    label : str
        The label for the configuration to add in __config_paths__ meta info
    not_exist_error : bool
        If True raise ``ConfigFileDoesNotExistError`` if the config file does not exist.

    Returns
    -------
    config : DictConfig
        Updated configuration object

    Raises
    ------
    ConfigFileDoesNotExistError : If ``not_exist_error`` is True and the config file does not exist.
    UpdateConfigError : If an error occurred while updating config

    See Also
    --------
    load_config

    """

    if config_path.is_file():
        try:
            new_config = OmegaConf.load(config_path)
            cfg = OmegaConf.merge(cfg, new_config)
        except Exception as err:
            raise UpdateConfigError(f"Cannot update config from '{config_path}': {err}") from err
        else:
            if OmegaConf.is_missing(cfg, '__config_paths__'):
                cfg.__config_paths__ = {}
            cfg.__config_paths__[label] = str(config_path)
    elif not_exist_error:
        raise ConfigFileDoesNotExistError(f"'{config_path}' does not exist.")

    return cfg


def load_config() -> DictConfig:
    """Load and return the configuration object

    Returns
    -------
    config : DictConfig
        The configuration object

    Raises
    ------
    LoadConfigError : Cannot load config from config file(s)

    See Also
    --------
    update_config

    """

    try:
        cfg = OmegaConf.load(config_paths.default_path)
    except Exception as err:
        raise LoadConfigError(
            f"Cannot load default configuration from '{config_paths.default_path}': {err}") from err

    cfg.__config_paths__ = {'default': str(config_paths.default_path)}

    try:
        cfg = update_config(cfg, config_paths.user_path, 'user')
    except Exception as err:
        raise LoadConfigError(f'{err}') from err

    return cfg


# Load the config globally
config = load_config()


def _load_or_create_user_config(draft_config: dict) -> DictConfig:
    """Load or create the user config from the draft
    """

    if config_paths.user_path.exists():
        try:
            cfg = OmegaConf.load(config_paths.user_path)
        except Exception as err:
            raise LoadConfigError(
                f"Cannot load the user configuration from '{config_paths.user_path}': {err}") from err
    else:
        try:
            config_paths.user_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as err:
            raise SaveConfigError(
                f"Cannot create a user directory '{config_paths.user_path.parent}': {err}") from err

        cfg = OmegaConf.create(draft_config)

    return cfg


def _save_user_config(cfg: DictConfig):
    """Save the user config and update the config globally
    """

    try:
        OmegaConf.save(cfg, config_paths.user_path)
    except Exception as err:
        raise SaveConfigError(
            f"Cannot save the user configuration to '{config_paths.user_path}': {err}") from err

    global config
    config = load_config()


def add_currency_to_config(name: str, address: str):
    """Add a new currency to the user config
    """

    cfg = _load_or_create_user_config({
        'currencies': {}
    })

    cfg.currencies[name.upper()] = address

    _save_user_config(cfg)
