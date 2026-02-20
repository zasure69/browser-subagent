"""
Entry point for `python -m browser_mcp_server`.
Starts the MCP server with stdio transport.
"""

from .server import run

if __name__ == "__main__":
    run()
