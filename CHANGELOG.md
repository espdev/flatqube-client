# Changelog

## v0.2.4 (02.05.2022)

- Use rich package for formatting and styling text in CLI
- Add optional "24h Fee" info to `currency show` CLI command

## v0.2.3 (01.05.2022)

- Change CLI structure
  * Move `config` subcommand to CLI top level
  * Rename some subcommands

## v0.2.2 (01.05.2022)

- Fix `currency show` command for default (`whitelist`) list: get value from the config
- Update readme

## v0.2.1 (01.05.2022)

- Fix `currency show` command for default (`whitelist`) list
- Add QUSA meme token to "meme" list
- Update readme

## v0.2.0 (30.04.2022)

- Improve the client API
- Change config format for currencies

## v0.1.9 (28.04.2022)

- Improve `currency show` command:
  * add support of multiple currency lists
  * add support of passing both currency lists and currency names jointly

## v0.1.8 (27.04.2022)

- Fix table border. Add table border character to config

## v0.1.7 (27.04.2022)

- Add optional show 24h transaction count (option `-t/--show-trans-count` in `currency show` command)

## v0.1.6 (27.04.2022)

- Fix formatting currencies
- Update readme

## v0.1.5 (27.04.2022)

- Bugfixes and CLI improvements
- Add "star" currency list with WEVER, BRIDGE and QUBE tokens

## v0.1.4 (27.04.2022)

- Fix a bug in `currency config show` command
- Add main classes to `__init__/__all__` to direct import
- Update readme

## v0.1.3 (27.04.2022)

- Fix formatting currency rows for some corner cases

## v0.1.2 (27.04.2022)

- Fix license badge in the readme
- Add version info to CLI tool

## v0.1.1 (27.04.2022)

- Bugfixes
- Update readme

## v0.1.0 (27.04.2022)

- Initial public release
