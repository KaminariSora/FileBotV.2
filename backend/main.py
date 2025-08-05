import asyncio
from mcp_layer import mcp
from intent_engine import extract_intent

async def route_intent(intent: dict):
    """แมป intent เป็นฟังก์ชันใน mcp_layer"""
    intent_type = intent.get("intent")
    if intent_type == "search_file":
        print(f"🧭 Routing to: {intent_type}")

        content = input("Content searching: ")
        search_path = r"D:\Working\C_work\Coding\FileBotV.2\TestData"
        file_type = input("📁 ระบุประเภทไฟล์ (เช่น .pdf หรือเว้นไว้): ") or None

        params = {
            "content": content,
            "search_path": search_path,
            "type": file_type
        }

        # filename = input("🔎 ใส่ชื่อไฟล์ที่ต้องการค้นหา (เช่น *.txt): ")
        # file_type = input("📁 ระบุประเภทไฟล์ (เช่น .pdf หรือเว้นไว้): ") or None
        # days = input("⏱ แก้ไขภายในกี่วัน (หรือเว้นไว้): ")
        # modified_within_days = int(days) if days else None
        # search_path = input("📂 โฟลเดอร์ที่ต้องการค้นหา (default = .): ") or "."
        
        # params = {
        #     "filename": filename,
        #     "file_type": file_type,
        #     "modified_within_days": modified_within_days,
        #     "search_path": search_path
        # }
        result = await mcp.call_tool("search_file_tool", params)
        return result
    else:
        print(intent)
        return "ขออภัย ฉันไม่เข้าใจคำสั่งนี้"

async def main():
    print("📦 FileBot CLI (MCP Simulation)")
    while True:
        message = input("👤 User: ")
        if message.strip().lower() in ["exit", "quit", "q", "e"]:
            break
        intent = extract_intent(message)
        print("🧠 Intent:", intent)

        response = await route_intent(intent)
        print("🤖 Bot:", response)

if __name__ == "__main__":
    asyncio.run(main())  # ✅ รัน async main
