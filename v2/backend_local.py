"""
Local OpenAI backend for the HR Chatbot v2.

Provides ``make_client()`` and ``get_config()`` using the standard OpenAI API
(platform.openai.com). Select this backend by setting ``BACKEND=local`` (the
default) in your ``.env`` file.

Required environment variables
--------------------------------
OPENAI_API_KEY : str
    Your OpenAI platform API key (``sk-...``).
OPENAI_VECTOR_STORE_ID : str
    ID of the OpenAI vector store created by ``ingest_policy.py``.

Optional environment variables
--------------------------------
OPENAI_MODEL : str
    Model name to use (default: ``"gpt-5.2"``).
HR_USER_NAME : str
    Name of the current HR chatbot user (default: ``"Alexander Verdad"``).
"""

import os
import openai
from dotenv import load_dotenv

load_dotenv()


def make_client() -> openai.OpenAI:
    """Instantiate and return an OpenAI client using ``OPENAI_API_KEY``."""
    return openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def get_config() -> dict:
    """Return the model name, vector store ID, and system prompt for this backend.

    Returns:
        A dict with keys:

        - ``model`` (str): Model identifier from ``OPENAI_MODEL`` env var.
        - ``vector_store_id`` (str): From ``OPENAI_VECTOR_STORE_ID`` env var.
        - ``system_prompt`` (str): HR assistant instructions including the
          current user's name from ``HR_USER_NAME``.
    """
    user = os.getenv("HR_USER_NAME", "Alexander Verdad")
    return {
        "model": os.getenv("OPENAI_MODEL", "gpt-5.2"),
        "vector_store_id": os.environ["OPENAI_VECTOR_STORE_ID"],
        "system_prompt": (
            f"You are a friendly HR assistant. You are tasked to assist the current "
            f"user: {user} on questions related to HR policies and their employee data. "
            f"When answering questions about the current user, assume they are {user} "
            f"unless they specify otherwise. Use your tools to look up accurate data "
            f"before answering."
        ),
    }
