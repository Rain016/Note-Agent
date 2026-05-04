import streamlit as st
from tools.notion_tool import get_notion_client
import os

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

def get_concepts(page_id: str):
    notion = get_notion_client()
    results = notion.blocks.children.list(page_id).get("results", [])
    concepts = []
    for block in results:
        if block["type"] == "toggle":
            title = block["toggle"]["rich_text"]
            if title:
                concepts.append(title[0]["text"]["content"])
    return concepts

st.title("📚 筆記列表")

with st.spinner("載入中..."):
    papers = get_all_papers()

if not papers:
    st.info("還沒有任何筆記，去「存筆記」頁面新增吧！")
else:
    for paper in papers:
        with st.expander(f"📄 {paper['title']}"):
            concepts = get_concepts(paper["id"])
            if not concepts:
                st.write("這篇論文還沒有筆記")
            else:
                for concept in concepts:
                    st.write(f"▶ {concept}")