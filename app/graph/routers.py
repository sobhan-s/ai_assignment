from typing import Literal

from langgraph.types import Send

from app.domain.state import GraphState, Route


def route_after_classify(
    state: GraphState,
) -> Literal["rag_retrieve", "sql_generate", "refuse", "direct_reply"] | list[Send]:
    """
    Determines where to go after the classification LLM makes its decision.
    If the decision is COMBINED, it fans out to both RAG and SQL in parallel.
    """
    decision = state.decision
    if not decision:
        return "refuse"

    if decision.route == Route.DOCUMENTS:
        return "rag_retrieve"
    elif decision.route == Route.DATABASE:
        return "sql_generate"
    elif decision.route == Route.COMBINED:
        # LangGraph Fan-Out: Execute both nodes in parallel
        return [Send("rag_retrieve", state), Send("sql_generate", state)]
    elif decision.route == Route.CHITCHAT:
        return "direct_reply"
    else:  # Route.REFUSE
        return "refuse"


def route_after_validate(
    state: GraphState,
) -> Literal["sql_execute", "sql_repair", "circuit_breaker"]:
    """
    After SQL validation, proceed to execution if OK,
    otherwise loop to repair, or break the circuit if max attempts reached.
    """
    if state.sql_validation and state.sql_validation.ok:
        return "sql_execute"

    if state.sql_attempts < 3:
        return "sql_repair"

    return "circuit_breaker"


def route_after_execute(
    state: GraphState,
) -> Literal["sql_answer", "sql_repair", "circuit_breaker"]:
    """
    If SQL execution throws a database error, loop to repair or break circuit.
    """
    # Assuming if sql_last_error is present, execution failed.
    if state.sql_last_error:
        if state.sql_attempts < 3:
            return "sql_repair"
        return "circuit_breaker"

    return "sql_answer"
