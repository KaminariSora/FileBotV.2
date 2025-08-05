from langchain.tools import tool
import os
from pathlib import Path
import os
from langchain.chat_models import init_chat_model


@tool(description="Search for files based on user intent dictionary.")
def search_file(
    content: str,
    search_path: str,
    type: str = None
):
    search_dir = Path(search_path)
    results = []

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./service/service_account.json"

    llm = init_chat_model(
        "gemini-2.0-flash",
        model_provider="google_genai",
        temperature=0.8
    )

    def chunk_text(text, chunk_size=2000):
        for i in range(0, len(text), chunk_size):
            yield text[i:i+chunk_size]

    for file_path in search_dir.rglob("*"):
        if not file_path.is_file():
            continue

        # Filter by file type
        if type and not file_path.name.lower().endswith(type.lower()):
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                file_content = f.read()
        except Exception:
            continue

        # Split file content into chunks
        matched = False
        for chunk in chunk_text(file_content):
            prompt = f"Does the following file content relate to '{content}'? Answer yes or no.\n\n{chunk}"
            response = llm.invoke(prompt)
            response_text = response.content.strip().lower()
            if "yes" in response_text:
                results.append(str(file_path))
                matched = True
                break  # Stop checking more chunks for this file

    if results:
        return f"พบทั้งหมด {len(results)} ไฟล์ที่ตรงกับเนื้อหา:\n" + "\n".join(results)
    else:
        return "ไม่พบไฟล์ที่ตรงกับเนื้อหา"