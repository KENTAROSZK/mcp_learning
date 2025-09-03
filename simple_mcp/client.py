# client.py
import asyncio

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    # # サーバスクリプトをpythonで起動
    server_params = StdioServerParameters(
        # NOTE: 親プロセス（クライアント）をuv仮想環境で起動すれば、子プロセス（サーバー）も同じ環境で実行される
        # client.pyをuv経由で実行（uv run python client.py）している場合は、このコマンドもuv仮想環境下で実行される
        command="python",
        args=["./simple_mcp/server.py"],
    )

    # async withを使ってstdio_clientを起動・管理
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialise the connection
            await session.initialize()

            # call the tool: hello
            result = await session.call_tool("hello", {"name": "MCP from client"})

            print(f"Tool result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
