import os
import re
from notion_client import Client
from langchain_core.tools import tool

def get_notion_client():
    return Client(auth=os.getenv("NOTION_API_KEY"))

def get_or_create_paper_page(paper_title: str) -> str:
    notion = get_notion_client()
    results = notion.search(query=paper_title).get("results", [])
    for page in results:
        if page["object"] == "page":
            title = page["properties"].get("title", {}).get("title", [])
            if title and title[0]["text"]["content"] == paper_title:
                return page["id"]
    
    new_page = notion.pages.create(
        parent={"page_id": os.getenv("NOTION_PAGE_ID")},
        properties={
            "title": {
                "title": [{"text": {"content": paper_title}}]
            }
        }
    )
    return new_page["id"]

def concept_exists(page_id: str, concept: str) -> bool:
    notion = get_notion_client()
    blocks = notion.blocks.children.list(page_id).get("results", [])
    for block in blocks:
        if block["type"] == "toggle":
            title = block["toggle"]["rich_text"]
            if title and title[0]["text"]["content"] == concept:
                return True
    return False

def text_to_rich_text(text: str) -> list:
    text = text.strip()
    # 整行都是公式
    full_match = re.match(r'^\$\$(.+)\$\$$', text)
    if full_match:
        return [{"type": "equation", "equation": {"expression": full_match.group(1)}}]
    # 文字裡面包含公式，拆開處理
    parts = re.split(r'(\$\$.+?\$\$|\$.+?\$)', text)
    rich_text = []
    for part in parts:
        if re.match(r'^\$\$(.+)\$\$$', part):
            expr = re.match(r'^\$\$(.+)\$\$$', part).group(1)
            rich_text.append({"type": "equation", "equation": {"expression": expr}})
        elif re.match(r'^\$(.+)\$$', part):
            expr = re.match(r'^\$(.+)\$$', part).group(1)
            rich_text.append({"type": "equation", "equation": {"expression": expr}})
        elif part:
            rich_text.append({"type": "text", "text": {"content": part}})
    return rich_text

def make_paragraph_block(text: str) -> dict:
    text = text.strip()
    if re.match(r'^\$\$(.+)\$\$$', text):
        formula = re.match(r'^\$\$(.+)\$\$$', text).group(1)
        return {
            "object": "block",
            "type": "equation",
            "equation": {"expression": formula}
        }
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }

def create_toggle_block(page_id: str, note: dict):
    notion = get_notion_client()

    key_point_children = [
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": text_to_rich_text(point)
            }
        }
        for point in note["key_points"]
    ]

    related_children = [
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": concept}}]
            }
        }
        for concept in note["related_concepts"]
    ]

    understanding_blocks = [
        make_paragraph_block(line)
        for line in note["my_understanding"].split("\n")
        if line.strip()
    ]

    notion.blocks.children.append(
        page_id,
        children=[
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": note["concept"]}}],
                    "children": [
                        {
                            "object": "block",
                            "type": "toggle",
                            "toggle": {
                                "rich_text": [{"type": "text", "text": {"content": "核心重點"}}],
                                "children": key_point_children
                            }
                        },
                        {
                            "object": "block",
                            "type": "toggle",
                            "toggle": {
                                "rich_text": [{"type": "text", "text": {"content": "我的理解"}}],
                                "children": understanding_blocks
                            }
                        },
                        {
                            "object": "block",
                            "type": "toggle",
                            "toggle": {
                                "rich_text": [{"type": "text", "text": {"content": "相關概念"}}],
                                "children": related_children
                            }
                        }
                    ]
                }
            }
        ]
    )

def delete_concept_from_notion(page_id: str, concept: str) -> bool:
    notion = get_notion_client()
    blocks = notion.blocks.children.list(page_id).get("results", [])
    for block in blocks:
        if block["type"] == "toggle":
            title = block["toggle"]["rich_text"]
            if title and title[0]["text"]["content"] == concept:
                notion.blocks.delete(block["id"])
                return True
    return False

@tool
def save_to_notion_tool(paper_title: str, concept: str, key_points: list, my_understanding: str, related_concepts: list) -> str:
    """把整理好的筆記存到 Notion。"""
    note = {
        "paper_title": paper_title,
        "concept": concept,
        "key_points": key_points,
        "my_understanding": my_understanding,
        "related_concepts": related_concepts
    }
    page_id = get_or_create_paper_page(paper_title)

    if concept_exists(page_id, concept):
        return f"這個概念已經存在：{paper_title} → {concept}，跳過儲存"

    create_toggle_block(page_id, note)
    return f"筆記已存到 Notion：{paper_title} → {concept}"

def delete_paper_page(page_id: str):
    """刪除整篇論文的 Notion 頁面"""
    notion = get_notion_client()
    notion.pages.update(page_id, archived=True)