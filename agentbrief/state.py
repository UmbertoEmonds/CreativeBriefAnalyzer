import operator
from typing import TypedDict, Annotated

class QA(TypedDict):
    q: str
    r: str

class BriefState(TypedDict):
    input: str
    analyse: str
    questions_answers: Annotated[list[QA], operator.add]
    rag_result: str
    final_data: str
    result_path: str