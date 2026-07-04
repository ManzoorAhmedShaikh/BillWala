from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from .tools import fetch_hesco_bill
from .prompt import SYSTEM_PROMPT
import os

load_dotenv()
KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = ChatAnthropic(model="claude-haiku-4-5", api_key = KEY)
CHECKPOINTER = MemorySaver()

tools = [fetch_hesco_bill]
agent = create_agent(
    MODEL,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=CHECKPOINTER
)