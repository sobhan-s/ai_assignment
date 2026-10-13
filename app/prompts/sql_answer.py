"""
SQL Answer / Summarize Prompt
Converts raw SQL execution results (columns + rows) into a human-readable answer.
This is an alias of sql_summarize, kept here for backwards compatibility.
"""

from app.prompts.sql_summarize import sql_summarize_prompt

# Canonical export expected by sql_answer node
sql_answer_prompt = sql_summarize_prompt
