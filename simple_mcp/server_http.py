"""
Streamable HTTP で FastMCP サーバを起動する専用スクリプト。

環境変数でホストやポートを上書き可能:
  - MCP_HOST (例: 0.0.0.0)
  - MCP_PORT (例: 8000)
  - MCP_HTTP_PATH (例: "/mcp")

例:
  MCP_HOST=0.0.0.0 MCP_PORT=8000 uv run python simple_mcp/server_http.py
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("simple_mcp_http")


def _configure_from_env() -> None:
    host = "0.0.0.0"
    port = "8000"
    path = "/mcp"

    if host:
        mcp.settings.host = host
    if port:
        try:
            mcp.settings.port = int(port)
        except ValueError:
            pass
    if path:
        mcp.settings.streamable_http_path = path


@mcp.tool()
async def hello(name: str) -> str:
    return f"hello {name} 1"


if __name__ == "__main__":
    _configure_from_env()
    mcp.run(transport="streamable-http")
