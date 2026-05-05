import streamlit as st
from tools.notion_tool import get_notion_client, delete_concept_from_notion, delete_paper_page
from tools.pinecone_tool import get_index, get_embeddings
import os
import hashlib

def get_all_papers():
    notion = get_notion_client()
    parent_id = os.getenv("NOTION_PAGE_ID")
    results = notion.blocks.children.list(parent_id).get("results", [])
    papers = []
    for block in results:
        if block["type"] == "child_page":
            papers.append({
                "id": block["id"],
                "title": block["child_page"]["title"]
            })
    return papers

def get_concepts_with_content(page_id: str):
    notion = get_notion_client()
    blocks = notion.blocks.children.list(page_id).get("results", [])
    concepts = []
    for block in blocks:
        if block["type"] == "toggle":
            title = block["toggle"]["rich_text"]
            if not title:
                continue
            concept_name = title[0]["text"]["content"]
            
            children = notion.blocks.children.list(block["id"]).get("results", [])
            content = {"核心重點": [], "我的理解": "", "相關概念": []}
            
            for child in children:
                if child["type"] == "toggle":
                    child_title = child["toggle"]["rich_text"]
                    if not child_title:
                        continue
                    section = child_title[0]["text"]["content"]
                    grandchildren = notion.blocks.children.list(child["id"]).get("results", [])
                    
                    if section == "核心重點":
                        for gc in grandchildren:
                            if gc["type"] == "bulleted_list_item":
                                rt = gc["bulleted_list_item"]["rich_text"]
                                if rt:
                                    content["核心重點"].append(rt[0].get("text", {}).get("content", "") or rt[0].get("equation", {}).get("expression", ""))
                    
                    elif section == "我的理解":
                        texts = []
                        for gc in grandchildren:
                            if gc["type"] == "paragraph":
                                rt = gc["paragraph"]["rich_text"]
                                if rt:
                                    texts.append(rt[0]["text"]["content"])
                            elif gc["type"] == "equation":
                                texts.append(f"$${gc['equation']['expression']}$$")
                        content["我的理解"] = "\n".join(texts)
                    
                    elif section == "相關概念":
                        for gc in grandchildren:
                            if gc["type"] == "bulleted_list_item":
                                rt = gc["bulleted_list_item"]["rich_text"]
                                if rt:
                                    content["相關概念"].append(rt[0]["text"]["content"])
            
            concepts.append({
                "id": block["id"],
                "name": concept_name,
                "content": content
            })
    return concepts

def delete_from_pinecone(paper_title: str, concept: str):
    index = get_index()
    vector_id = hashlib.md5(f"{paper_title}_{concept}".encode()).hexdigest()
    index.delete(ids=[vector_id])

def sync_notion_to_pinecone(paper_title: str, concepts: list):
    index = get_index()
    embeddings = get_embeddings()
    for concept in concepts:
        c = concept["content"]
        content = f"""
論文：{paper_title}
概念：{concept['name']}
重點：{' '.join(c['核心重點'])}
理解：{c['我的理解']}
相關：{'、'.join(c['相關概念'])}
"""
        vector = embeddings.embed_query(content)
        index.upsert(vectors=[{
            "id": hashlib.md5(f"{paper_title}_{concept['name']}".encode()).hexdigest(),
            "values": vector,
            "metadata": {
                "paper_title": paper_title,
                "concept": concept["name"],
                "content": content
            }
        }])

st.title("📚 筆記列表")

with st.spinner("載入中..."):
    papers = get_all_papers()

if not papers:
    st.info("還沒有任何筆記，去「存筆記」頁面新增吧！")
else:
    for paper in papers:
        col1, col2 = st.columns([5, 1])
        with col1:
            with st.expander(f"📄 {paper['title']}"):
                with st.spinner("載入概念..."):
                    concepts = get_concepts_with_content(paper["id"])
                
                if not concepts:
                    st.write("這篇論文還沒有筆記")
                else:
                    for concept in concepts:
                        with st.expander(f"▶ {concept['name']}"):
                            c = concept["content"]
                            
                            if c["核心重點"]:
                                st.write("**核心重點**")
                                for point in c["核心重點"]:
                                    st.write(f"- {point}")
                            
                            if c["我的理解"]:
                                st.write("**我的理解**")
                                st.write(c["我的理解"])
                            
                            if c["相關概念"]:
                                st.write("**相關概念**")
                                st.write("、".join(c["相關概念"]))
                            
                            if st.button("🗑️ 刪除這個概念", key=f"del_{concept['id']}"):
                                with st.spinner("刪除中..."):
                                    delete_concept_from_notion(paper["id"], concept["name"])
                                    delete_from_pinecone(paper["title"], concept["name"])
                                st.success(f"已刪除：{concept['name']}")
                                st.rerun()
        with col2:
            if st.button("🗑️ 刪除整篇", key=f"del_paper_{paper['id']}"):
                with st.spinner("刪除中..."):
                    concepts = get_concepts_with_content(paper["id"])
                    for concept in concepts:
                        delete_from_pinecone(paper["title"], concept["name"])
                    delete_paper_page(paper["id"])
                st.success(f"已刪除整篇：{paper['title']}")
                st.rerun()
            
            if st.button("🔄 同步", key=f"sync_{paper['id']}"):
                with st.spinner("同步中..."):
                    concepts = get_concepts_with_content(paper["id"])
                    sync_notion_to_pinecone(paper["title"], concepts)
                st.success(f"已同步：{paper['title']}")