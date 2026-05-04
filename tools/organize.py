import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import tool

def read_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def organize_note_internal(chat_content):
    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = ChatPromptTemplate.from_template("""
你是一個專業的論文筆記整理助手。
請根據以下的對話內容，整理成結構化筆記。

對話內容：
{chat_content}

請輸出 JSON 格式，不要加其他東西：
{{
    "paper_title": "論文名稱，不確定就寫未知",
    "concept": "這段對話討論的概念名稱",
    "key_points": ["重點1", "重點2", "重點3"],
    "my_understanding": "用第一人稱描述使用者的理解",
    "related_concepts": ["相關概念1", "相關概念2"]
}}
""")
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    return chain.invoke({"chat_content": chat_content})

@tool
def organize_note_tool(file_path: str) -> dict:
    """讀取對話 markdown 檔案，整理成結構化筆記。輸入是 markdown 檔案的路徑。"""
    chat_content = read_markdown(file_path)
    return organize_note_internal(chat_content)