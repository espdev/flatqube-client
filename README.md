# flatqube-client

[![PyPI version](https://img.shields.io/pypi/v/flatqube-client.svg)](https://pypi.python.org/pypi/flatqube-client)
![Supported Python versions](https://img.shields.io/pypi/pyversions/flatqube-client.svg)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

flatqube-client is an API client library and CLI tools for [FlatQube](https://app.flatqube.io) DEX service in [Everscale](https://everscale.network) blockchain network.

## Installing

```
pip install -U flatqube-client
```

## Usage

Main CLI help:

```
flatqube --help
```

### Show Currency Info

Show the default list of currencies:

```
flatqube currency show
```

Also, we can show some list, "meme" for example:

```
flatqube currency show -l meme -s price-ch
```

See help for more info about `currency show` command:

```
flatqube currency show --help
```
