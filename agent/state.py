from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class AgentState(TypedDict):
    """State for the Neo4j Cypher agent"""
    # User input
    question: str
    
    # Query processing
    query_type: Optional[str]
    entities: Optional[Dict[str, Any]]
    cypher_query: Optional[str]
    
    # Execution results
    query_result: Optional[Any]
    
    # Final response
    response: Optional[str]
    
    # Error handling
    error: Optional[str]