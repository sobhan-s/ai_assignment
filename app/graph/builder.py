from collections.abc import Awaitable, Callable
from typing import Any, cast

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.core.logging import get_logger
from app.domain.state import GraphState
from app.graph.nodes.circuit_breaker import circuit_breaker
from app.graph.nodes.classify_route import classify_route
from app.graph.nodes.condense_question import condense_question
from app.graph.nodes.direct_reply import direct_reply
from app.graph.nodes.persist_and_log import persist_and_log
from app.graph.nodes.rag_answer import rag_answer
from app.graph.nodes.rag_retrieve import rag_retrieve
from app.graph.nodes.refuse import refuse
from app.graph.nodes.sql_answer import sql_answer
from app.graph.nodes.sql_execute import sql_execute
from app.graph.nodes.sql_generate import sql_generate
from app.graph.nodes.sql_repair import sql_repair
from app.graph.nodes.sql_validate import sql_validate
from app.graph.nodes.synthesize import synthesize
from app.graph.routers import (
    route_after_classify,
    route_after_execute,
    route_after_validate,
)

log = get_logger(__name__)


def logged_node(
    name: str, func: Callable[[GraphState], Awaitable[Any]]
) -> Callable[[GraphState], Awaitable[Any]]:
    async def wrapper(state: GraphState) -> Any:
        log.info("graph.node.execute", node=name)
        return await func(state)

    return wrapper


def build_graph() -> CompiledStateGraph[Any, Any, Any]:
    """Compiles the LangGraph state machine based on our immutable GraphState."""
    workflow: Any = StateGraph(GraphState)

    # 1. Add all nodes to the graph
    workflow.add_node(
        "condense_question", logged_node("condense_question", condense_question)
    )
    workflow.add_node("classify_route", logged_node("classify_route", classify_route))
    workflow.add_node("rag_retrieve", logged_node("rag_retrieve", rag_retrieve))
    workflow.add_node("rag_answer", logged_node("rag_answer", rag_answer))
    workflow.add_node("sql_generate", logged_node("sql_generate", sql_generate))
    workflow.add_node("sql_validate", logged_node("sql_validate", sql_validate))
    workflow.add_node("sql_repair", logged_node("sql_repair", sql_repair))
    workflow.add_node("sql_execute", logged_node("sql_execute", sql_execute))
    workflow.add_node("sql_answer", logged_node("sql_answer", sql_answer))
    workflow.add_node(
        "circuit_breaker", logged_node("circuit_breaker", circuit_breaker)
    )
    workflow.add_node("direct_reply", logged_node("direct_reply", direct_reply))
    workflow.add_node("refuse", logged_node("refuse", refuse))
    workflow.add_node("synthesize", logged_node("synthesize", synthesize))
    workflow.add_node(
        "persist_and_log", logged_node("persist_and_log", persist_and_log)
    )

    # 2. Define the Entry Point
    workflow.set_entry_point("condense_question")

    # 3. Static Edges (Guaranteed linear paths)
    workflow.add_edge("condense_question", "classify_route")
    workflow.add_edge("rag_retrieve", "rag_answer")

    # RAG, Chitchat, Refuse, and Circuit Breaker all converge on Synthesize
    workflow.add_edge("rag_answer", "synthesize")
    workflow.add_edge("direct_reply", "synthesize")
    workflow.add_edge("refuse", "synthesize")
    workflow.add_edge("circuit_breaker", "synthesize")
    workflow.add_edge("sql_answer", "synthesize")

    workflow.add_edge("synthesize", "persist_and_log")
    workflow.add_edge("persist_and_log", END)

    # 4. The SQL Repair Loop (Internal static edge)
    workflow.add_edge("sql_repair", "sql_validate")

    # Generate always goes to validate
    workflow.add_edge("sql_generate", "sql_validate")

    # 5. Conditional Edges (The Brain's decision points)
    workflow.add_conditional_edges("classify_route", route_after_classify)
    workflow.add_conditional_edges("sql_validate", route_after_validate)
    workflow.add_conditional_edges("sql_execute", route_after_execute)

    return cast(CompiledStateGraph[Any, Any, Any], workflow.compile())
