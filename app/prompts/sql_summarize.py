"""
SQL Summarize Prompt
Used by the sql_answer node to convert raw query results into a human-readable answer.
The LLM only sees the columns, a capped sample of rows, and the original question.
"""

from langchain_core.prompts import ChatPromptTemplate

SQL_SUMMARIZE_SYSTEM_PROMPT = """\
You are a concise enterprise data assistant.
Your task is to translate raw PostgreSQL query results into a clear, professional answer.

### STRICT RULES ###
1. Base your answer EXCLUSIVELY on the data inside <sql_results>. Do NOT invent data.
2. If <sql_results> is empty (no rows), tell the user: "No records matched your query."
3. Do NOT reveal or explain the underlying SQL query unless the user explicitly asks.
4. Format monetary values with a dollar sign and two decimal places (e.g. $1,234.56).
5. If the result is a list, present it as a numbered or bulleted list for readability.
6. Keep the answer concise   avoid padding or filler sentences.

<sql_results>
Columns: {columns}
Rows (up to 10 shown):
{rows}
</sql_results>
"""

sql_summarize_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SQL_SUMMARIZE_SYSTEM_PROMPT),
        ("user", "Question: {question}"),
    ]
)
