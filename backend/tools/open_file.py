from file_utils import ask_question

async def open_file(intent: dict) -> dict:
    filename = intent.get("filename")
    file_path = f"./files/{filename}"
    answer = ask_question(file_path, "ช่วยสรุปไฟล์ให้หน่อย")
    return {"answer": answer}
