"""
Prompts package.
All LangChain prompt templates for the GenAI Data Assistant.
Import prompts directly from this module (e.g. `from app.prompts import router_prompt`).
"""

from app.prompts.condense import CONDENSE_SYSTEM_PROMPT, condense_prompt
from app.prompts.rag_answer import RAG_ANSWER_SYSTEM_PROMPT, rag_answer_prompt
from app.prompts.router import ROUTER_SYSTEM_PROMPT, router_prompt
from app.prompts.sql_answer import sql_answer_prompt
from app.prompts.sql_generate import SQL_GENERATE_SYSTEM_PROMPT, sql_generate_prompt
from app.prompts.sql_repair import SQL_REPAIR_SYSTEM_PROMPT, sql_repair_prompt
from app.prompts.sql_summarize import SQL_SUMMARIZE_SYSTEM_PROMPT, sql_summarize_prompt
from app.prompts.synthesize import SYNTHESIZE_SYSTEM_PROMPT, synthesize_prompt

__all__ = [
    "CONDENSE_SYSTEM_PROMPT",
    "RAG_ANSWER_SYSTEM_PROMPT",
    "ROUTER_SYSTEM_PROMPT",
    "SQL_GENERATE_SYSTEM_PROMPT",
    "SQL_REPAIR_SYSTEM_PROMPT",
    "SQL_SUMMARIZE_SYSTEM_PROMPT",
    "SYNTHESIZE_SYSTEM_PROMPT",
    "condense_prompt",
    "rag_answer_prompt",
    "router_prompt",
    "sql_answer_prompt",
    "sql_generate_prompt",
    "sql_repair_prompt",
    "sql_summarize_prompt",
    "synthesize_prompt",
]
