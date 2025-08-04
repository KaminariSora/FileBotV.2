from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import JsonOutputParser
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./service/service_account.json"

llm = init_chat_model(
    "gemini-2.0-flash",
    model_provider="google_genai",
    temperature=0.8
)

# prompt ใช้แยก intent
prompt = ChatPromptTemplate.from_messages([
    ("system", """คุณคือผู้ช่วยที่วิเคราะห์ข้อความผู้ใช้และตอบกลับเป็น JSON 

        ประเภท intent ที่เป็นไปได้:
        - search_file: เมื่อผู้ใช้ต้องการค้นหาไฟล์
        - open_file: เมื่อผู้ใช้ต้องการเปิดไฟล์

        คำที่สื่อถึงการค้นหา: ค้นหา, หา, ต้องการดู, มีไฟล์อะไรบ้าง
        คำที่สื่อถึงการเปิด: เปิด, เปิดไฟล์, แสดงไฟล์

        หากข้อความไม่ชัดเจนให้เลือก search_file

        ตัวอย่าง:
        - "หาไฟล์ pdf" -> search_file
        - "เปิดไฟล์ชื่อ report.pdf" -> open_file
        - "ค้นหาไฟล์ excel ที่ใช้เมื่อ 2 วันก่อน" -> search_file
        - "เปิดไฟล์นี้" -> open_file
        """),
            ("human", "ข้อความ: {message}\nโปรดตอบกลับ JSON เท่านั้น เช่น:\n"
                    '{{{{ "intent": "search_file", "filename": "report", "type": ".pdf", "modified_within_days": 3 }}}}\n'
                    'หรือ {{{{ "intent": "open_file", "filename": "report.pdf", "type": null, "modified_within_days": null }}}}')
])



chain = prompt | llm | JsonOutputParser()

def extract_intent(message: str) -> dict:
    return chain.invoke({"message": message})
