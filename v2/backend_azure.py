"""
Azure OpenAI backend for the HR Chatbot v2.

Provides ``make_client()`` and ``get_config()`` using the Azure OpenAI Service
via the standard OpenAI SDK with a custom ``base_url``. Select this backend by
setting ``BACKEND=azure`` in your ``.env`` file.

Requirements
------------
- A gpt-5.x deployment with the Responses API enabled
  (``api_version >= 2025-04-01-preview``).
- A vector store created against your Azure OpenAI resource endpoint
  via ``python ingest_policy.py`` with ``BACKEND=azure``.

Required environment variables
--------------------------------
AZURE_OPENAI_API_KEY : str
    API key for your Azure OpenAI resource.
AZURE_OPENAI_ENDPOINT : str
    Full endpoint URL including ``/openai/v1``, e.g.
    ``https://<resource>.openai.azure.com/openai/v1``.
AZURE_OPENAI_MODEL : str
    Deployment name used as the ``model`` identifier in API calls.
AZURE_OPENAI_VECTOR_STORE_ID : str
    ID of the vector store created by ``ingest_policy.py``.

Optional environment variables
--------------------------------
HR_USER_NAME : str
    Name of the current HR chatbot user (default: ``"Alexander Verdad"``).
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DEPLOYMENT_NAME = os.environ["AZURE_OPENAI_MODEL"]


def make_client() -> OpenAI:
    """Instantiate and return an OpenAI client pointed at the Azure endpoint.

    Uses the standard ``openai.OpenAI`` client with ``base_url`` overridden to
    the Azure OpenAI endpoint, which exposes the same Responses API surface as
    the direct OpenAI API.
    """
    return OpenAI(
        base_url=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )


def get_config() -> dict:
    """Return the deployment name, vector store ID, and system prompt for this backend.

    Returns:
        A dict with keys:

        - ``model`` (str): Azure deployment name from ``AZURE_OPENAI_MODEL``.
        - ``vector_store_id`` (str): From ``AZURE_OPENAI_VECTOR_STORE_ID``.
        - ``system_prompt`` (str): HR assistant instructions including the
          current user's name from ``HR_USER_NAME``.
    """
    user = os.getenv("HR_USER_NAME", "Alexander Verdad")
    return {
        "model": DEPLOYMENT_NAME,
        "vector_store_id": os.environ["AZURE_OPENAI_VECTOR_STORE_ID"],
        "system_prompt": (
            f"You are a friendly HR assistant. You are tasked to assist the current "
            f"user: {user} on questions related to HR policies and their employee data. "
            f"When answering questions about the current user, assume they are {user} "
            f"unless they specify otherwise. Always consult the HR policy. Use all available tools to look up accurate data "
            f"before answering."
        ),
    }
