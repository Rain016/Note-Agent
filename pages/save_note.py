import streamlit as st
from tools.organize import organize_note_internal
from tools.notion_tool import get_or_create_paper_page, concept_exists, create_toggle_block
from tools.pinecone_tool import get_index, get_embeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
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

def ai_revise_note(note: dict, instruction: str) -> dict:
    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = ChatPromptTemplate.from_template("""
你是一個論文筆記整理助手。
使用者想要修改以下筆記，請根據修改指令調整內容。

目前筆記：
概念：{concept}
核心重點：{key_points}
我的理解：{my_understanding}
相關概念：{related_concepts}

修改指令：{instruction}

請輸出修改後的 JSON，格式如下，不要加其他東西：
{{
    "concept": "概念名稱",
    "key_points": ["重點1", "重點2"],
    "my_understanding": "我的理解",
    "related_concepts": ["相關概念1", "相關概念2"]
}}
""")
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    result = chain.invoke({
        "concept": note["concept"],
        "key_points": "\n".join(note["key_points"]),
        "my_understanding": note["my_understanding"],
        "related_concepts": ", ".join(note["related_concepts"]),
        "instruction": instruction
    })
    result["paper_title"] = note["paper_title"]
    return result

st.title("✏️ 存筆記")

paper_title = st.text_input("論文名稱", placeholder="例如：Diffusion Policy")
concept_name = st.text_input("概念名稱", placeholder="例如：Forward Process")
uploaded_files = st.file_uploader(
    "上傳對話 markdown 檔（可多選）",
    type=["md"],
    accept_multiple_files=True
)

if uploaded_files and paper_title and concept_name:
    all_content = ""
    for f in uploaded_files:
        all_content += f.read().decode("utf-8") + "\n\n"

    with st.expander("點開查看對話內容"):
        st.text(all_content)

    if st.button("整理筆記", type="primary"):
        with st.spinner("整理中..."):
            note = organize_note_internal(all_content)
            note["paper_title"] = paper_title
            note["concept"] = concept_name
        st.session_state["current_note"] = note

if "current_note" in st.session_state:
    note = st.session_state["current_note"]

    st.subheader("整理結果")
    
    col_edit, col_preview = st.columns(2)
    
    with col_edit:
        st.markdown("#### ✏️ 編輯")
        edited_concept = st.text_input("概念名稱", value=note["concept"], key="edit_concept")
        
        st.write("**核心重點**（每行一個）")
        edited_key_points = st.text_area(
            "核心重點",
            value="\n".join(note["key_points"]),
            height=150,
            label_visibility="collapsed"
        )
        
        edited_understanding = st.text_area(
            "我的理解",
            value=note["my_understanding"],
            height=100
        )
        
        edited_related = st.text_input(
            "相關概念（用逗號分隔）",
            value=", ".join(note["related_concepts"])
        )

        st.markdown("#### 🤖 請 AI 修改")
        instruction = st.text_input("修改指令", placeholder="例如：把第二點重點刪掉")
        if st.button("請 AI 修改"):
            current = {
                "paper_title": note["paper_title"],
                "concept": edited_concept,
                "key_points": [p.strip() for p in edited_key_points.split("\n") if p.strip()],
                "my_understanding": edited_understanding,
                "related_concepts": [r.strip() for r in edited_related.split(",") if r.strip()]
            }
            with st.spinner("修改中..."):
                revised = ai_revise_note(current, instruction)
                st.session_state["current_note"] = revised
            st.rerun()

    with col_preview:
        st.markdown("#### 👁️ 預覽")
        st.markdown(f"## {edited_concept}")
        
        st.markdown("**核心重點**")
        for point in edited_key_points.split("\n"):
            if point.strip():
                st.markdown(f"- {point.strip()}")
        
        st.markdown("**我的理解**")
        st.markdown(edited_understanding)
        
        st.markdown("**相關概念**")
        st.markdown(", ".join([r.strip() for r in edited_related.split(",") if r.strip()]))

    st.divider()
    if st.button("確認儲存到 Notion + Pinecone", type="primary"):
        final_note = {
            "paper_title": note["paper_title"],
            "concept": edited_concept,
            "key_points": [p.strip() for p in edited_key_points.split("\n") if p.strip()],
            "my_understanding": edited_understanding,
            "related_concepts": [r.strip() for r in edited_related.split(",") if r.strip()]
        }
        with st.spinner("儲存中..."):
            page_id = get_or_create_paper_page(final_note["paper_title"])
            if concept_exists(page_id, final_note["concept"]):
                st.warning(f"這個概念已經存在：{final_note['concept']}，跳過 Notion 儲存")
            else:
                create_toggle_block(page_id, final_note)
                st.success("✅ 已存到 Notion！")
            save_to_pinecone(final_note)
            st.success("✅ 已存到 Pinecone！")