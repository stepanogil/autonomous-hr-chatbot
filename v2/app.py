"""
Streamlit frontend for the HR Chatbot v2.

Renders a chat interface that streams model reasoning, tool calls, file search
results, and the final assistant answer in real time. Backend (local OpenAI or
Azure OpenAI) is selected via the ``BACKEND`` environment variable.

Session state keys
------------------
history : list[dict]
    UI-only message log — ``[{"role": "user"|"assistant", "content": str}]``.
    Used solely to re-render past messages on Streamlit reruns; the actual
    conversation context lives server-side via ``previous_response_id``.
previous_response_id : str | None
    The ``response.id`` returned by the last Responses API call, threaded into
    the next ``run_turn`` call so the model retains full conversation context
    without replaying the message history.
client : openai.OpenAI | openai.AzureOpenAI
    Shared API client, created once and stored to avoid re-initialising on
    every Streamlit rerun.
config : dict
    Backend configuration dict from ``get_config()`` — contains ``model``,
    ``vector_store_id``, and ``system_prompt``.

Environment variables (via .env)
---------------------------------
BACKEND : str
    ``"local"`` (default) or ``"azure"``.
HR_USER_NAME : str
    Display name of the current user shown in the caption bar.
"""

import json
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="HR Chatbot (v2)", page_icon="🤖", layout="centered")

# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------
backend = os.getenv("BACKEND", "local")
if backend == "azure":
    from backend_azure import get_config, make_client
else:
    from backend_local import get_config, make_client

from agent_loop import run_turn  # noqa: E402

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []  # [{role, content}] for UI rendering only
if "previous_response_id" not in st.session_state:
    st.session_state.previous_response_id = None
if "client" not in st.session_state:
    st.session_state.client = make_client()
if "config" not in st.session_state:
    st.session_state.config = get_config()

client = st.session_state.client
config = st.session_state.config

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("HR Chatbot")
st.caption(
    f"Powered by OpenAI Responses API · model `{config['model']}` · "
    f"backend `{backend}` · user `{os.getenv('HR_USER_NAME', 'Alexander Verdad')}`"
)
st.divider()

# ---------------------------------------------------------------------------
# Render conversation history
# ---------------------------------------------------------------------------
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask your HR question…")

if user_input:
    # Show user message immediately
    st.session_state.history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Stream the assistant response
    with st.chat_message("assistant"):
        reasoning_text = ""
        answer_text = ""
        answer_placeholder = st.empty()

        with st.status("Thinking…", expanded=True) as status:
            reasoning_placeholder = st.empty()

            for event in run_turn(
                client,
                model=config["model"],
                user_input=user_input,
                previous_response_id=st.session_state.previous_response_id,
                vector_store_id=config["vector_store_id"],
                system_prompt=config["system_prompt"],
            ):
                tag = event[0]

                if tag == "reasoning_delta":
                    reasoning_text += event[1]
                    reasoning_placeholder.markdown(
                        f"**Reasoning**\n\n{reasoning_text}"
                    )

                elif tag == "file_search_started":
                    _fs_placeholder = st.empty()
                    _fs_placeholder.markdown("**🔍 File search:** *searching…*")

                elif tag == "file_search_done":
                    queries, results = event[1], event[2]
                    label = f'"{queries[0]}"' if queries else "hr_policy"
                    _fs_placeholder.markdown(f"**🔍 File search:** {label}")
                    if results:
                        MAX_CHARS = 50
                        snippets = "\n---\n".join(
                            r["text"][:MAX_CHARS] + ("…" if len(r["text"]) > MAX_CHARS else "")
                            for r in results
                        )
                        st.code(snippets, language="text")

                elif tag == "tool_call_started":
                    _, call_id, name = event
                    st.markdown(f"**🔧 Tool call:** `{name}`")

                elif tag == "tool_call_finished":
                    _, call_id, name, result_json = event
                    try:
                        pretty = json.dumps(json.loads(result_json), indent=2)
                    except Exception:
                        pretty = result_json
                    st.code(pretty, language="json")

                elif tag == "text_delta":
                    answer_text += event[1]
                    answer_placeholder.markdown(answer_text)

                elif tag == "done":
                    st.session_state.previous_response_id = event[1]

                elif tag == "error":
                    st.error(f"Error: {event[1]}")

            status.update(label="Done", state="complete", expanded=False)

        # Ensure final answer is visible outside the status panel
        if answer_text:
            answer_placeholder.markdown(answer_text)

    st.session_state.history.append({"role": "assistant", "content": answer_text})
