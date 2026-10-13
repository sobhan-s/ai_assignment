"""
Unit tests for graph router functions.
All tests are deterministic   no LLM calls involved.
"""

from __future__ import annotations

from uuid import uuid4

from langgraph.types import Send

from app.domain.state import GraphState, Route, RouteDecision, SqlValidation
from app.graph.routers import (
    route_after_classify,
    route_after_execute,
    route_after_validate,
)

# route_after_classify


class TestRouteAfterClassify:
    def _state(self, route: Route) -> GraphState:
        return GraphState(
            thread_id=uuid4(),
            request_id=uuid4(),
            question="test",
            decision=RouteDecision(route=route, confidence=1.0, rationale="test"),
        )

    def test_documents_routes_to_rag_retrieve(self) -> None:
        assert route_after_classify(self._state(Route.DOCUMENTS)) == "rag_retrieve"

    def test_database_routes_to_sql_generate(self) -> None:
        assert route_after_classify(self._state(Route.DATABASE)) == "sql_generate"

    def test_chitchat_routes_to_direct_reply(self) -> None:
        assert route_after_classify(self._state(Route.CHITCHAT)) == "direct_reply"

    def test_refuse_routes_to_refuse(self) -> None:
        assert route_after_classify(self._state(Route.REFUSE)) == "refuse"

    def test_combined_fans_out_to_both(self) -> None:
        result = route_after_classify(self._state(Route.COMBINED))
        assert isinstance(result, list)
        assert len(result) == 2
        nodes = {s.node for s in result}
        assert "rag_retrieve" in nodes
        assert "sql_generate" in nodes

    def test_combined_sends_are_send_objects(self) -> None:
        result = route_after_classify(self._state(Route.COMBINED))
        assert all(isinstance(s, Send) for s in result)

    def test_no_decision_routes_to_refuse(self) -> None:
        state = GraphState(thread_id=uuid4(), request_id=uuid4(), question="test")
        assert route_after_classify(state) == "refuse"


# route_after_validate


class TestRouteAfterValidate:
    def _state(self, ok: bool, attempts: int) -> GraphState:
        return GraphState(
            thread_id=uuid4(),
            request_id=uuid4(),
            question="test",
            sql_validation=SqlValidation(
                ok=ok,
                violations=() if ok else ("some error",),
            ),
            sql_attempts=attempts,
        )

    def test_valid_sql_routes_to_execute(self) -> None:
        assert route_after_validate(self._state(ok=True, attempts=1)) == "sql_execute"

    def test_invalid_sql_low_attempts_routes_to_repair(self) -> None:
        assert route_after_validate(self._state(ok=False, attempts=1)) == "sql_repair"

    def test_invalid_sql_at_max_attempts_trips_circuit(self) -> None:
        assert (
            route_after_validate(self._state(ok=False, attempts=3)) == "circuit_breaker"
        )

    def test_invalid_sql_attempt_2_routes_to_repair(self) -> None:
        assert route_after_validate(self._state(ok=False, attempts=2)) == "sql_repair"

    def test_valid_sql_regardless_of_attempts(self) -> None:
        # Even at attempt 3, if SQL passes validation, it should execute
        assert route_after_validate(self._state(ok=True, attempts=3)) == "sql_execute"

    def test_no_validation_result_trips_circuit(self) -> None:
        # sql_validation=None, attempts=3 → circuit_breaker
        state = GraphState(
            thread_id=uuid4(), request_id=uuid4(), question="test", sql_attempts=3
        )
        # sql_validation is None so ok check evaluates to False
        assert route_after_validate(state) == "circuit_breaker"


# route_after_execute


class TestRouteAfterExecute:
    def _state(self, last_error: str | None, attempts: int) -> GraphState:
        return GraphState(
            thread_id=uuid4(),
            request_id=uuid4(),
            question="test",
            sql_last_error=last_error,
            sql_attempts=attempts,
        )

    def test_no_error_routes_to_sql_answer(self) -> None:
        assert route_after_execute(self._state(None, 1)) == "sql_answer"

    def test_error_low_attempts_routes_to_repair(self) -> None:
        assert (
            route_after_execute(self._state("column does not exist", 1)) == "sql_repair"
        )

    def test_error_at_max_attempts_trips_circuit(self) -> None:
        assert (
            route_after_execute(self._state("column does not exist", 3))
            == "circuit_breaker"
        )

    def test_error_attempt_2_routes_to_repair(self) -> None:
        assert route_after_execute(self._state("timeout", 2)) == "sql_repair"
