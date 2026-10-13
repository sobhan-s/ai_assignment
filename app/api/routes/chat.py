"""
Chat Route
POST /chat   main entry point for conversational queries.
Uses the LangGraph compiled graph injected via api/deps.py.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter

from app.api.deps import GraphDep
from app.api.schemas import ChatRequest, ChatResponse
from app.core.logging import bind_request_id, clear_request_context, get_logger

router = APIRouter(prefix="/chat", tags=["chat"])
log = get_logger(__name__)


@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    graph: GraphDep,
) -> ChatResponse:
    """
    Main entrypoint. Takes a secure HTTP request and runs it through
    the LangGraph state machine.
    """
    request_id = uuid4()
    bind_request_id(str(request_id))

    try:
        log.info(
            "chat.request",
            thread_id=str(request.thread_id),
            question=request.message[:80],
        )

        # Initialise the strict immutable state
        initial_state = {
            "thread_id": request.thread_id,
            "request_id": request_id,
            "question": request.message,
        }

        # Config ensures checkpointing works per thread_id
        config = {"configurable": {"thread_id": str(request.thread_id)}}

        final_state = await graph.ainvoke(initial_state, config=config)  # type: ignore[call-overload]

        # Safely extract fields from the final state dict
        decision = final_state.get("decision")
        if decision:
            route = (
                decision.get("route")
                if isinstance(decision, dict)
                else getattr(decision, "route", None)
            )
        else:
            route = None

        response = ChatResponse(
            request_id=request_id,
            thread_id=request.thread_id,
            answer=final_state.get("final_answer") or "No answer generated.",
            route=route,
            outcome=final_state.get("outcome"),
            citations=list(final_state.get("final_citations") or []),
            executed_sql=final_state.get("executed_sql"),
        )

        log.info("chat.response", route=str(route), answer_length=len(response.answer))
        return response

    finally:
        clear_request_context()
