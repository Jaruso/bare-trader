# Installation Workflow Summary

## Overview

AutoTrader can be installed and configured for use with Claude Desktop or Cursor in **two simple steps**:

1. **Install the CLI tool** (Homebrew or pipx)
2. **Configure the MCP server** (add to Claude Desktop/Cursor config)

## Step-by-Step

### Step 1: Install AutoTrader

**Option A: Homebrew (macOS)**
```bash
brew install autotrader
```

**Option B: pipx (Cross-platform)**
```bash
pipx install -e . --global
```

**Verify installation:**
```bash
trader status
```

### Step 2: Configure MCP Server

**For Claude Desktop:**

1. Open config file:
   ```bash
   # macOS
   open ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Add AutoTrader configuration:
   ```json
   {
     "mcpServers": {
       "AutoTrader": {
         "command": "trader",
         "args": ["mcp", "serve"],
         "env": {
           "ALPACA_API_KEY": "your_paper_key",
           "ALPACA_SECRET_KEY": "your_paper_secret"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** (fully quit and reopen)

**For Cursor:**

1. Open Settings (Cmd/Ctrl + ,)
2. Navigate to **MCP Servers**
3. Add new server:
   - **Name**: `AutoTrader`
   - **Command**: `trader`
   - **Args**: `["mcp", "serve"]`
   - **Environment**: Add `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`

4. **Restart Cursor**

## What Happens Behind the Scenes

### Path Resolution

When AutoTrader is installed via Homebrew/pipx, it automatically detects that it's running in **installed mode** (not development) and uses user directories:

- **macOS**: `~/.autotrader/config/`, `~/.autotrader/data/`, `~/.autotrader/logs/`
- **Linux**: `~/.config/autotrader/`, `~/.local/share/autotrader/`, `~/.local/state/autotrader/`
- **Windows**: `%APPDATA%\autotrader\` or `~/.autotrader/`

These directories are created automatically on first use.

### MCP Server Startup

When Claude Desktop or Cursor starts, it:
1. Spawns the `trader mcp serve` command
2. Communicates via stdio (standard input/output)
3. AutoTrader exposes 31 MCP tools for trading operations

The MCP server runs as a subprocess and handles all tool calls from the AI agent.

## Testing Installation

Run the installation test script:

```bash
# After installation
python3 scripts/test_installation.py

# Or in development mode
poetry run python scripts/test_installation.py
```

This verifies:
- ✓ Path resolution works correctly
- ✓ Config can be loaded
- ✓ Strategies can be loaded
- ✓ MCP server can be imported
- ✓ CLI commands work

## Troubleshooting

### "trader" command not found

Claude Desktop/Cursor may not see your shell PATH. Use the **full path**:

```bash
which trader  # Find the path
```

Then use that full path in the config:
```json
{
  "mcpServers": {
    "AutoTrader": {
      "command": "/opt/homebrew/bin/trader",  // Full path here
      ...
    }
  }
}
```

### MCP server errors

1. Check API keys are correct
2. Check JSON syntax (no trailing commas)
3. Check logs: `~/.autotrader/logs/` or `~/autotrader_mcp_debug.log`

### Config files location

After installation, config files are stored in user directories (not in the package installation directory). This ensures:
- Data persists across package updates
- Multiple users can have separate configs
- Files are writable by the user

See [Installation Paths](INSTALLATION_PATHS.md) for complete details.

## Next Steps

Once configured, you can:

- **Check status**: "What's my trading account status?"
- **View portfolio**: "Show me my portfolio"
- **Create strategies**: "Create a trailing stop strategy for AAPL"
- **Run backtests**: "Backtest a bracket strategy for NVDA"
- **Monitor positions**: "What are my open positions?"

See [Agent Guide](agent-guide.md) for comprehensive usage examples.
