import os
from notion_client import Client
from langchain_core.tools import tool

PARENT_PAGE_ID = os.getenv("NOTION_PAGE_ID")

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
    """檢查頁面裡是否已有這個概念的 toggle"""
    notion = get_notion_client()
    blocks = notion.blocks.children.list(page_id).get("results", [])
    for block in blocks:
        if block["type"] == "toggle":
            title = block["toggle"]["rich_text"]
            if title and title[0]["text"]["content"] == concept:
                return True
    return False

def create_toggle_block(page_id: str, note: dict):
    """在頁面裡建立 toggle 結構的筆記"""
    
    # 建立 key_points 的子 bullet
    notion = get_notion_client()
    key_point_children = [
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": point}}]
            }
        }
        for point in note["key_points"]
    ]

    # 建立 related_concepts 的子 bullet
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
                                "children": [
                                    {
                                        "object": "block",
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [{"type": "text", "text": {"content": note["my_understanding"]}}]
                                        }
                                    }
                                ]
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