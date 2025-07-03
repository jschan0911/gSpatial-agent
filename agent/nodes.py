from typing import Dict, Any, TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
import os
import re
import json
from neo4j import GraphDatabase

# Import prompts from the local prompts module
from .prompts import (
    classification_prompt,
    entity_extraction_prompt,
    cypher_generation_prompt,
    response_generation_prompt
)

# Initialize LLM
llm = ChatOpenAI(
    model_name=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Initialize Neo4j connection
def get_neo4j_connection():
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(
            os.getenv("NEO4J_USERNAME"),
            os.getenv("NEO4J_PASSWORD")
        )
    )

def classify_query(state: Dict[str, Any]) -> Dict[str, Any]:
    """Classify the type of the user's query."""
    chain = classification_prompt | llm
    result = chain.invoke({
        "input": state["question"],
        "schema": ""  # Add schema if needed
    })
    
    # Clean and standardize the query type
    query_type = result.content.strip().upper()
    valid_types = {"TOPOLOGICAL", "SET", "BUFFER", "SINGLE", "DISTANCE"}
    
    # Default to TOPOLOGICAL if the response is not a valid type
    if query_type not in valid_types:
        query_type = "TOPOLOGICAL"
        
    return {"query_type": query_type}

def extract_entities(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract entities from the user's query."""
    chain = entity_extraction_prompt | llm
    result = chain.invoke({"input": state["question"]})
    
    # Try to parse the JSON response, fallback to raw text if parsing fails
    try:
        entities = json.loads(result.content.strip())
    except json.JSONDecodeError:
        entities = result.content.strip()
        
    return {"entities": entities}

def generate_cypher(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a Cypher query based on the query type and entities with retry context."""
    # Prepare the input for the Cypher generation prompt
    chain = cypher_generation_prompt | llm
    
    # Convert entities to string if it's a dictionary
    entities_str = state["entities"]
    if isinstance(entities_str, dict):
        entities_str = json.dumps(entities_str, ensure_ascii=False, indent=2)
    
    # Prepare the prompt input
    prompt_input = {
        "query_type": state["query_type"],
        "entities": entities_str,
        "input": state["question"],
        "schema": ""  # Add schema if needed
    }
    
    # Add error context if this is a retry
    if state.get("error_context"):
        error_ctx = state["error_context"]
        prompt_input["error_context"] = (
            "The previous query failed with the following error:\n"
            f"Error: {error_ctx.get('last_error', 'Unknown error')}\n"
            f"Attempt: {error_ctx.get('attempts', 0)} of {state.get('retry_context', {}).get('max_attempts', 5)}\n"
            "Previous queries that failed:\n" + 
            "\n".join([f"- {q}" for q in error_ctx.get('previous_queries', [])[-3:]])
        )
    
    try:
        result = chain.invoke(prompt_input)
        
        # Extract the Cypher query from markdown code blocks
        cypher_raw = result.content
        m = re.search(r"```(?:cypher)?\n([\s\S]*?)```$", cypher_raw, re.MULTILINE)
        cypher = m.group(1).strip() if m else cypher_raw.strip()
        
        # Clean up the query
        cypher = cypher.replace("```", "").strip()
        
        return {"cypher_query": cypher, "error": None}
        
    except Exception as e:
        return {
            "cypher_query": None,
            "error": f"Failed to generate Cypher query: {str(e)}"
        }

def execute_cypher(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the generated Cypher query against Neo4j."""
    # Initialize retry context if not exists
    if "retry_context" not in state:
        state["retry_context"] = {
            "attempts": 0,
            "max_attempts": 5,
            "last_error": None,
            "previous_queries": [],
            "status": "PENDING"
        }
    
    # Add current query to history before execution
    if state["cypher_query"]:
        state["retry_context"]["previous_queries"].append(state["cypher_query"])
    
    driver = get_neo4j_connection()
    try:
        with driver.session() as session:
            result = session.run(state["cypher_query"])
            records = [dict(record) for record in result]
            
            # Update retry context on success
            state["retry_context"]["status"] = "SUCCESS"
            state["retry_context"]["last_error"] = None
            
            return {
                "query_result": records, 
                "error": None,
                "retry_context": state["retry_context"]
            }
            
    except Exception as e:
        error_msg = str(e)
        state["retry_context"]["status"] = "ERROR"
        state["retry_context"]["last_error"] = error_msg
        state["retry_context"]["attempts"] += 1
        
        return {
            "query_result": None, 
            "error": error_msg,
            "retry_context": state["retry_context"]
        }
    finally:
        driver.close()

def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a natural language response based on the query results."""
    if state.get("error"):
        return {"response": f"죄송합니다. 쿼리 실행 중 오류가 발생했습니다: {state['error']}"}
    
    chain = response_generation_prompt | llm
    
    result = chain.invoke({
        "question": state["question"],
        "query": state["cypher_query"],
        "result": str(state["query_result"][:5]) + ("..." if len(state["query_result"]) > 5 else "")
    })
    
    return {"response": result.content.strip()}