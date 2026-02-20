#!/usr/bin/env python3
"""List all MCP tools registered in the BareTrader server.

This script helps verify that all tools are properly registered and can be
used for debugging tool visibility issues in MCP clients.
"""

import asyncio

from trader.mcp.server import _ALL_TOOLS


def main() -> None:
    """List all registered MCP tools."""
    print(f"Total tools registered: {len(_ALL_TOOLS)}\n")

    for tool_fn in sorted(_ALL_TOOLS, key=lambda f: f.__name__):
        name = tool_fn.__name__
        desc = tool_fn.__doc__ or "No description"
        desc_short = desc.split("\n")[0][:80] + "..." if len(desc.split("\n")[0]) > 80 else desc.split("\n")[0]
        print(f"{name}")
        print(f"  {desc_short}")
        print()


if __name__ == "__main__":
    main()
