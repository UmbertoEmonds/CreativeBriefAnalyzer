from agentbrief.state import BriefState

def route_after_analysis(state: BriefState) -> str:
    """
        Determines the next routing step after the initial analysis phase.

        Enforces a maximum question limit by routing directly to 'search_web'
        once enough clarifications have been collected. If the limit is not
        reached, routes to 'more' when the LLM flags the brief as incomplete,
        or to 'search_web' otherwise.

        Args:
            state (BriefState): The current graph state, expected to contain
                an 'analyse' key with the LLM's analysis and a
                'questions_answers' key with the clarification history.

        Returns:
            str: 'search_web' if the question limit is reached or the brief
                 is sufficiently detailed. 'more' if the analysis contains
                 'CLARIFICATION_NEEDED'.
    """
    qa = state.get("questions_answers", [])

    # 4 questions limit
    if len(qa) >= 4:
        return "search_web"

    if "CLARIFICATION_NEEDED" in state.get("analyse", ""):
        return "more"
    return "search_web"

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
            str: 'search_web' if the user provides a stopping phrase
                 (e.g., 'non', 'stop', 'ça suffit', 'comme tu veux').
                 Otherwise returns 'call_model' to continue the loop.
    """
    last_qa = state.get("questions_answers", [])

    # Check if the user wants to stop the clarification process
    if last_qa and last_qa[-1]["r"].lower() in ["non", "stop", "ça suffit", "comme tu veux"]:
        return "search_web"
    return "call_model"