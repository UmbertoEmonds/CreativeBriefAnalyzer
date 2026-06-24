"""LangGraph StateGraph definition for the brief analysis workflow."""
from langchain_mistralai import ChatMistralAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from agentbrief.config import LLM_MODEL
from agentbrief.routing import route_after_analysis, route_after_clarification
from agentbrief.nodes import call_model, ask, retrieve, generate_final_data, create_html
from agentbrief.state import BriefState
from dotenv import load_dotenv

load_dotenv()

llm = ChatMistralAI(model=LLM_MODEL)

builder = StateGraph(BriefState)

builder.add_node("call_model", lambda state: call_model(state, llm))
builder.add_node("more", lambda state: ask(state, llm))
builder.add_node("retrieve", lambda state: retrieve(state, llm))
builder.add_node("generate", lambda state: generate_final_data(state, llm))
builder.add_node("create_html", create_html)

builder.add_edge(START, "call_model")

builder.add_conditional_edges("call_model", route_after_analysis)
builder.add_conditional_edges("more", route_after_clarification)

builder.add_edge("retrieve", "generate")
builder.add_edge("generate", "create_html")
builder.add_edge("create_html", END)

graph = builder.compile(checkpointer=MemorySaver())
