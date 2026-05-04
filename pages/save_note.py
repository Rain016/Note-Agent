import streamlit as st
from tools.organize import organize_note_internal
from tools.notion_tool import get_or_create_paper_page, concept_exists, create_toggle_block
from tools.pinecone_tool import get_index, get_embeddings
import hashlib

def save_to_pinecone(note: dict):
    index = get_index()
    embeddings = get_embeddings()
    content = f"""
論文：{note['paper_title']}
概念：{note['concept']}
重點：{' '.join(note['key_points'])}
理解：{note['my_understanding']}
相關：{' '.join(note['related_concepts'])}
"""
    vector = embeddings.embed_query(content)
    index.upsert(vectors=[{
        "id": hashlib.md5(f"{note['paper_title']}_{note['concept']}".encode()).hexdigest(),
        "values": vector,
        "metadata": {
            "paper_title": note["paper_title"],
            "concept": note["concept"],
            "content": content
        }
    }])

st.title("✏️ 存筆記")

# 輸入論文名稱
paper_title = st.text_input("論文名稱", placeholder="例如：Diffusion Policy")

# 輸入概念名稱
concept_name = st.text_input("概念名稱", placeholder="例如：Forward Process")

# 上傳 markdown 檔
uploaded_file = st.file_uploader("上傳對話 markdown 檔", type=["md"])

if uploaded_file and paper_title and concept_name:
    chat_content = uploaded_file.read().decode("utf-8")
    
    st.subheader("對話預覽")
    with st.expander("點開查看對話內容"):
        st.text(chat_content)
    
    if st.button("整理筆記", type="primary"):
        with st.spinner("整理中..."):
            note = organize_note_internal(chat_content)
            note["paper_title"] = paper_title
            note["concept"] = concept_name
        
        st.subheader("整理結果")
        st.write(f"**概念**：{note['concept']}")
        
        st.write("**核心重點**：")
        for point in note["key_points"]:
            st.write(f"- {point}")
        
        st.write(f"**我的理解**：{note['my_understanding']}")
        st.write(f"**相關概念**：{', '.join(note['related_concepts'])}")
        
        st.session_state["current_note"] = note

if "current_note" in st.session_state:
    note = st.session_state["current_note"]
    
    if st.button("確認儲存到 Notion + Pinecone", type="primary"):
        with st.spinner("儲存中..."):
            page_id = get_or_create_paper_page(note["paper_title"])
            
            if concept_exists(page_id, note["concept"]):
                st.warning(f"這個概念已經存在：{note['concept']}，跳過 Notion 儲存")
            else:
                create_toggle_block(page_id, note)
                st.success("✅ 已存到 Notion！")
            
            save_to_pinecone(note)
            st.success("✅ 已存到 Pinecone！")