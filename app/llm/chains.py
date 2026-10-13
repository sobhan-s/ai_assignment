from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable

from app.domain.state import RouteDecision
from app.llm.factory import get_llm
from app.llm.prompts.condense import condense_prompt
from app.llm.prompts.rag_answer import rag_answer_prompt
from app.llm.prompts.router import router_prompt
from app.llm.prompts.sql_generate import sql_generate_prompt
from app.llm.prompts.sql_repair import sql_repair_prompt
from app.llm.prompts.sql_summarize import sql_summarize_prompt
from app.llm.prompts.synthesize import synthesize_prompt


def get_condense_chain() -> Runnable[Any, Any]:
    """Rephrases a follow-up question into a standalone question."""
    llm = get_llm()
    return condense_prompt | llm | StrOutputParser()


def get_router_chain() -> Runnable[Any, Any]:
    """Classifies user intent into a RouteDecision structured output."""
    llm = get_llm()
    return router_prompt | llm.with_structured_output(RouteDecision)


def get_rag_answer_chain() -> Runnable[Any, Any]:
    """Answers a question strictly from retrieved document context."""
    llm = get_llm()
    return rag_answer_prompt | llm | StrOutputParser()


def get_sql_generate_chain() -> Runnable[Any, Any]:
    """Generates a raw PostgreSQL query from a natural-language question."""
    llm = get_llm()
    return sql_generate_prompt | llm | StrOutputParser()


def get_sql_repair_chain() -> Runnable[Any, Any]:
    """Repairs a broken SQL query given the error message."""
    llm = get_llm()
    return sql_repair_prompt | llm | StrOutputParser()


def get_sql_summarize_chain() -> Runnable[Any, Any]:
    """Converts raw SQL results into a human-readable answer."""
    llm = get_llm()
    return sql_summarize_prompt | llm | StrOutputParser()


def get_synthesize_chain() -> Runnable[Any, Any]:
    """Merges RAG and SQL branch answers into a single coherent response."""
    llm = get_llm()
    return synthesize_prompt | llm | StrOutputParser()
