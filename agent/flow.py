from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict, Optional, List
from .state import AgentState
from .nodes import (
    classify_query,
    extract_entities,
    generate_cypher,
    execute_cypher,
    generate_response
)

def create_workflow() -> StateGraph:
    """Create the workflow for the Neo4j Cypher agent."""
    # Create a new graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("classify_query", classify_query)
    workflow.add_node("extract_entities", extract_entities)
    workflow.add_node("generate_cypher", generate_cypher)
    workflow.add_node("execute_cypher", execute_cypher)
    workflow.add_node("generate_response", generate_response)
    
    # Define the edges
    workflow.add_edge("classify_query", "extract_entities")
    workflow.add_edge("extract_entities", "generate_cypher")
    workflow.add_edge("generate_cypher", "execute_cypher")
    workflow.add_edge("execute_cypher", "generate_response")
    
    # Set entry point
    workflow.set_entry_point("classify_query")
    
    # Set conditional edges (if any)
    # For example, you could add error handling branches here
    
    # Set the final node
    workflow.add_edge("generate_response", END)
    
    # Compile the workflow
    return workflow.compile()

# Create the workflow instance
neo4j_agent_workflow = create_workflow()

def run_agent(question: str) -> Dict[str, Any]:
    """Run the agent with the given question."""
    # Initialize the state
    initial_state = {
        "question": question,
        "query_type": None,
        "entities": None,
        "cypher_query": None,
        "query_result": None,
        "response": None,
        "error": None
    }
    
    # Execute the workflow
    result = neo4j_agent_workflow.invoke(initial_state)
    
    # Return the final state
    return result