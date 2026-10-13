import os
import uuid

import requests
import streamlit as st

st.set_page_config(
    page_title="Enterprise Data Assistant", layout="wide", page_icon="🚀"
)

API_URL = os.getenv("API_URL", "http://localhost:8000/chat")

# Initialize Session State
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_sql" not in st.session_state:
    st.session_state.last_sql = None
if "last_route" not in st.session_state:
    st.session_state.last_route = None
if "last_citations" not in st.session_state:
    st.session_state.last_citations = []

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")
    st.caption(f"**Thread ID:** `{st.session_state.thread_id}`")

    if st.button("🔄 New Conversation", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.last_sql = None
        st.session_state.last_route = None
        st.session_state.last_citations = []
        st.rerun()

# --- Main Layout ---
# 2/3 for chat, 1/3 for raw data inspector
col_chat, col_data = st.columns([2, 1], gap="large")

with col_chat:
    st.title("Enterprise Data Assistant")
    st.caption("Hybrid RAG & Text-to-SQL Assistant powered by LangGraph")

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ask about customers, orders, or company policies..."):
        # Add to state and display
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Using st.status to show the "process"
            with st.status(
                "Consulting the LangGraph Brain...", expanded=True
            ) as status:
                st.write("📡 Sending request to Router...")
                try:
                    response = requests.post(
                        API_URL,
                        json={
                            "message": prompt,
                            "thread_id": st.session_state.thread_id,
                        },
                        timeout=120,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        route = data.get("route", "unknown")
                        answer = data.get("answer", "No answer provided.")

                        # Update status with final route
                        status.update(
                            label=f"Done! Routed to `{route}` branch.", state="complete"
                        )

                        # Save inspector data
                        st.session_state.last_sql = data.get("executed_sql")
                        st.session_state.last_route = route
                        st.session_state.last_citations = data.get("citations", [])

                        # Display the actual answer
                        st.markdown(answer)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": answer}
                        )
                    else:
                        status.update(label="API Error", state="error")
                        st.error(f"Error {response.status_code}: {response.text}")
                except Exception as e:
                    status.update(label="Connection Error", state="error")
                    st.error(f"Failed to connect to backend: {str(e)}")

# --- Right Column (Inspector) ---
with col_data:
    st.subheader("Data Inspector 🔍")

    if st.session_state.last_route:
        if st.session_state.last_route == "database":
            st.info("🛤️ **Route:** Database (SQL)")
        elif st.session_state.last_route == "documents":
            st.info("🛤️ **Route:** Documents (RAG)")
        elif st.session_state.last_route == "combined":
            st.info("🛤️ **Route:** Combined (Parallel Fan-Out)")
        else:
            st.info(f"🛤️ **Route:** {st.session_state.last_route}")

    st.divider()

    if st.session_state.last_sql:
        st.write("### 💻 Executed SQL")
        st.code(st.session_state.last_sql, language="sql")

    if st.session_state.last_citations:
        st.write("### 📄 Document Citations")
        for idx, citation in enumerate(st.session_state.last_citations):
            with st.expander(f"Source: {citation.get('filename', 'Unknown')}"):
                st.write(f"**Score:** {citation.get('score', 0):.2f}")
                st.write(citation.get("snippet", ""))

    if (
        not st.session_state.last_route
        and not st.session_state.last_sql
        and not st.session_state.last_citations
    ):
        st.caption(
            "Submit a query to see behind-the-scenes data here (like generated SQL or document citations)."
        )
