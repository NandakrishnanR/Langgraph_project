"""Tiny aiohttp server exposing the LangGraph workflow."""

import asyncio
import io
import json
from typing import Dict, Any

import pandas as pd
from aiohttp import web
from langchain_core.messages import AIMessage, HumanMessage

from graph import run_workflow


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def invoke_graph(request: web.Request) -> web.Response:
    """Handle CSV file upload and run ML analysis workflow."""
    reader = await request.multipart()
    csv_data = None
    
    async for field in reader:
        if field.name == 'file':
            content = await field.read()
            try:
                df = pd.read_csv(io.BytesIO(content))

                def truncate(value: Any, max_len: int = 40) -> str:
                    text = str(value)
                    return text if len(text) <= max_len else text[:max_len] + "..."

                def build_summary(frame: pd.DataFrame) -> Dict[str, Any]:
                    rows, cols = frame.shape
                    max_cols = 12
                    column_names = list(frame.columns[:max_cols])
                    if cols > max_cols:
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
                        sample_row = {
                            col: truncate(val)
                            for col, val in frame.iloc[0].items()
                            if col in frame.columns[:max_cols]
                        }

                    numeric_preview = {}
                    numeric_subset = frame.select_dtypes(include="number").iloc[:, :5]
                    if not numeric_subset.empty:
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
                summary_text = json.dumps(summary_payload, separators=(",", ":"))
                if len(summary_text) > 1800:
                    summary_text = summary_text[:1800] + "..."
                csv_data = summary_text
            except Exception as e:
                return web.json_response({"error": f"Invalid CSV: {str(e)}"}, status=400)
    
    if not csv_data:
        return web.json_response({"error": "CSV file is required"}, status=400)
    
    prompt = f"Data: {csv_data}"
    print(f"[SERVER] Starting workflow...")
    messages, generated_code = await asyncio.to_thread(run_workflow, prompt)
    print(f"[SERVER] Workflow complete. Code length: {len(generated_code)} chars, Messages: {len(messages)}")

    def to_dict(msg):
        role = msg.name or (msg.type if hasattr(msg, "type") else "assistant")
        return {"role": role, "content": msg.content}

    ai_steps = [to_dict(m) for m in messages if isinstance(m, AIMessage)]
    conversation = [to_dict(m) for m in messages if isinstance(m, (AIMessage, HumanMessage))]

    return web.json_response({
        "agents": ai_steps,
        "messages": conversation,
        "code": generated_code
    })


@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        resp = web.Response(status=204)
    else:
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
    app = web.Application(middlewares=[cors_middleware])
    app.add_routes(
        [
            web.get("/health", health),
            web.post("/api/run", invoke_graph),
        ]
    )
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=8000)