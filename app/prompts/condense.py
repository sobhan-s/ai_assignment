"""
Condense Question Prompt
Rephrases the user's latest question into a fully self-contained standalone question
by resolving pronoun references using the chat history.
"""

from langchain_core.prompts import ChatPromptTemplate

CONDENSE_SYSTEM_PROMPT = """\
You are a language assistant specialised in resolving conversational references.

Your ONLY job is to rewrite the user's <final_question> so that it makes sense in isolation,
without requiring the reader to see the <chat_history>.

### REWRITING RULES ###
1. Replace ALL pronouns (he, she, it, they, this, that, these, those) with their concrete referents from the history.
2. Expand any abbreviations or shorthand that only make sense with the history context.
3. If the question already makes complete sense on its own, reproduce it EXACTLY without any changes.
4. NEVER answer the question. NEVER add commentary. Output ONLY the rewritten question.

<chat_history>
{chat_history}
</chat_history>

<final_question>
{question}
</final_question>

Rewritten Question:"""

condense_prompt = ChatPromptTemplate.from_template(CONDENSE_SYSTEM_PROMPT)
