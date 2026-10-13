from app.domain.state import (
    BranchResult,
    Frozen,
    NodeFailure,
    RetrievedChunk,
    RouteDecision,
    SqlDraft,
    SqlExecution,
    SqlValidation,
)

# Each delta represents the EXCLUSIVE fields a node is allowed to modify.


class ClassifyDelta(Frozen):
    decision: RouteDecision


class RagRetrieveDelta(Frozen):
    retrieved: tuple[RetrievedChunk, ...]


class SqlGenerateDelta(Frozen):
    sql_draft: SqlDraft
    sql_attempts: int


class SqlValidateDelta(Frozen):
    sql_validation: SqlValidation


class SqlRepairDelta(Frozen):
    sql_draft: SqlDraft
    sql_attempts: int


class BranchResultDelta(Frozen):
    # LangGraph reducers require lists or tuples to append
    branch_results: tuple[BranchResult, ...]


class NodeFailureDelta(Frozen):
    failures: tuple[NodeFailure, ...]


class SynthesizeDelta(Frozen):
    final_answer: str
    executed_sql: str | None = None


# SQL Execution deltas
# These were previously defined as *inline anonymous classes* inside
# graph/nodes/sql_execute.py   that is an anti-pattern. Delta types belong here.


class SqlExecutionSuccessDelta(Frozen):
    """Applied when execute_read_only_sql returns without error."""

    sql_execution: SqlExecution


class SqlExecuteFailDelta(Frozen):
    """Applied when the database rejects the query (e.g. missing column)."""

    sql_last_error: str
