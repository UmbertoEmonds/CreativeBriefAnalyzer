"""Shared state type definitions for the ChatBotLangGraph workflow."""
import operator
from typing import TypedDict, Annotated, List


class QA(TypedDict):
    """A single question/answer pair from the clarification loop."""
    q: str
    r: str

class BriefState(TypedDict):
    """State schema for the LangGraph brief analysis workflow."""
    input: str
    analyse: str
    questions_answers: Annotated[List[QA], operator.add]
    rag_result: str
    final_data: str
    result_path: str
    sources: List[str]
