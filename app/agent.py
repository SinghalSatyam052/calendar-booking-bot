from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from .tools import availability_tool, suggest_slots_tool, booking_tool
from .config import get_settings

settings = get_settings()

# ── LLM ──────────────────────────────────────────────────────────────────────
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    streaming=True,
    api_key=settings.openai_api_key,
)

# ── Tools ────────────────────────────────────────────────────────────────────
_tools = [availability_tool, suggest_slots_tool, booking_tool]

# ── Memory (keeps full chat history) ─────────────────────────────────────────
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
)

# ── Prompt ───────────────────────────────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful assistant that manages calendar bookings for the user. "
        "Use the available tools to check availability, suggest time slots, and create events. "
        "Always confirm with the user before booking."
    ),
    MessagesPlaceholder(variable_name="chat_history"),  # <= full history here
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),  # required
])

# ── Agent & Executor ─────────────────────────────────────────────────────────
agent = create_openai_functions_agent(
    llm=llm,
    tools=_tools,
    prompt=prompt,
)

booking_agent: AgentExecutor = AgentExecutor(
    agent=agent,
    tools=_tools,
    memory=memory,      # <= give the agent its memory
    verbose=True,
)
