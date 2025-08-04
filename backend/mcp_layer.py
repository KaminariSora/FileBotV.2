from mcp.server.fastmcp import FastMCP
from tools.search_file import search_file
from tools.open_file import open_file

mcp = FastMCP("filebot-agent")

@mcp.tool()
async def search_file_tool(
    filename: str,
    search_path: str,
    type: str | None = None,
    modified_within_days: int | None = None
):
    intent = {
        "filename": filename,
        "search_path": search_path
    }
    if type is not None:
        intent["type"] = type
    if modified_within_days is not None:
        intent["modified_within_days"] = modified_within_days
    return search_file(intent)


@mcp.tool()
async def open_file_tool(intent: dict):
    return await open_file(intent)

