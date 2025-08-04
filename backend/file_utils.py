import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_vertexai.embeddings import VertexAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./service/service_account.json"

def ask_question(file_path: str, question: str):
    loader = PyPDFLoader(file_path=file_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    embedding_model = VertexAIEmbeddings(
        model_name="gemini-embedding-001",
        location="us-central1"
    )

    vector_store = InMemoryVectorStore(embedding=embedding_model)
    vector_store.add_documents(chunks)

    retriever = vector_store.as_retriever()
    docs = retriever.invoke(question)
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = ChatPromptTemplate.from_messages([
        ("system", "คุณคือผู้ช่วยที่ตอบคำถามจากเนื้อหาในไฟล์"),
        ("human", "คำถาม: {question}, ข้อมูลที่เกี่ยวข้อง: {context}")
    ])

    llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai", temperature=0.8)
    qa_chain = (
        RunnableLambda(lambda x: {"context": context, "question": x})
        | prompt
        | llm
        | StrOutputParser()
    )

    return qa_chain.invoke(question)
