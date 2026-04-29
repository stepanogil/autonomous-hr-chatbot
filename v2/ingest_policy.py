"""
One-time script: upload hr_policy.txt into an OpenAI vector store.

Usage:
    cd v2
    python ingest_policy.py

Prints the vector store ID — paste it into your .env as OPENAI_VECTOR_STORE_ID.
For Azure, set BACKEND=azure and provide AZURE_OPENAI_* vars before running.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

backend = os.getenv("BACKEND", "local")
print(f"Backend: {backend}")
if backend == "azure":
    from backend_azure import make_client
else:
    from backend_local import make_client

policy_path = Path(__file__).parent / "hr_policy.txt"
if not policy_path.exists():
    print(f"ERROR: {policy_path} not found.", file=sys.stderr)
    sys.exit(1)

client = make_client()

print("Creating vector store...")
vs = client.vector_stores.create(name="hr-policy")
print(f"  Vector store created: {vs.id}")

print(f"Uploading {policy_path.name}...")
with open(policy_path, "rb") as f:
    client.vector_stores.files.upload_and_poll(vector_store_id=vs.id, file=f)

print("\nDone. Add this to your .env:\n")
env_key = "OPENAI_VECTOR_STORE_ID" if backend == "local" else "AZURE_OPENAI_VECTOR_STORE_ID"
print(f"  {env_key}={vs.id}\n")
