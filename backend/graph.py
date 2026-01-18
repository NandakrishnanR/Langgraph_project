"""Defines the LangGraph workflow used by the backend agents."""

import os
import re
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Shape of the shared memory passed between nodes."""

    messages: Annotated[list, add_messages]  # chat history seen by every agent
    generated_code: str  # latest Python snippet produced by the code agent


def _content_to_text(message: AIMessage) -> str:
    """Turn any AIMessage content into a plain string."""

    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content

    parts = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                text = block.get("text") or block.get("output")
                if text:
                    parts.append(text)
            else:
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
    if parts:
        return "\n".join(parts)
    return str(content)


# One local model reused by all agents (Ollama keeps it warm for 10 minutes).
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.1")
model = ChatOllama(
    model=MODEL_NAME,
    temperature=0.1,
    num_predict=512,
    num_ctx=2048,
    keep_alive="10m",
    top_p=0.85,
    top_k=40,
)


def make_agent(role: str, idx: int, goal: str, extract_code: bool = False):
    """Create a LangGraph node wrapper around the chat model."""

    def node(state: AgentState) -> AgentState:
        # Tell the model what this agent should focus on.
        guidance = HumanMessage(content=f"{goal}")

        # Keep only three previous turns to save tokens.
        history = state["messages"][-3:]
        reply = model.invoke(history + [guidance])
        reply_text = _content_to_text(reply)

        # Tag the response so the frontend knows which agent spoke.
        msg_content = f"Agent {idx}: {reply_text}"
        result = {"messages": [AIMessage(content=msg_content, name=f"{role}")]}
        
        # Optionally capture code blocks for the UI.
        if extract_code:
            code_blocks = re.findall(r'```(?:python)?\s*(.*?)```', reply_text, re.DOTALL | re.IGNORECASE)
            if code_blocks:
                result["generated_code"] = code_blocks[-1].strip()
            else:
                # If nothing is fenced off, return the raw reply instead.
                result["generated_code"] = reply_text.strip()
        
        return result

    return node


# Agents: all share the same model but use different goals.
data_cleaner = make_agent(
    "DataCleaner", 1,
    "Summarize data issues in <=2 sentences: missing %, dtype notes, obvious scaling needs."
)
algorithm_selector = make_agent(
    "AlgorithmSelector", 2,
    (
        "Recommend exactly one algorithm. Respond ONLY as JSON with keys task, model, reason. "
        "Set task to classification or regression based on target characteristics; set model to the precise sklearn class name; "
        "keep reason under 12 words."
    )
)
code_generator = make_agent(
    "CodeGenerator", 3,
    (
        "Produce a full runnable Python script in ```python``` fences. "
        "Read the latest Agent 2 JSON to determine task and model and use only that estimator (no extra algorithms). "
        "Steps: import pandas, numpy, scikit-learn tools needed for the chosen model, plus matplotlib/seaborn; "
        "set csv_path and target_column placeholders; load data; handle missing values; detect categorical vs numeric features; "
        "build a preprocessing pipeline matching the model (encoder/standardizer as required); perform train/test split; "
        "train the recommended estimator; compute accuracy along with precision/recall/F1 for classification or R2/MSE for regression; "
        "plot a confusion matrix for classification or residual scatter for regression; "
        "print metrics clearly."
    ),
    extract_code=True
)


# Build LangGraph: register nodes and connect them in order.
graph = StateGraph(AgentState)
graph.add_node("data_cleaner", data_cleaner)
graph.add_node("algorithm_selector", algorithm_selector)
graph.add_node("code_generator", code_generator)

graph.set_entry_point("data_cleaner")
graph.add_edge("data_cleaner", "algorithm_selector")
graph.add_edge("algorithm_selector", "code_generator")
graph.add_edge("code_generator", END)

# Finalize the graph so we can call ``workflow.invoke`` later.
workflow = graph.compile()


def run_workflow(prompt: str):
    """Kick off the graph given the CSV summary prompt."""

    initial_state: AgentState = {
        "messages": [HumanMessage(content=prompt)],
        "generated_code": ""
    }
    # Run each node one after another.
    result = workflow.invoke(initial_state)
    return result["messages"], result.get("generated_code", "")


__all__ = ["workflow", "run_workflow"]