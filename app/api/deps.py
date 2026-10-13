"""
FastAPI Dependency Providers
Centralises all dependency injection for routes.
Import `get_graph`, `get_settings`, etc. in route files instead of calling constructors directly.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends
from langgraph.graph.state import CompiledStateGraph

from app.core.config import Settings
from app.core.config import settings as _settings
from app.graph.builder import build_graph


# Graph (compiled once at startup, reused across requests)
@lru_cache(maxsize=1)
def _get_compiled_graph() -> CompiledStateGraph[Any, Any, Any]:
    """Compiles the LangGraph state machine once and caches it."""
    return build_graph()


def get_graph() -> CompiledStateGraph[Any, Any, Any]:
    """FastAPI dependency: returns the cached compiled LangGraph."""
    return _get_compiled_graph()


# Settings
def get_settings() -> Settings:
    """FastAPI dependency: returns the application settings singleton."""
    return _settings


# Type aliases for cleaner route signatures
GraphDep = Annotated[CompiledStateGraph[Any, Any, Any], Depends(get_graph)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
