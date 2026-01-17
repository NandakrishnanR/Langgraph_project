"""Tiny aiohttp server exposing the LangGraph workflow."""

import asyncio
import io
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
                csv_summary = f"""Dataset Info:
- Shape: {df.shape[0]} rows, {df.shape[1]} columns
- Columns: {', '.join(df.columns.tolist())}
- Data types: {df.dtypes.to_dict()}
- Missing values: {df.isnull().sum().to_dict()}
- First 3 rows:\n{df.head(3).to_string()}"""
                csv_data = csv_summary
            except Exception as e:
                return web.json_response({"error": f"Invalid CSV: {str(e)}"}, status=400)
    
    if not csv_data:
        return web.json_response({"error": "CSV file is required"}, status=400)
    
    prompt = f"Analyze this dataset and recommend an ML solution:\n\n{csv_data}"
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