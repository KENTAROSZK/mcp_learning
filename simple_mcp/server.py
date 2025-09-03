from mcp.server.fastmcp import FastMCP

mcp = FastMCP("simple_mcp")


@mcp.tool()
async def hello(name: str) -> str:
    return f"hello {name} 1"


if __name__ == "__main__":
    # stdioで通信
    mcp.run(transport="stdio")
