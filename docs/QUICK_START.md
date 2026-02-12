# Quick Start Guide

Get AutoTrader up and running with Claude Desktop or Cursor in **two simple steps**.

## Step 1: Install AutoTrader

### Option A: Homebrew (Recommended for macOS)

```bash
brew install autotrader
```

### Option B: pipx (Cross-platform)

```bash
pipx install -e . --global
```

Verify installation:

```bash
trader status
```

**Note**: Config files are automatically stored in:
- **macOS**: `~/.autotrader/config/`
- **Linux**: `~/.config/autotrader/`
- **Windows**: `%APPDATA%\autotrader\config\`

See [Installation Paths](INSTALLATION_PATHS.md) for details.

## Step 2: Configure MCP Server

### For Claude Desktop

1. Open or create the config file:
   ```bash
   # macOS
   open ~/Library/Application\ Support/Claude/claude_desktop_config.json
   
   # Linux
   nano ~/.config/Claude/claude_desktop_config.json
   ```

2. Add AutoTrader to the MCP servers:

   ```json
   {
     "mcpServers": {
       "AutoTrader": {
         "command": "trader",
         "args": ["mcp", "serve"],
         "env": {
           "ALPACA_API_KEY": "your_paper_trading_key",
           "ALPACA_SECRET_KEY": "your_paper_trading_secret"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** (fully quit and reopen)

### For Cursor

1. Open Cursor settings (Cmd/Ctrl + ,)
2. Navigate to **MCP Servers** or **AI Settings**
3. Add a new MCP server with:
   - **Name**: `AutoTrader`
   - **Command**: `trader`
   - **Args**: `["mcp", "serve"]`
   - **Environment Variables**:
     - `ALPACA_API_KEY`: Your paper trading key
     - `ALPACA_SECRET_KEY`: Your paper trading secret

4. **Restart Cursor**

## Troubleshooting

### "trader" command not found

Claude Desktop and Cursor may not see your shell PATH. Use the **full path** to the `trader` executable:

```bash
# Find the full path
which trader  # macOS/Linux
where trader  # Windows
```

Then use that full path in the config:

```json
{
  "mcpServers": {
    "AutoTrader": {
      "command": "/opt/homebrew/bin/trader",  // Use full path here
      "args": ["mcp", "serve"],
      ...
    }
  }
}
```

### MCP server errors

1. **Check API keys**: Ensure `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` are correct
2. **Check JSON syntax**: No trailing commas, valid JSON
3. **Check logs**: Look for errors in `~/.autotrader/logs/` or `~/autotrader_mcp_debug.log`

### Test installation

Run the installation test script:

```bash
python3 scripts/test_installation.py
```

This verifies:
- ✓ Path resolution works
- ✓ Config can be loaded
- ✓ Strategies can be loaded
- ✓ MCP server can be imported
- ✓ CLI commands work

## Next Steps

Once configured, you can:

1. **Check status**: Ask Claude/Cursor to check your trading account status
2. **View portfolio**: "Show me my portfolio"
3. **Create strategies**: "Create a trailing stop strategy for AAPL"
4. **Run backtests**: "Backtest a bracket strategy for NVDA"
5. **Monitor positions**: "What are my open positions?"

See [Agent Guide](agent-guide.md) for comprehensive usage examples.

## What Gets Stored Where?

When installed via Homebrew/pipx:

- **Config** (`~/.autotrader/config/`):
  - `strategies.yaml` - Your trading strategies
  - `orders.yaml` - Order history
  - `notifications.yaml` - Notification settings

- **Data** (`~/.autotrader/data/`):
  - `backtests/` - Backtest results
  - `optimizations/` - Optimization results
  - `historical/` - Historical price data (if using CSV)
  - `cache/` - Cached market data

- **Logs** (`~/.autotrader/logs/`):
  - `audit.log` - Audit trail of all actions
  - `trader.log` - Application logs

All data persists across package updates!
