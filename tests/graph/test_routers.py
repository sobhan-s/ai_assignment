from uuid import uuid4

from app.domain.state import GraphState, Route, RouteDecision, SqlValidation
from app.graph.routers import route_after_classify, route_after_validate


def test_route_after_classify():
    state = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        decision=RouteDecision(route=Route.DATABASE, confidence=1.0, rationale="test"),
    )
    assert route_after_classify(state) == "sql_generate"

    state_combined = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        decision=RouteDecision(route=Route.COMBINED, confidence=1.0, rationale="test"),
    )
    out = route_after_classify(state_combined)
    assert isinstance(out, list)
    assert len(out) == 2


def test_route_after_validate():
    state_ok = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_validation=SqlValidation(ok=True),
    )
    assert route_after_validate(state_ok) == "sql_execute"

    state_fail = GraphState(
        thread_id=uuid4(),
        request_id=uuid4(),
        question="test",
        sql_validation=SqlValidation(ok=False, violations=("error",)),
        sql_attempts=1,
    )
    assert route_after_validate(state_fail) == "sql_repair"
