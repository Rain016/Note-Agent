import os
import hashlib
from langchain_core.tools import tool

def get_index():
    from pinecone import Pinecone, ServerlessSpec
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    INDEX_NAME = "paper-notes"
    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(INDEX_NAME)

def get_embeddings():
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(model="text-embedding-3-small")

@tool
def save_to_pinecone_tool(paper_title: str, concept: str, key_points: list, my_understanding: str, related_concepts: list) -> str:
    """把整理好的筆記存到 Pinecone 向量資料庫，讓之後可以語意搜尋。"""
    index = get_index()
    embeddings = get_embeddings()
    
    content = f"""
論文：{paper_title}
概念：{concept}
重點：{' '.join(key_points)}
理解：{my_understanding}
相關：{' '.join(related_concepts)}
"""
    vector = embeddings.embed_query(content)
    index.upsert(vectors=[{
        "id": hashlib.md5(f"{paper_title}_{concept}".encode()).hexdigest(),
        "values": vector,
        "metadata": {
            "paper_title": paper_title,
            "concept": concept,
            "content": content
        }
    }])
    return f"筆記已存到 Pinecone：{paper_title} → {concept}"

@tool
def search_notes_tool(query: str) -> str:
    """用自然語言搜尋過去的筆記。輸入是你想查詢的問題或關鍵字。"""
    index = get_index()
    embeddings = get_embeddings()
    
    vector = embeddings.embed_query(query)
    results = index.query(vector=vector, top_k=3, include_metadata=True)
    
    if not results["matches"]:
        return "找不到相關筆記"
    
    output = "找到以下相關筆記：\n\n"
    for match in results["matches"]:
        meta = match["metadata"]
        output += f"論文：{meta['paper_title']}\n"
        output += f"概念：{meta['concept']}\n"
        output += f"內容：{meta['content']}\n"
        output += "---\n"
    
    return output