from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from tools.organize import organize_note_tool
from tools.notion_tool import save_to_notion_tool
from tools.pinecone_tool import save_to_pinecone_tool, search_notes_tool

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")

tools = [
    organize_note_tool,
    save_to_notion_tool,
    save_to_pinecone_tool,
    search_notes_tool
]

agent = create_react_agent(llm, tools)

agent = create_react_agent(llm, tools)

def chat(message: str):
    result = agent.invoke(
        {"messages": [("human", message)]},
        config={"recursion_limit": 10}
    )
    # 印出所有訊息看過程
    for msg in result['messages']:
        print(f"\n[{msg.type}]: {msg.content}")
    return result['messages'][-1].content

print(chat("請幫我整理 test_chat.md 的筆記，整理完之後存到 Notion 和 Pinecone"))
print(chat("我之前有讀過關於 forward process 的筆記嗎？"))