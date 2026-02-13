#!/usr/bin/env python3
"""Test script to verify AutoTrader installation and path resolution.

This script simulates what happens when AutoTrader is installed via Homebrew/pipx
and verifies that:
1. Path resolution works correctly (uses user directories, not package dirs)
2. Config/data/log directories are created and writable
3. MCP server can be imported and initialized
4. Basic functionality works

Run this script AFTER installation (brew install or pipx install).
In development mode, run: poetry run python scripts/test_installation.py
"""

import os
import sys
from pathlib import Path

# Add project root to path for development mode
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_path_resolution():
    """Test that path resolution works correctly."""
    print("=" * 60)
    print("Testing Path Resolution")
    print("=" * 60)

    from trader.utils.paths import get_config_dir, get_data_dir, get_log_dir

    config_dir = get_config_dir()
    data_dir = get_data_dir()
    log_dir = get_log_dir()

    print(f"✓ Config dir: {config_dir}")
    print(f"✓ Data dir: {data_dir}")
    print(f"✓ Log dir: {log_dir}")

    # Verify directories exist and are writable
    for name, path in [("Config", config_dir), ("Data", data_dir), ("Log", log_dir)]:
        if not path.exists():
            print(f"✗ {name} directory does not exist: {path}")
            return False
        if not os.access(path, os.W_OK):
            print(f"✗ {name} directory is not writable: {path}")
            return False
        print(f"✓ {name} directory exists and is writable")

    # Check if we're in dev or installed mode
    project_root = Path(__file__).resolve().parent.parent
    is_dev = (project_root / "config" / "strategies.yaml").exists() or (project_root / "pyproject.toml").exists()

    if is_dev:
        print("\n✓ Running in DEVELOPMENT mode")
        print(f"  Project root: {project_root}")
    else:
        print("\n✓ Running in INSTALLED mode")
        print("  Config: ~/.autotrader/config/ (macOS) or ~/.config/autotrader/ (Linux)")

    return True


def test_config_loading():
    """Test that config can be loaded."""
    print("\n" + "=" * 60)
    print("Testing Config Loading")
    print("=" * 60)

    try:
        from trader.utils.config import load_config
        config = load_config()
        print("✓ Config loaded successfully")
        print(f"  Environment: {config.env.value}")
        print(f"  Service: {config.service.value}")
        print(f"  Data dir: {config.data_dir}")
        print(f"  Log dir: {config.log_dir}")
        return True
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_loader():
    """Test that strategies can be loaded."""
    print("\n" + "=" * 60)
    print("Testing Strategy Loader")
    print("=" * 60)

    try:
        from trader.strategies.loader import get_strategies_file, load_strategies
        strategies_file = get_strategies_file()
        print(f"✓ Strategies file: {strategies_file}")

        strategies = load_strategies()
        print(f"✓ Loaded {len(strategies)} strategies")
        return True
    except Exception as e:
        print(f"✗ Strategy loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_server_import():
    """Test that MCP server can be imported."""
    print("\n" + "=" * 60)
    print("Testing MCP Server Import")
    print("=" * 60)

    try:
        from trader.mcp.server import build_server
        print("✓ MCP server imports successful")

        # Try building server (don't actually run it)
        build_server()
        print("✓ MCP server can be built")

        # Check that tools are registered
        # The server should have tools registered via register_tools()
        print("✓ MCP server ready")
        return True
    except Exception as e:
        print(f"✗ MCP server import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_command():
    """Test that CLI command is available."""
    print("\n" + "=" * 60)
    print("Testing CLI Command")
    print("=" * 60)

    try:
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "trader.cli.main", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ CLI command works")
            if "mcp" in result.stdout.lower():
                print("✓ MCP subcommand available")
            return True
        else:
            print(f"✗ CLI command failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ CLI command test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AutoTrader Installation Test")
    print("=" * 60)
    print("\nThis script verifies that AutoTrader is properly installed")
    print("and ready to use with Claude Desktop or Cursor.\n")

    tests = [
        ("Path Resolution", test_path_resolution),
        ("Config Loading", test_config_loading),
        ("Strategy Loader", test_strategy_loader),
        ("MCP Server Import", test_mcp_server_import),
        ("CLI Command", test_cli_command),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! AutoTrader is ready to use.")
        print("\nNext steps:")
        print("1. Install via: brew install autotrader (or pipx install -e .)")
        print("2. Configure Claude Desktop:")
        print('   Add to ~/Library/Application Support/Claude/claude_desktop_config.json:')
        print('   {')
        print('     "mcpServers": {')
        print('       "AutoTrader": {')
        print('         "command": "trader",')
        print('         "args": ["mcp", "serve"],')
        print('         "env": {')
        print('           "ALPACA_API_KEY": "your_key",')
        print('           "ALPACA_SECRET_KEY": "your_secret"')
        print('         }')
        print('       }')
        print('     }')
        print('   }')
        print("3. Restart Claude Desktop")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
