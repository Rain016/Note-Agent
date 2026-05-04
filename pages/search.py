import streamlit as st
from tools.pinecone_tool import get_index, get_embeddings

def search_notes(query: str):
    index = get_index()
    embeddings = get_embeddings()
    vector = embeddings.embed_query(query)
    results = index.query(vector=vector, top_k=3, include_metadata=True)
    return results["matches"]

st.title("🔍 查詢筆記")

query = st.text_input("想查什麼？", placeholder="例如：forward process 是什麼？")

if st.button("搜尋", type="primary"):
    if query:
        with st.spinner("搜尋中..."):
            matches = search_notes(query)
        
        if not matches:
            st.warning("找不到相關筆記")
        else:
            st.subheader(f"找到 {len(matches)} 筆相關筆記")
            for match in matches:
                meta = match["metadata"]
                score = round(match["score"] * 100, 1)
                
                with st.expander(f"📄 {meta['paper_title']} → {meta['concept']} （相關度 {score}%）"):
                    content = meta["content"]
                    lines = content.strip().split("\n")
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("重點："):
                            st.write("**核心重點：**")
                            points = line.replace("重點：", "").split("。")
                            for point in points:
                                if point.strip():
                                    st.write(f"- {point.strip()}")
                        elif line.startswith("理解："):
                            st.write(f"**我的理解：** {line.replace('理解：', '')}")
                        elif line.startswith("相關："):
                            st.write(f"**相關概念：** {line.replace('相關：', '')}")
    else:
        st.warning("請輸入查詢內容")