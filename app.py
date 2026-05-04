import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Paper Note Agent",
    page_icon="📄",
    layout="wide"
)

pg = st.navigation([
    st.Page("pages/save_note.py", title="存筆記", icon="✏️"),
    st.Page("pages/note_list.py", title="筆記列表", icon="📚"),
    st.Page("pages/search.py", title="查詢筆記", icon="🔍"),
])

pg.run()