from langchain.tools import tool
import os
from pathlib import Path
from typing import List
from langchain.chat_models import init_chat_model
from langchain_google_vertexai.embeddings import VertexAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader

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

    embedding_model = VertexAIEmbeddings(
        model_name="gemini-embedding-001",
        location="us-central1"
    )

    def chunk_text(text, chunk_size=2000):
        for i in range(0, len(text), chunk_size):
            yield text[i:i+chunk_size]

    def is_readable_file(file_path):
        readable_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json',
                              '.xml', '.csv', '.log', '.sql', '.yml', '.yaml', '.ini',
                              '.conf', '.properties', '.sh', '.bat', '.dockerfile'}
        return file_path.suffix.lower() in readable_extensions

    def get_file_encoding(file_path):
        encodings = ['utf-8', 'utf-8-sig', 'cp874', 'windows-1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(100)
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        return None

    def chunk_lines(lines: List[str], chunk_size: int = 5) -> List[str]:
        chunks = []
        for i in range(0, len(lines), chunk_size):
            chunk = "\n".join(lines[i:i+chunk_size])
            chunks.append(chunk)
        return chunks

    def build_vector_store_from_text(text: str):
        lines = text.split("\n")
        chunks = chunk_lines(lines, chunk_size=5)
        docs = [Document(page_content=chunk) for chunk in chunks]
        vector_store = FAISS.from_documents(docs, embedding_model)
        return vector_store

    def extract_relevant_content(vector_store, user_content: str, max_context: int = 1000):
        results = vector_store.similarity_search(user_content, k=3)
        combined = "\n...\n".join([doc.page_content for doc in results])
        return combined[:max_context] + "..." if len(combined) > max_context else combined

    for file_path in search_dir.rglob("*"):
        if not file_path.is_file():
            continue

        if type and not file_path.name.lower().endswith(type.lower()):
            continue

        try:
            if file_path.suffix.lower() == ".pdf":
                loader = PyPDFLoader(str(file_path))
                docs = loader.load()
                file_content = "\n".join(doc.page_content for doc in docs)
            else:
                if not is_readable_file(file_path):
                    continue

                encoding = get_file_encoding(file_path)
                if not encoding:
                    continue

                with open(file_path, "r", encoding=encoding) as f:
                    file_content = f.read()

            vector_store = build_vector_store_from_text(file_content)
            relevant_content = extract_relevant_content(vector_store, content)

            for chunk in chunk_text(relevant_content):
                if not chunk.strip():
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
                        break

                except Exception as e:
                    print(f"Error processing chunk from {file_path}: {e}")
                    continue

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            continue

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
