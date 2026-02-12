# Path Resolution Fix for Homebrew/pipx Installation

## Problem

When AutoTrader is installed via Homebrew or pipx, the code was using relative paths (`Path(__file__).parent.parent.parent / "config"`) which would place config files inside the package installation directory. This is problematic because:

1. **Package directories are read-only** - Homebrew installs packages in protected directories
2. **Data loss on updates** - Package updates would wipe user data
3. **Not user-writable** - Users can't modify files in system package directories
4. **Wrong location** - User data should be in user directories, not system directories

## Solution

Created a centralized path resolution system (`trader/utils/paths.py`) that:

1. **Detects development vs installed mode** - Checks if running from project directory
2. **Uses appropriate directories**:
   - **Development**: `./config/`, `./data/`, `./logs/` (relative to project root)
   - **Installed (macOS)**: `~/.autotrader/config/`, `~/.autotrader/data/`, `~/.autotrader/logs/`
   - **Installed (Linux)**: Follows XDG Base Directory spec (`~/.config/autotrader/`, etc.)
   - **Installed (Windows)**: `%APPDATA%\autotrader\` or `~/.autotrader/`

## Changes Made

### New File: `trader/utils/paths.py`

Centralized path resolution functions:
- `get_config_dir()` - Returns config directory path
- `get_data_dir()` - Returns data directory path  
- `get_log_dir()` - Returns log directory path
- `get_project_root()` - Returns project root (for dev mode detection)

### Updated Files

1. **`trader/utils/config.py`**
   - Updated `load_config()` to use `get_data_dir()` and `get_log_dir()` for installed mode
   - Detects dev mode and uses project directories when appropriate

2. **`trader/strategies/loader.py`**
   - Updated `get_strategies_file()` to use `get_config_dir()`

3. **`trader/core/engine.py`**
   - Updated `get_lock_file_path()` to use `get_config_dir()`

4. **`trader/oms/store.py`**
   - Updated `get_orders_file()` to use `get_config_dir()`

5. **`trader/app/notifications.py`**
   - Updated `_config_dir()` to use `get_config_dir()`

6. **`trader/backtest/store.py`**
   - Updated `get_backtests_dir()` to use `get_data_dir()`

7. **`trader/optimization/store.py`**
   - Updated `get_optimizations_dir()` to use `get_data_dir()`

8. **`trader/cli/main.py`**
   - Fixed notification commands to use `get_config_dir()` instead of `config.data_dir.parent / "config"`

## Detection Logic

The system detects development mode by checking if:
1. `config/strategies.yaml` exists relative to the code location, OR
2. `pyproject.toml` exists relative to the code location

If neither exists, it assumes installed mode and uses user directories.

## Testing

To test the path resolution:

```python
from trader.utils.paths import get_config_dir, get_data_dir, get_log_dir

# In development mode (from project root):
print(get_config_dir())  # /path/to/auto-trader/config
print(get_data_dir())    # /path/to/auto-trader/data
print(get_log_dir())     # /path/to/auto-trader/logs

# In installed mode (when installed via Homebrew/pipx):
print(get_config_dir())  # ~/.autotrader/config (macOS)
print(get_data_dir())    # ~/.autotrader/data (macOS)
print(get_log_dir())     # ~/.autotrader/logs (macOS)
```

## User Impact

### Before Fix
- Config files would try to be created in package directory (would fail)
- User data would be lost on package updates
- No way to persist strategies/orders when installed

### After Fix
- Config files stored in user directory (`~/.autotrader/config/`)
- Data persists across package updates
- Strategies, orders, backtests all stored in user-accessible locations
- Works seamlessly in both development and installed modes

## Migration

Users upgrading from a version that tried to use package directories will automatically get the correct paths on first run. The directories are created automatically if they don't exist.

## Documentation

See `docs/INSTALLATION_PATHS.md` for complete documentation on:
- Where files are stored in each mode
- Platform-specific paths
- Environment variable overrides
- Migration guide from development to installed mode
