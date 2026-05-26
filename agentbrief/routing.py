from agentbrief.state import BriefState

def route_after_analysis(state: BriefState) -> str:
    """
        Determines the next routing step after the initial analysis phase.

        Args:
            state (BriefState): The current state of the agent, expected to contain
                an "analyse" key with the analysis results.

        Returns:
            str: "more" if the analysis indicates that further clarification is needed
                 (contains "CLARIFICATION_NEEDED"), otherwise returns "search_web" to
                 proceed with web searching.
    """
    if "CLARIFICATION_NEEDED" in state.get("analyse", ""):
        return "more"
    return "search_web"

def route_after_clarification(state: BriefState) -> str:
    """
        Determines the next routing step after interacting with the user for clarification.

        This router enforces a maximum limit of 2 questions. It also evaluates the user's
        latest response to determine if they wish to stop the clarification process early.

        Args:
            state (BriefState): The current state of the agent, containing the
                "questions_answers" history (a list of dicts with 'q' for question and 'r' for response).

        Returns:
            str: "search_web" if the 2-question limit is reached or if the user provides
                 a stopping phrase (e.g., "non", "stop", "ça suffit"). Otherwise, returns
                 "call_model" to continue the clarification loop.
    """
    last_qa = state.get("questions_answers", [])

    # 2 questions limit
    if len(last_qa) >= 2:
        return "search_web"

    # Check if the user wants to stop the clarification process
    if last_qa and last_qa[-1]["r"].lower() in ["non", "stop", "ça suffit", "comme tu veux"]:
        return "search_web"
    return "call_model"