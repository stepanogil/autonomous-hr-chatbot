import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DEPLOYMENT_NAME = os.environ["AZURE_OPENAI_MODEL"]


def make_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )


def get_config() -> dict:
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
