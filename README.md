# flatqube-client

[![PyPI version](https://img.shields.io/pypi/v/flatqube-client.svg)](https://pypi.python.org/pypi/flatqube-client)
![Supported Python versions](https://img.shields.io/pypi/pyversions/flatqube-client.svg)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

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

Show selected currencies:

```
flatqube currency show wever qube bridge
```

Show the default list (`everscale`) of currencies:

```
flatqube currency show
```

Also, we can show some list, "star" for example:

```
flatqube currency show -l star
```

![2022-04-27_20-34-34](https://user-images.githubusercontent.com/1299189/165585978-08d49363-7f0f-408b-ba33-e55cae3c630d.png)

Or we can show meme tokens sorted by price change:

```
flatqube currency show -l meme -s price-ch
```

![2022-04-27_20-58-13](https://user-images.githubusercontent.com/1299189/165589946-e9d1c943-ee13-4689-bf94-c45476674b8c.png)

Also, we can run cli in "auto-update" mode. By default update interval is 5 seconds:

```
flatqube currency show -l all -s price-ch -u -i3
```

See help for more info about `currency show` command:

```
flatqube currency show --help
```

## License

[MIT](https://opensource.org/licenses/MIT)
