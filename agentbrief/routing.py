"""Conditional routing: decides clarify vs retrieve vs continue based on state."""
from agentbrief.state import BriefState
from agentbrief.config import MAX_CLARIFICATION_QUESTIONS, STOPPING_PHRASES

def route_after_analysis(state: BriefState) -> str:
    """Route to 'more' if clarifications are needed and under the limit, else 'retrieve'."""
    qa = state.get("questions_answers", [])

    if len(qa) >= MAX_CLARIFICATION_QUESTIONS:
        return "retrieve"

    if "CLARIFICATION_NEEDED" in state.get("analyse", ""):
        return "more"
    return "retrieve"

def route_after_clarification(state: BriefState) -> str:
    """Route to 'retrieve' if the user used a stopping phrase, else 'call_model'."""
    last_qa = state.get("questions_answers", [])

    if last_qa and last_qa[-1]["r"].lower() in STOPPING_PHRASES:
        return "retrieve"
    return "call_model"
