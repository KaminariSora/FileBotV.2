from mcp.server.fastmcp import FastMCP
from tools.search_file import search_file
from tools.open_file import open_file

mcp = FastMCP("filebot-agent")

@mcp.tool()
async def search_file_tool(
    content: str,
    search_path: str,
    type: str | None = None
):
    if type is not None and "." not in type:
        type = "." + type

    intent = {
        "content": content,
        "search_path": search_path,
        "type": type
    }
    return search_file(intent)


@mcp.tool()
async def open_file_tool(intent: dict):
    return await open_file(intent)

