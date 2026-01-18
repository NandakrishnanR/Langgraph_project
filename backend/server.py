"""aiohttp bridge that accepts CSV uploads and runs the LangGraph workflow.

Each request performs the following steps:
1. Parse multipart form data and extract the uploaded CSV bytes.
2. Load the CSV into a DataFrame and distill a compact JSON summary.
3. Offload the LangGraph state machine to a worker thread via ``run_workflow``.
4. Serialize agent conversation history plus generated code back to the caller.
"""


import asyncio
import io
import json
from typing import Dict, Any

import pandas as pd
from aiohttp import web
from langchain_core.messages import AIMessage, HumanMessage

from graph import run_workflow


async def health(request: web.Request) -> web.Response:
    """Simple health probe so external monitors can verify liveness."""

    # Respond immediately without touching LangGraph or heavy dependencies.
    return web.json_response({"status": "ok"})


async def invoke_graph(request: web.Request) -> web.Response:
    """Handle CSV file upload and orchestrate the ML analysis pipeline.

    The function converts multipart form data into a compact JSON summary and
    then calls ``run_workflow`` in a background thread so the event loop stays
    responsive while LangGraph executes.
    """

    # Parse the incoming multipart/form-data stream incrementally to avoid
    # buffering the entire request unnecessarily.
    reader = await request.multipart()

    # Holds the JSON summary that will seed LangGraph once extracted.
    csv_data = None
    
    async for field in reader:
        if field.name == 'file':
            # Read the entire uploaded file into memory (datasets are expected to
            # be moderate in size during interactive use).
            content = await field.read()
            try:
                # Convert raw bytes into a pandas DataFrame for rich inspection.
                df = pd.read_csv(io.BytesIO(content))

                def truncate(value: Any, max_len: int = 40) -> str:
                    """Clamp long textual values so the JSON payload stays small."""

                    text = str(value)
                    return text if len(text) <= max_len else text[:max_len] + "..."

                def build_summary(frame: pd.DataFrame) -> Dict[str, Any]:
                    """Assemble a concise schema + statistics snapshot for LangGraph."""

                    # Capture overall shape so agents know dataset breadth/width.
                    rows, cols = frame.shape
                    max_cols = 12
                    column_names = list(frame.columns[:max_cols])
                    if cols > max_cols:
                        # Signal omitted columns when the dataset has a wide schema.
                        column_names.append("...")

                    dtype_snapshot = {
                        col: str(frame[col].dtype) for col in frame.columns[:max_cols]
                    }
                    missing_snapshot = {
                        col: int(frame[col].isnull().sum())
                        for col in frame.columns[:max_cols]
                        if frame[col].isnull().any()
                    }

                    sample_row = {}
                    if rows:
                        # Provide one representative row so the agents glimpse values.
                        sample_row = {
                            col: truncate(val)
                            for col, val in frame.iloc[0].items()
                            if col in frame.columns[:max_cols]
                        }

                    numeric_preview = {}
                    numeric_subset = frame.select_dtypes(include="number").iloc[:, :5]
                    if not numeric_subset.empty:
                        # ``describe`` delivers statistics such as mean/std/min/max.
                        describe = numeric_subset.describe().round(3).iloc[1:]
                        numeric_preview = {
                            col: {idx: truncate(val) for idx, val in describe[col].items()}
                            for col in describe.columns
                        }

                    return {
                        "rows": int(rows),
                        "cols": int(cols),
                        "columns": column_names,
                        "dtypes": dtype_snapshot,
                        "missing": missing_snapshot,
                        "sample": sample_row,
                        "numeric_stats": numeric_preview,
                    }

                summary_payload = build_summary(df)
                # Compact JSON (no whitespace) keeps the prompt well under context
                # limits for most local LLMs.
                summary_text = json.dumps(summary_payload, separators=(",", ":"))
                if len(summary_text) > 1800:
                    # Guardrail: truncate oversized datasets so prompts remain sane.
                    summary_text = summary_text[:1800] + "..."
                csv_data = summary_text
            except Exception as e:
                # Gracefully report parsing issues (bad CSV, wrong encoding, etc.).
                return web.json_response({"error": f"Invalid CSV: {str(e)}"}, status=400)
    
    if not csv_data:
        # No file field or empty upload: short-circuit with a clear error.
        return web.json_response({"error": "CSV file is required"}, status=400)
    
    # Seed message injected into LangGraph; agents treat this like user input.
    prompt = f"Data: {csv_data}"
    print(f"[SERVER] Starting workflow...")

    # ``run_workflow`` is synchronous; ``asyncio.to_thread`` stops it from
    # blocking aiohttp's event loop while the agents execute sequentially.
    messages, generated_code = await asyncio.to_thread(run_workflow, prompt)
    print(f"[SERVER] Workflow complete. Code length: {len(generated_code)} chars, Messages: {len(messages)}")

    def to_dict(msg):
        """Normalize LangChain messages to serializable role/content pairs."""

        role = msg.name or (msg.type if hasattr(msg, "type") else "assistant")
        return {"role": role, "content": msg.content}

    # AI-only steps show each agent's contribution for the frontend timeline.
    ai_steps = [to_dict(m) for m in messages if isinstance(m, AIMessage)]
    # Full conversation keeps both human seed and assistant replies for context.
    conversation = [to_dict(m) for m in messages if isinstance(m, (AIMessage, HumanMessage))]

    return web.json_response({
        "agents": ai_steps,
        "messages": conversation,
        "code": generated_code
    })


@web.middleware
async def cors_middleware(request: web.Request, handler):
    """Permit cross-origin requests so the Vite dev server can reach aiohttp."""

    if request.method == "OPTIONS":
        # Pre-flight requests receive an empty 204 response immediately.
        resp = web.Response(status=204)
    else:
        # Delegate to the target handler and decorate the outgoing response.
        resp = await handler(request)

    resp.headers.update(
        {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )
    return resp


def create_app() -> web.Application:
    """Build the aiohttp application with routes and middleware attached."""

    app = web.Application(middlewares=[cors_middleware])
    app.add_routes(
        [
            web.get("/health", health),
            web.post("/api/run", invoke_graph),
        ]
    )
    return app


if __name__ == "__main__":
    # Allow external clients (frontend dev server) to reach the backend on port 8000.
    web.run_app(create_app(), host="0.0.0.0", port=8000)