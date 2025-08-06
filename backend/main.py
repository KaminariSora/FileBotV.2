import asyncio
from mcp_layer import mcp
from intent_engine import extract_intent

async def route_intent(intent: dict):
    """แมป intent เป็นฟังก์ชันใน mcp_layer"""
    intent_type = intent.get("intent")
    if intent_type == "search_file":
        print(f"Routing to: {intent_type}")

        content = input(">>> Content searching: ")
        if content.strip().lower() in["e", "q"]:
            return "cancel searching..."

        search_path = r"D:\Working\C_work\Coding\FileBotV.2\TestData"
        file_type = input("📁 ระบุประเภทไฟล์ (เช่น .pdf หรือเว้นไว้): ") or None
        # file_type = "pdf"

        params = {
            "content": content,
            "search_path": search_path,
            "type": file_type
        }

        result = await mcp.call_tool("search_file_tool", params)
        if isinstance(result, list) and hasattr(result[0], "text"):
            return result[0].text
        else:
            return str(result)
    else:
        return "ขออภัย ฉันไม่เข้าใจคำสั่งนี้"

async def main():
    print("📦 FileBot CLI (MCP Simulation)")
    while True:
        message = input(">>> User: ")
        if message.strip().lower() in ["exit", "quit", "q", "e"]:
            print("exiting program...")
            break
        intent = extract_intent(message)
        print("Intent:", intent)

        response = await route_intent(intent)
        print(">>> Bot:", response)

if __name__ == "__main__":
    asyncio.run(main())
