"""LangGraph state machine powering the backend agents.

This module wires three specialized LangChain agents—data cleaning, algorithm
selection, and code generation—into a sequential LangGraph workflow. The graph
shares conversation state plus any generated Python code, enabling the aiohttp
backend to report intermediate reasoning alongside executable scripts.
"""

import os
import re
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Container passed between nodes; LangGraph merges returned keys."""

    # ``messages`` accumulates HumanMessage/AIMessage entries as agents reply.
    messages: Annotated[list, add_messages]
    # ``generated_code`` captures the latest ```python``` block from the generator.
    generated_code: str


def _content_to_text(message: AIMessage) -> str:
    """Normalize heterogeneous LangChain message formats into plain text."""

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


# Single local model reused by every node; no API keys required.
# ``keep_alive`` reduces cold starts while ``num_predict`` keeps outputs concise.
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
    """Factory producing node callables compatible with LangGraph.

    Parameters
    ----------
    role: str
        Label stored on the outgoing ``AIMessage`` so the frontend can render it.
    idx: int
        Human-friendly index appended to the content for traceability.
    goal: str
        Prompt fragment injected as a ``HumanMessage`` each time the node runs.
    extract_code: bool
        When true, the node captures ```python``` blocks into ``generated_code``.
    """

    def node(state: AgentState) -> AgentState:
        # Inject role-specific guidance so the agent understands its objective.
        guidance = HumanMessage(content=f"{goal}")

        # Preserve only the last few exchanges to minimise context window usage.
        history = state["messages"][-3:]
        reply = model.invoke(history + [guidance])
        reply_text = _content_to_text(reply)

        # Prefix response with agent identifier for clear timeline display.
        msg_content = f"Agent {idx}: {reply_text}"
        result = {"messages": [AIMessage(content=msg_content, name=f"{role}")]}
        
        # Optionally capture executable snippets for downstream rendering.
        if extract_code:
            code_blocks = re.findall(r'```(?:python)?\s*(.*?)```', reply_text, re.DOTALL | re.IGNORECASE)
            if code_blocks:
                result["generated_code"] = code_blocks[-1].strip()
            else:
                # Fallback: expose the full reply so users still see attempt details.
                result["generated_code"] = reply_text.strip()
        
        return result

    return node


# --- Agent definitions ----------------------------------------------------
# Each agent reuses ``make_agent`` with a tailored goal description.
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


# --- Graph assembly -------------------------------------------------------
# Register each callable as a node and connect them sequentially.
graph = StateGraph(AgentState)
graph.add_node("data_cleaner", data_cleaner)
graph.add_node("algorithm_selector", algorithm_selector)
graph.add_node("code_generator", code_generator)

graph.set_entry_point("data_cleaner")
graph.add_edge("data_cleaner", "algorithm_selector")
graph.add_edge("algorithm_selector", "code_generator")
graph.add_edge("code_generator", END)

# Cache a compiled executor; compilation resolves the topology to a runnable graph.
workflow = graph.compile()


def run_workflow(prompt: str):
    """Invoke the compiled LangGraph workflow with a human seed message."""

    initial_state: AgentState = {
        "messages": [HumanMessage(content=prompt)],
        "generated_code": ""
    }
    # ``invoke`` executes each node synchronously following the defined edges.
    result = workflow.invoke(initial_state)
    return result["messages"], result.get("generated_code", "")


__all__ = ["workflow", "run_workflow"]