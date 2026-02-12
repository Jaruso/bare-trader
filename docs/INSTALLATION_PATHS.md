# Installation Paths

AutoTrader automatically detects whether it's running in **development mode** or **installed mode** and uses appropriate directories for config, data, and logs.

## Development Mode

When running from the project directory (e.g., `poetry run trader`), AutoTrader uses directories relative to the project root:

- **Config**: `./config/` (contains `strategies.yaml`, `orders.yaml`, `notifications.yaml`)
- **Data**: `./data/` (contains `backtests/`, `optimizations/`, `historical/`, `cache/`)
- **Logs**: `./logs/` (contains `audit.log`, `trader.log`)

## Installed Mode (pipx, Homebrew, or pip install --user)

When installed via **pipx**, Homebrew, or other package managers (any install where the code does not live in a project tree with `config/strategies.yaml`), AutoTrader uses user directories. **pipx is fully supported** and behaves the same as Homebrew for paths and config.

### macOS

- **Config**: `~/.autotrader/config/`
- **Data**: `~/.autotrader/data/`
- **Logs**: `~/.autotrader/logs/`

### Linux

Follows [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html):

- **Config**: `~/.config/autotrader/` (or `$XDG_CONFIG_HOME/autotrader/`)
- **Data**: `~/.local/share/autotrader/` (or `$XDG_DATA_HOME/autotrader/`)
- **Logs**: `~/.local/state/autotrader/` (or `$XDG_STATE_HOME/autotrader/`)

### Windows

- **Config**: `%APPDATA%\autotrader\config\` (or `~/.autotrader/config/`)
- **Data**: `%APPDATA%\autotrader\data\` (or `~/.autotrader/data/`)
- **Logs**: `%APPDATA%\autotrader\logs\` (or `~/.autotrader/logs/`)

## Detection Logic

AutoTrader detects development mode by checking if:
1. `config/strategies.yaml` exists relative to the code location, OR
2. `pyproject.toml` exists relative to the code location

If neither exists, it assumes installed mode and uses user directories.

## Environment Variables

You can override default locations using environment variables:

- `HISTORICAL_DATA_DIR`: Override historical CSV data directory
- `DATA_CACHE_DIR`: Override cache directory
- `XDG_CONFIG_HOME`: Override XDG config directory (Linux)
- `XDG_DATA_HOME`: Override XDG data directory (Linux)
- `XDG_STATE_HOME`: Override XDG state directory (Linux)
- `APPDATA`: Override Windows AppData directory

## Example: First Run After pipx Install

```bash
# Install via pipx (recommended if Homebrew is not available)
pipx install -e . --global
# or: pipx install autotrader --global   # when published to PyPI

# First command creates directories automatically
trader status

# Config files are now in (macOS):
ls ~/.autotrader/config/
# strategies.yaml  orders.yaml  notifications.yaml

# .env for API keys (trader config set):
ls ~/.autotrader/.env

# Backtest results are in:
ls ~/.autotrader/data/backtests/

# Logs are in:
ls ~/.autotrader/logs/
# audit.log  trader.log
```

The same paths are used when installed via Homebrew; only the install command differs.

## Migration from Development to Installed

If you've been using AutoTrader in development mode and want to migrate to an installed version:

1. Copy your config files:
   ```bash
   cp -r ./config/* ~/.autotrader/config/
   ```

2. Copy your data (if needed):
   ```bash
   cp -r ./data/* ~/.autotrader/data/
   ```

3. Copy your logs (optional):
   ```bash
   cp -r ./logs/* ~/.autotrader/logs/
   ```

## Custom Paths

For advanced use cases, you can pass custom paths to most functions that accept `config_dir` or `data_dir` parameters. However, the CLI commands use the automatic detection described above.
