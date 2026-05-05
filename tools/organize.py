import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from pydantic import BaseModel
from typing import List

class NoteSchema(BaseModel):
    paper_title: str
    concept: str
    key_points: List[str]
    my_understanding: str
    related_concepts: List[str]

def read_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def extract_formulas(text: str):
    """把公式抽出來換成佔位符"""
    formulas = []
    
    def replace_formula(match):
        formulas.append(match.group(0))
        return f"[FORMULA_{len(formulas)-1}]"
    
    # 先抽 $$ 再抽 $（順序很重要）
    text = re.sub(r'\$\$.+?\$\$', replace_formula, text, flags=re.DOTALL)
    text = re.sub(r'\$.+?\$', replace_formula, text)
    
    return text, formulas

def restore_formulas(text: str, formulas: list) -> str:
    """把佔位符換回公式"""
    for i, formula in enumerate(formulas):
        text = text.replace(f"[FORMULA_{i}]", formula)
    return text

def organize_note_internal(chat_content):
    # 先把公式抽出來
    clean_content, formulas = extract_formulas(chat_content)
    
    llm = ChatOpenAI(model="gpt-4o-mini")
    structured_llm = llm.with_structured_output(NoteSchema)
    
    prompt = ChatPromptTemplate.from_template("""
你是一個專業的論文筆記整理助手。
請根據以下的對話內容，整理成結構化筆記。

對話內容：
{chat_content}

重要規則：
1. 如果內容中有 [FORMULA_數字] 這樣的佔位符，請原封不動保留在對應的重點裡。
2. 用第一人稱描述使用者的理解。
3. 所有輸出請使用繁體中文。
4. key_points 每個重點是一個獨立的句子。
5. 論文名稱不確定就寫「未知」。
""")
    
    chain = prompt | structured_llm
    result = chain.invoke({"chat_content": clean_content})
    note = result.model_dump()
    
    # 把公式換回來
    note["key_points"] = [restore_formulas(p, formulas) for p in note["key_points"]]
    note["my_understanding"] = restore_formulas(note["my_understanding"], formulas)
    
    return note

@tool
def organize_note_tool(file_path: str) -> dict:
    """讀取對話 markdown 檔案，整理成結構化筆記。輸入是 markdown 檔案的路徑。"""
    chat_content = read_markdown(file_path)
    return organize_note_internal(chat_content)