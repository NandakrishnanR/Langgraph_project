"""Minimal LangGraph workflow with three cooperating agents using Ollama."""

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Shared conversational state carried between agents."""

    messages: Annotated[list, add_messages]
    generated_code: str  # Extracted Python code from CodeGenerator


# Single local model reused by all agents (no external API required)
model = ChatOllama(model="llama3.1", temperature=0.2)


def make_agent(role: str, idx: int, goal: str, extract_code: bool = False):
    """Create a LangGraph node that appends an agent reply to the message list."""

    def node(state: AgentState) -> AgentState:
        # Ultra-concise prompt for speed
        guidance = HumanMessage(content=f"{goal}")
        reply = model.invoke(state["messages"] + [guidance])
        
        # Add agent number prefix
        msg_content = f"Agent {idx}: {reply.content}"
        result = {"messages": [AIMessage(content=msg_content, name=f"{role}")]}
        
        # Extract Python code if this is the code generator
        if extract_code:
            import re
            code_blocks = re.findall(r'```python\n(.*?)```', reply.content, re.DOTALL)
            if code_blocks:
                result["generated_code"] = code_blocks[0].strip()
            else:
                # Fallback: try to extract any Python-like code
                lines = reply.content.split('\n')
                code_lines = [l for l in lines if any(kw in l for kw in ['import', 'def ', 'class ', 'df', 'model', 'fit', 'predict'])]
                if code_lines:
                    result["generated_code"] = '\n'.join(code_lines)
        
        return result

    return node


# Define three ML workflow agents with ultra-fast prompts
data_cleaner = make_agent(
    "DataCleaner", 1,
    "List ONLY (2-3 bullets): missing %, data types (numeric/string), 1 action. No sentences."
)
algorithm_selector = make_agent(
    "AlgorithmSelector", 2,
    "Output ONLY: Problem type: [classification/regression/clustering]. Best Algorithm: [name]. Done."
)
code_generator = make_agent(
    "CodeGenerator", 3,
    "Generate ONLY Python code in ```python``` block. Imports, load data, preprocess, train. No text.",
    extract_code=True
)


# Build the state machine
graph = StateGraph(AgentState)
graph.add_node("data_cleaner", data_cleaner)
graph.add_node("algorithm_selector", algorithm_selector)
graph.add_node("code_generator", code_generator)

graph.set_entry_point("data_cleaner")
graph.add_edge("data_cleaner", "algorithm_selector")
graph.add_edge("algorithm_selector", "code_generator")
graph.add_edge("code_generator", END)

# Compiled graph ready for invocation
workflow = graph.compile()


def run_workflow(prompt: str):
    """Convenience helper to invoke the workflow from a plain prompt."""

    initial_state: AgentState = {
        "messages": [HumanMessage(content=prompt)],
        "generated_code": ""
    }
    result = workflow.invoke(initial_state)
    return result["messages"], result.get("generated_code", "")


__all__ = ["workflow", "run_workflow"]