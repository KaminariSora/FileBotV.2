from langchain.tools import tool
import os
import fnmatch
from datetime import datetime, timedelta
from pathlib import Path
# from langchain_mcp.server.fastmcp import FastMCP

@tool(description="Search for files based on user intent dictionary.")
def search_file(filename: str, type: str = None, modified_within_days: int = None, search_path: str = ".") -> str:
    search_dir = Path(search_path)
    results = []
    now = datetime.now()

    for file_path in search_dir.rglob("*"):
        if not file_path.is_file():
            continue

        # Filter by file type
        if type and not file_path.name.lower().endswith(type.lower()):
            continue

        # Filter by filename (partial match)
        if filename and filename.lower() not in file_path.name.lower():
            continue

        # Filter by modified date
        if modified_within_days is not None:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if now - mtime > timedelta(days=modified_within_days):
                continue

        results.append(str(file_path))
    if results:
        return f"พบทั้งหมด {len(results)} ไฟล์ที่ตรงกับเงื่อนไข:\n" + "\n".join(results)
    else:
        print("searching in path: ",search_path)
        return "ไม่พบไฟล์ที่ตรงกับเงื่อนไข"
