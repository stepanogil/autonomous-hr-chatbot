# HR Chatbot — v2 (OpenAI Responses API)

A modernized rewrite of the [original HR chatbot](../README.md) using an agent loop via **OpenAI Responses API** directly — no LangChain, no Pinecone. Surfaces real model reasoning via `gpt-5.2`'s reasoning summaries and demonstrates the Responses API's native function calling and `file_search` built-in tool.

#### Sample Chat

![sample_chat](assets/image.png)

## What changed vs. the 2023 version

| | Original (2023) | v2 (2026) |
|---|---|---|
| **Framework** | LangChain `0.0.220` | None — pure OpenAI SDK |
| **Model** | `gpt-3.5-turbo` | `gpt-5.2` |
| **"Thought" panel** | LangChain `verbose=True` scratchpad text | Real reasoning summaries from the model |
| **RAG** | Pinecone vector DB + manual embeddings | OpenAI `file_search` built-in tool |
| **Employee data tool** | `PythonAstREPLTool` (arbitrary code exec) | Typed function tools |
| **Frontend** | `streamlit-chat` (deprecated) | Native `st.chat_message` / `st.status` |
| **State** | Full message replay each turn | `previous_response_id` (server-side) |

## Tech stack

- [OpenAI Python SDK](https://github.com/openai/openai-python) `>=1.55`
- [Streamlit](https://streamlit.io/) `>=1.40`
- [pandas](https://pandas.pydata.org/) — employee data
- [python-dotenv](https://github.com/theskumar/python-dotenv)

## Setup

### 1. Create and activate a virtual environment

```bash
cd v2
python -m venv .venv
```

**Activate:**

- macOS / Linux: `source .venv/bin/activate`
- Windows (CMD): `.venv\Scripts\activate.bat`
- Windows (PowerShell): `.venv\Scripts\Activate.ps1`

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

> **Pick the path that matches where your LLM is hosted — Path A for OpenAI, Path B for Azure OpenAI.**

---

### Path A — OpenAI

#### A1. Configure environment

```bash
cp .env.example .env
```

Fill in `OPENAI_API_KEY`. Leave `OPENAI_VECTOR_STORE_ID` blank for now.

#### A2. Ingest the HR policy (one-time)

```bash
python ingest_policy.py
```

Copy the printed `vs_…` ID into your `.env` as `OPENAI_VECTOR_STORE_ID`.

#### A3. Run

```bash
streamlit run app.py
```

---

### Path B — Azure OpenAI

Requirements:
- A `gpt-5.n` deployment (or any reasoning model that supports the Responses API)

#### B1. Configure environment

```bash
cp .env.example .env
```

Set `BACKEND=azure` and fill in all `AZURE_OPENAI_*` variables. Leave `AZURE_OPENAI_VECTOR_STORE_ID` blank for now.

#### B2. Ingest the HR policy (one-time)

```bash
python ingest_policy.py
```

Copy the printed `vs_…` ID into your `.env` as `AZURE_OPENAI_VECTOR_STORE_ID`.


#### B3. Run

```bash
streamlit run app.py
```

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI — renders reasoning panel, tool traces, final answer |
| `agent_loop.py` | Responses API streaming loop — dispatches tool calls, yields events |
| `tools.py` | Typed function tools + JSON schemas + dispatch table |
| `backend_local.py` | OpenAI client + config |
| `backend_azure.py` | AzureOpenAI client + config |
| `ingest_policy.py` | One-time script to create vector store and upload `hr_policy.txt` |

---

## Sample questions to try

- "How many vacation leaves do I have left?"
- "What's the policy on unused vacation leave?"
- "If I encash 10 unused vacation days, how much will I be paid?"
- "Who are the direct reports of Joseph Santos?"
- "Can I apply for sick leave while on probation?"
