# flatqube-client

[![PyPI version](https://img.shields.io/pypi/v/flatqube-client.svg)](https://pypi.python.org/pypi/flatqube-client)
![Supported Python versions](https://img.shields.io/pypi/pyversions/flatqube-client.svg)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

flatqube-client is an API client library and CLI tools for [FlatQube](https://app.flatqube.io) DEX service in [Everscale](https://everscale.network) blockchain network.

## Installing

```
pip3 install -U flatqube-client
```

## Usage

Main CLI help:

```
flatqube --help
```

### Show Currency Info

Show selected currencies:

```
flatqube currency show wever qube bridge
```

Show the default (`whitelist`) list of currencies:

```
flatqube currency show
```

Also, we can show some list, "everscale" for example:

```
flatqube currency show -l everscale
```

Or we can show meme tokens sorted by price change:

```
flatqube currency show -l meme -s price-ch
```

We can show currencies by names and currencies from multiple lists jointly:

```
flatqube currency show weth wbtc -l everscale -l stable
```

Also, we can run cli in "auto-update" mode with interval 3 seconds (by default update interval is 5 seconds):

```
flatqube currency show -s price-ch -u -i3
```

See help for more info about `currency show` command:

```
flatqube currency show --help
```

## License

[MIT](https://opensource.org/licenses/MIT)
