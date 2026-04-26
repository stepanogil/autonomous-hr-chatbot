import os
import openai
from dotenv import load_dotenv

load_dotenv()


def make_client() -> openai.OpenAI:
    return openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def get_config() -> dict:
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
