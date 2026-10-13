"""
Prompts package
All LangChain prompt templates for the GenAI Data Assistant.

Each module exports exactly ONE named prompt object:
  - condense.py       → condense_prompt
  - router.py         → router_prompt
  - rag_answer.py     → rag_answer_prompt
  - sql_generate.py   → sql_generate_prompt
  - sql_repair.py     → sql_repair_prompt
  - sql_summarize.py  → sql_summarize_prompt  (canonical name)
  - sql_answer.py     → sql_answer_prompt     (alias of sql_summarize_prompt)
  - synthesize.py     → synthesize_prompt

Consumers should import chains from llm/chains.py rather than prompts directly.
"""
