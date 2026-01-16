"""
LangGraph Multi-Agent System
3 specialized agents that communicate and collaborate:
1. Data Analyst Agent - analyzes dataset characteristics
2. Algorithm Selector Agent - decides best ML approach
3. Code Generator Agent - generates production code
"""

from typing import TypedDict, Annotated, Any
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
import pandas as pd
import numpy as np
from operator import add


# Define the shared state that agents pass between each other
class AgentState(TypedDict):
    """Shared state passed between all agents"""
    # Input data
    dataframe: Any  # pd.DataFrame
    problem_description: str
    
    # Agent communication messages
    messages: Annotated[list[str], add]  # Agents append messages here
    
    # Data Analyst Agent outputs
    data_analysis: dict
    data_insights: str
    
    # Algorithm Selector Agent outputs
    recommended_algorithm: str
    algorithm_reasoning: str
    alternative_algorithms: list[str]
    
    # Code Generator Agent outputs
    generated_code: str
    code_explanation: str
    
    # Final decision
    final_recommendation: dict


class MultiAgentSystem:
    """LangGraph-based multi-agent system for ML problem solving"""
    
    def __init__(self, model_name: str = "llama3.2:latest"):
        """Initialize the multi-agent system with LLM"""
        self.llm = ChatOllama(model=model_name, temperature=0.7)
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow with 3 agents"""
        
        # Create state graph
        workflow = StateGraph(AgentState)
        
        # Add agent nodes
        workflow.add_node("data_analyst", self.data_analyst_agent)
        workflow.add_node("algorithm_selector", self.algorithm_selector_agent)
        workflow.add_node("code_generator", self.code_generator_agent)
        workflow.add_node("final_decision", self.make_final_decision)
        
        # Define workflow edges
        workflow.set_entry_point("data_analyst")
        workflow.add_edge("data_analyst", "algorithm_selector")
        workflow.add_edge("algorithm_selector", "code_generator")
        workflow.add_edge("code_generator", "final_decision")
        workflow.add_edge("final_decision", END)
        
        return workflow.compile()
    
    def data_analyst_agent(self, state: AgentState) -> AgentState:
        """
        Agent 1: Data Analyst
        Analyzes dataset characteristics and provides insights
        """
        df = state["dataframe"]
        problem_desc = state["problem_description"]
        
        # Real data analysis
        n_rows = len(df)
        n_cols = len(df.columns)
        n_numeric = len(df.select_dtypes(include=[np.number]).columns)
        n_categorical = len(df.select_dtypes(include=['object', 'category']).columns)
        missing_percent = (df.isnull().sum().sum() / (n_rows * n_cols)) * 100
        
        # Find target column
        target_col = self._identify_target_column(df, problem_desc)
        target_info = self._analyze_target(df[target_col])
        
        # Get column info
        column_info = []
        for col in df.columns[:10]:  # First 10 columns
            dtype = str(df[col].dtype)
            unique = df[col].nunique()
            missing = df[col].isnull().sum()
            column_info.append(f"{col} ({dtype}): {unique} unique, {missing} missing")
        
        # Create analysis prompt for LLM
        analysis_prompt = f"""You are a Data Analyst Agent. Analyze this dataset:

Dataset: {n_rows} rows, {n_cols} columns
- Numeric columns: {n_numeric}
- Categorical columns: {n_categorical}
- Missing data: {missing_percent:.1f}%
- Target column: {target_col} ({target_info['type']}, {target_info['unique_values']} unique values)

Sample columns: {', '.join(df.columns[:5].tolist())}

Problem Description: {problem_desc}

Provide a concise analysis of:
1. What type of ML problem this is (classification/regression)
2. Key data characteristics that matter for algorithm selection
3. Any data quality concerns

Keep response under 150 words."""

        # Get LLM analysis
        response = self.llm.invoke(analysis_prompt)
        insights = response.content if hasattr(response, 'content') else str(response)
        if isinstance(insights, list):
            insights = str(insights)
        
        # Prepare structured analysis
        data_analysis = {
            "n_rows": n_rows,
            "n_cols": n_cols,
            "n_numeric": n_numeric,
            "n_categorical": n_categorical,
            "missing_percent": round(missing_percent, 2),
            "target_column": target_col,
            "target_type": target_info['type'],
            "n_unique_target": target_info['unique_values'],
            "problem_type": target_info['problem_type'],
            "columns": column_info[:5]
        }
        
        # Update state
        state["data_analysis"] = data_analysis
        state["data_insights"] = insights
        state["messages"].append(f"[Data Analyst]: Analyzed dataset. Found {target_info['problem_type']} problem with {n_rows} samples and {n_cols} features.")
        
        return state
    
    def algorithm_selector_agent(self, state: AgentState) -> AgentState:
        """
        Agent 2: Algorithm Selector
        Receives data analysis and decides best ML algorithm
        Communicates with Data Analyst's findings
        """
        data_analysis = state["data_analysis"]
        data_insights = state["data_insights"]
        messages = state["messages"]
        
        # Create selection prompt with previous agent's findings
        selection_prompt = f"""You are an Algorithm Selector Agent. Based on the Data Analyst's findings, select the best ML algorithm.

Data Analyst's Report:
{data_insights}

Key Statistics:
- Problem Type: {data_analysis['problem_type']}
- Samples: {data_analysis['n_rows']}
- Features: {data_analysis['n_cols']}
- Missing Data: {data_analysis['missing_percent']}%
- Target Classes: {data_analysis['n_unique_target']}

Previous Agent Messages:
{chr(10).join(messages)}

Recommend:
1. PRIMARY algorithm (specific sklearn model)
2. WHY this algorithm fits the data characteristics
3. TWO alternative algorithms

Format: Algorithm Name | Reason (1 sentence) | Alternative1, Alternative2

Keep response under 100 words."""

        # Get LLM recommendation
        response = self.llm.invoke(selection_prompt)
        recommendation = response.content if hasattr(response, 'content') else str(response)
        if isinstance(recommendation, list):
            recommendation = str(recommendation)
        
        # Parse recommendation (simple parsing)
        lines = recommendation.strip().split('\n')
        algorithm = "Random Forest"  # Default
        reasoning = recommendation
        alternatives = ["Logistic Regression", "Gradient Boosting"]
        
        # Try to extract structured info
        if '|' in recommendation:
            parts = recommendation.split('|')
            if len(parts) >= 3:
                algorithm = parts[0].strip()
                reasoning = parts[1].strip()
                alternatives = [a.strip() for a in parts[2].split(',')][:2]
        
        # Map to actual sklearn algorithms
        algorithm = self._map_to_sklearn_algorithm(algorithm, data_analysis)
        
        # Update state
        state["recommended_algorithm"] = algorithm
        state["algorithm_reasoning"] = reasoning
        state["alternative_algorithms"] = alternatives
        state["messages"].append(f"[Algorithm Selector]: Recommended {algorithm} based on data characteristics.")
        
        return state
    
    def code_generator_agent(self, state: AgentState) -> AgentState:
        """
        Agent 3: Code Generator
        Generates production-ready ML code based on previous agents' decisions
        """
        algorithm = state["recommended_algorithm"]
        data_analysis = state["data_analysis"]
        reasoning = state["algorithm_reasoning"]
        messages = state["messages"]
        
        # Create code generation prompt
        code_prompt = f"""You are a Code Generator Agent. Generate production-ready Python ML code.

Algorithm Selected: {algorithm}
Reasoning: {reasoning}
Problem Type: {data_analysis['problem_type']}
Features: {data_analysis['n_cols']}
Target Column: {data_analysis['target_column']}

Previous Agent Decisions:
{chr(10).join(messages[-2:])}

Generate complete sklearn pipeline code including:
1. Imports
2. Data preprocessing
3. Train/test split
4. Model training with {algorithm}
5. Evaluation metrics

Use variable name 'df' for dataframe, target column is '{data_analysis['target_column']}'.
Make code production-ready and well-commented.
Return ONLY valid Python code, no explanations outside comments."""

        # Get LLM code generation
        response = self.llm.invoke(code_prompt)
        generated_code = response.content if hasattr(response, 'content') else str(response)
        if isinstance(generated_code, list):
            generated_code = str(generated_code)
        
        # Clean code (remove markdown if present)
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1].split("```")[0].strip()
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0].strip()
        
        # Create explanation
        explanation = f"Generated {algorithm} pipeline based on {data_analysis['problem_type']} problem with {data_analysis['n_rows']} samples."
        
        # Update state
        state["generated_code"] = generated_code
        state["code_explanation"] = explanation
        state["messages"].append(f"[Code Generator]: Generated {algorithm} implementation with preprocessing pipeline.")
        
        return state
    
    def make_final_decision(self, state: AgentState) -> AgentState:
        """
        Final node: Consolidate all agent outputs into recommendation
        """
        final_rec = {
            "algorithm": state["recommended_algorithm"],
            "confidence": "high",
            "reasoning": state["algorithm_reasoning"],
            "data_summary": {
                "problem_type": state["data_analysis"]["problem_type"],
                "samples": state["data_analysis"]["n_rows"],
                "features": state["data_analysis"]["n_cols"],
                "target": state["data_analysis"]["target_column"]
            },
            "alternatives": state["alternative_algorithms"],
            "agent_collaboration": state["messages"]
        }
        
        state["final_recommendation"] = final_rec
        state["messages"].append("[System]: Multi-agent collaboration completed successfully.")
        
        return state
    
    def _identify_target_column(self, df: pd.DataFrame, problem_desc: str) -> str:
        """Identify target column from dataset"""
        col_names_lower = [col.lower() for col in df.columns]
        target_keywords = ['target', 'label', 'class', 'churn', 'fraud', 'default', 'outcome', 'result', 'y', 'price', 'sales']
        
        for keyword in target_keywords:
            for idx, col in enumerate(col_names_lower):
                if keyword == col or keyword in col:
                    return df.columns[idx]
        
        # Default to last column
        return df.columns[-1]
    
    def _analyze_target(self, target_series: pd.Series) -> dict:
        """Analyze target variable"""
        n_unique = target_series.nunique()
        is_numeric = pd.api.types.is_numeric_dtype(target_series)
        
        if is_numeric and n_unique > 20:
            return {
                "type": "continuous",
                "unique_values": n_unique,
                "problem_type": "Regression"
            }
        else:
            return {
                "type": "categorical",
                "unique_values": n_unique,
                "problem_type": f"{n_unique}-class Classification"
            }
    
    def _map_to_sklearn_algorithm(self, algorithm_name: str, data_analysis: dict) -> str:
        """Map LLM algorithm name to sklearn model"""
        algo_lower = algorithm_name.lower()
        
        if "random forest" in algo_lower:
            return "Random Forest"
        elif "logistic" in algo_lower:
            return "Logistic Regression"
        elif "gradient boost" in algo_lower or "xgboost" in algo_lower:
            return "Gradient Boosting"
        elif "svm" in algo_lower or "support vector" in algo_lower:
            return "Support Vector Machine"
        elif "decision tree" in algo_lower:
            return "Decision Tree"
        elif "neural" in algo_lower or "mlp" in algo_lower:
            return "Neural Network"
        elif "naive bayes" in algo_lower:
            return "Naive Bayes"
        else:
            # Default based on problem type
            if "Classification" in data_analysis.get('problem_type', ''):
                return "Random Forest"
            else:
                return "Linear Regression"
    
    def run_analysis(self, df: pd.DataFrame, problem_description: str) -> dict:
        """
        Execute the multi-agent workflow
        Returns final recommendation with all agent outputs
        """
        # Initialize state
        initial_state = {
            "dataframe": df,
            "problem_description": problem_description,
            "messages": [],
            "data_analysis": {},
            "data_insights": "",
            "recommended_algorithm": "",
            "algorithm_reasoning": "",
            "alternative_algorithms": [],
            "generated_code": "",
            "code_explanation": "",
            "final_recommendation": {}
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return {
            "success": True,
            "algorithm": final_state["recommended_algorithm"],
            "reasoning": final_state["algorithm_reasoning"],
            "code": final_state["generated_code"],
            "data_analysis": final_state["data_analysis"],
            "data_insights": final_state["data_insights"],
            "alternatives": final_state["alternative_algorithms"],
            "agent_messages": final_state["messages"],
            "final_recommendation": final_state["final_recommendation"]
        }
