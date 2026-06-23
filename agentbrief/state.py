"""
Shared state type definitions for the ChatBotLangGraph workflow.

Defines the QA typed dict for question/answer pairs and the
BriefState typed dict that serves as the graph's state schema.
"""
import operator
from typing import TypedDict, Annotated, List


class QA(TypedDict):
    """A single question/answer pair from the clarification loop."""
    q: str
    r: str

class BriefState(TypedDict):
    """Shared state schema for the LangGraph brief analysis workflow."""
    input: str
    analyse: str
    questions_answers: Annotated[List[QA], operator.add]
    rag_result: str
    final_data: str
    result_path: str
    sources: List[str]