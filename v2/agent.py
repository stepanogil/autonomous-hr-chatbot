"""
Responses API agent loop.

Yields tagged events consumed by the Streamlit frontend:
    ("reasoning_delta", str)
    ("tool_call_started", call_id, name)
    ("tool_call_finished", call_id, name, result_json)
    ("file_search_started",)
    ("file_search_done", queries, results)  # queries: list[str], results: list[dict]
    ("text_delta", str)
    ("done", response_id)
    ("error", message)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generator

from tools import TOOL_SCHEMAS, dispatch

if TYPE_CHECKING:
    import openai


def run_turn(
    client: "openai.OpenAI",
    *,
    model: str,
    user_input: str,
    previous_response_id: str | None,
    vector_store_id: str,
    system_prompt: str,
) -> Generator[tuple, None, None]:
    """Drive one user turn through the Responses API agent loop, yielding events as they arrive.

    Streams a response from the model, dispatches any function calls to local
    tool implementations, and feeds results back via ``previous_response_id``
    until the model emits a final text answer with no further tool calls.

    The ``file_search`` built-in tool is handled server-side; its results are
    included via ``include=["file_search_call.results"]`` and surfaced as
    ``file_search_done`` events — no local dispatch is required.

    Args:
        client: An ``openai.OpenAI`` or ``openai.AzureOpenAI`` instance.
        model: Model name or Azure deployment name (e.g. ``"gpt-5.2"``).
        user_input: The raw message text from the user for this turn.
        previous_response_id: The ``response.id`` from the prior turn, used by
            the Responses API to carry conversation context server-side.
            Pass ``None`` on the first turn of a new conversation.
        vector_store_id: ID of the OpenAI vector store containing the HR policy
            document, wired to the built-in ``file_search`` tool.
        system_prompt: The ``instructions`` string sent on every API call,
            establishing the assistant persona and current user context.

    Yields:
        Tagged tuples consumed by the Streamlit frontend:

        - ``("reasoning_delta", str)`` — incremental reasoning summary text.
        - ``("tool_call_started", call_id, name)`` — function call has begun.
        - ``("tool_call_finished", call_id, name, result_json)`` — local tool
          executed; ``result_json`` is the JSON-encoded return value.
        - ``("file_search_started",)`` — server-side file search has begun.
        - ``("file_search_done", queries, results)`` — search complete;
          ``queries`` is a ``list[str]`` of search terms used, ``results`` is
          a ``list[{"text": str, "score": float|None}]`` of retrieved chunks.
        - ``("text_delta", str)`` — incremental assistant answer text.
        - ``("done", response_id)`` — final response ID for the next turn.
        - ``("error", message)`` — unrecoverable API or dispatch error.
    """
    tools = TOOL_SCHEMAS + [
        {"type": "file_search", "vector_store_ids": [vector_store_id]}
    ]

    # The input for the very first call is the user message.
    # After tool calls, input becomes the function_call_output items.
    current_input: list[dict] = [{"role": "user", "content": user_input}]
    current_previous_id: str | None = previous_response_id
    is_first_call = True

    while True:
        kwargs: dict = dict(
            model=model,
            tools=tools,
            reasoning={"effort": "low", "summary": "auto"},
            instructions=system_prompt,
            input=current_input,
            include=["file_search_call.results"],
        )
        if current_previous_id:
            kwargs["previous_response_id"] = current_previous_id

        # Only pass user input on the first call; tool-output continuations
        # use previous_response_id to carry context.
        if not is_first_call:
            # Drop the role/content framing — input is now raw tool outputs.
            pass  # current_input is already set to tool outputs from prior iteration
        is_first_call = False

        pending_tool_outputs: list[dict] = []

        try:
            with client.responses.stream(**kwargs) as stream:
                for event in stream:
                    etype = event.type

                    if etype == "response.reasoning_summary_text.delta":
                        yield ("reasoning_delta", event.delta)

                    elif etype == "response.output_item.added":
                        item = event.item
                        if item.type == "function_call":
                            yield ("tool_call_started", item.call_id, item.name)
                        elif item.type == "file_search_call":
                            yield ("file_search_started",)

                    elif etype == "response.output_item.done":
                        item = event.item
                        if item.type == "function_call":
                            result_json = dispatch(item.name, item.arguments)
                            yield ("tool_call_finished", item.call_id, item.name, result_json)
                            pending_tool_outputs.append(
                                {
                                    "type": "function_call_output",
                                    "call_id": item.call_id,
                                    "output": result_json,
                                }
                            )
                        elif item.type == "file_search_call":
                            queries = getattr(item, "queries", []) or []
                            raw_results = getattr(item, "results", []) or []
                            results = [
                                {
                                    "text": getattr(r, "text", str(r)),
                                    "score": getattr(r, "score", None),
                                }
                                for r in raw_results
                            ]
                            yield ("file_search_done", queries, results)

                    elif etype == "response.output_text.delta":
                        yield ("text_delta", event.delta)

                    elif etype == "response.completed":
                        current_previous_id = event.response.id

        except Exception as exc:
            yield ("error", str(exc))
            return

        if pending_tool_outputs:
            # Feed tool results back; previous_response_id carries full context.
            current_input = pending_tool_outputs
        else:
            break

    yield ("done", current_previous_id)
