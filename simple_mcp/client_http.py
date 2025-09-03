"""
Streamable HTTP トランスポート版のシンプルな MCP クライアント。

使い方:
  - 環境変数 MCP_SERVER_URL でサーバURLを指定、または --url 引数で指定。
  - 既定: http://localhost:8000/mcp

例:
  uv run python simple_mcp/client_http.py --url http://localhost:8000/mcp
"""

import asyncio
from typing import Optional

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main(server_url: Optional[str] = None) -> None:
    """Streamable HTTP でサーバに接続し、hello ツールを呼び出す。"""
    url = server_url

    # streamable HTTP で接続
    async with streamablehttp_client(url) as (read_stream, write_stream, _meta):
        # セッションを開始
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # server.py 側の "hello" ツールを呼び出し（引数は client.py と合わせる）
            result = await session.call_tool("hello", {"name": "MCP from HTTP client"})

            # 最低限の出力（必要に応じて整形を追加してください）
            print(f"Tool result: {result}")


if __name__ == "__main__":
    server_url = "http://localhost:8000/mcp"

    asyncio.run(main(server_url))
