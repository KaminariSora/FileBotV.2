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
) -> str:
    search_dir = Path(search_path)
    results = []

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./service/service_account.json"

    llm = init_chat_model(
        "gemini-2.0-flash",
        model_provider="google_genai",
        temperature=0.8
    )

    def chunk_text(text, chunk_size=2000):
        """แบ่งข้อความเป็นชิ้นๆ เพื่อประมวลผล"""
        for i in range(0, len(text), chunk_size):
            yield text[i:i+chunk_size]

    def is_readable_file(file_path):
        """ตรวจสอบว่าไฟล์สามารถอ่านได้หรือไม่"""
        readable_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', 
                              '.xml', '.csv', '.log', '.sql', '.yml', '.yaml', '.ini', 
                              '.conf', '.properties', '.sh', '.bat', '.dockerfile'}
        return file_path.suffix.lower() in readable_extensions

    def get_file_encoding(file_path):
        """ตรวจสอบ encoding ของไฟล์"""
        encodings = ['utf-8', 'utf-8-sig', 'cp874', 'windows-1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(100)
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        return None

    def extract_relevant_content(file_content, user_content, max_context=1000):
        """แยกเนื้อหาที่เกี่ยวข้องจากไฟล์"""
        lines = file_content.split('\n')
        relevant_sections = []
        
        # ค้นหาบรรทัดที่มีคำสำคัญ
        keywords = user_content.lower().split()
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords):
                # เอาบริบทรอบๆ บรรทัดที่พบ
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                context = '\n'.join(lines[start:end])
                relevant_sections.append(context)
        
        # รวมส่วนที่เกี่ยวข้องและจำกัดความยาว
        combined = '\n...\n'.join(relevant_sections[:3])  # เอาแค่ 3 ส่วนแรก
        if len(combined) > max_context:
            combined = combined[:max_context] + "..."
        
        return combined if combined else file_content[:max_context]

    # ค้นหาไฟล์ในโฟลเดอร์
    for file_path in search_dir.rglob("*"):
        if not file_path.is_file():
            continue

        # กรองตามประเภทไฟล์ที่ระบุ
        if type and not file_path.name.lower().endswith(type.lower()):
            continue

        # ตรวจสอบว่าเป็นไฟล์ที่อ่านได้หรือไม่
        if not is_readable_file(file_path):
            continue

        try:
            # หา encoding ที่เหมาะสม
            encoding = get_file_encoding(file_path)
            if not encoding:
                continue

            # อ่านไฟล์
            with open(file_path, "r", encoding=encoding) as f:
                file_content = f.read()

            # ถ้าไฟล์ใหญ่เกินไป ให้แยกเนื้อหาที่เกี่ยวข้องก่อน
            if len(file_content) > 5000:
                relevant_content = extract_relevant_content(file_content, content)
            else:
                relevant_content = file_content

            # แบ่งเนื้อหาเป็นชิ้นๆ และตรวจสอบความเกี่ยวข้อง
            matched = False
            for chunk in chunk_text(relevant_content):
                if not chunk.strip():  # ข้าม chunk ว่าง
                    continue
                    
                prompt = f"""วิเคราะห์ว่าเนื้อหาไฟล์ต่อไปนี้เกี่ยวข้องกับ '{content}' หรือไม่
                
                    เนื้อหาไฟล์:
                    {chunk}

                    ตอบ 'yes' ถ้าเกี่ยวข้อง หรือ 'no' ถ้าไม่เกี่ยวข้อง พร้อมเหตุผลสั้นๆ"""

                try:
                    response = llm.invoke(prompt)
                    response_text = response.content.strip().lower()
                    
                    if "yes" in response_text:
                        results.append({
                            'file_path': str(file_path),
                            'file_name': file_path.name,
                            'file_size': file_path.stat().st_size,
                            'matched_content': chunk[:200] + "..." if len(chunk) > 200 else chunk
                        })
                        matched = True
                        break  # หยุดตรวจสอบ chunk อื่นของไฟล์นี้
                        
                except Exception as e:
                    print(f"Error processing chunk from {file_path}: {e}")
                    continue

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            continue

    # จัดรูปแบบผลลัพธ์
    if results:
        response_text = f"พบทั้งหมด {len(results)} ไฟล์ที่เกี่ยวข้องกับ '{content}':\n\n"
        
        for i, result in enumerate(results, 1):
            file_size_kb = result['file_size'] / 1024
            response_text += f"{i}. {result['file_name']}\n"
            response_text += f"   📁 Path: {result['file_path']}\n"
            response_text += f"   📊 Size: {file_size_kb:.1f} KB\n"
            response_text += f"   📄 Preview: \n{result['matched_content']}\n\n"
        
        return response_text
    else:
        return f"ไม่พบไฟล์ที่เกี่ยวข้องกับ '{content}' ในโฟลเดอร์ {search_path}"