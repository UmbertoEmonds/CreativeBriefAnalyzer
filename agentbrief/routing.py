"""
Conditional routing functions for the ChatBotLangGraph state graph.

Determines whether to ask for more clarifications, proceed to
retrieval, or terminate based on the current graph state.
"""
from agentbrief.state import BriefState
from agentbrief.config import MAX_CLARIFICATION_QUESTIONS, STOPPING_PHRASES

def route_after_analysis(state: BriefState) -> str:
    """
        Determines the next routing step after the initial analysis phase.

        Enforces a maximum question limit by routing directly to 'retrieve'
        once enough clarifications have been collected. If the limit is not
        reached, routes to 'more' when the LLM flags the brief as incomplete,
        or to 'retrieve' otherwise.

        Args:
            state (BriefState): The current graph state, expected to contain
                an 'analyse' key with the LLM's analysis and a
                'questions_answers' key with the clarification history.

        Returns:
            str: 'retrieve' if the question limit is reached or the brief
                 is sufficiently detailed. 'more' if the analysis contains
                 'CLARIFICATION_NEEDED'.
    """
    qa = state.get("questions_answers", [])

    if len(qa) >= MAX_CLARIFICATION_QUESTIONS:
        return "retrieve"

    if "CLARIFICATION_NEEDED" in state.get("analyse", ""):
        return "more"
    return "retrieve"

def route_after_clarification(state: BriefState) -> str:
    """
        Determines the next routing step after a user clarification interaction.

        Evaluates the user's latest response to check whether they wish to
        stop the clarification process early using a stopping phrase. If no
        stopping phrase is detected, routes back to 'call_model' to re-analyse
        the brief with the updated clarification history.

        Args:
            state (BriefState): The current graph state, containing the
                'questions_answers' history (a list of QA dicts with 'q'
                for question and 'r' for user response).

        Returns:
            str: 'retrieve' if the user provides a stopping phrase
                 (e.g., 'non', 'stop', 'ça suffit', 'comme tu veux').
                 Otherwise, returns 'call_model' to continue the loop.
    """
    last_qa = state.get("questions_answers", [])

    if last_qa and last_qa[-1]["r"].lower() in STOPPING_PHRASES:
        return "retrieve"
    return "call_model"