import streamlit as st
from agent.flow import create_workflow
import os
import json
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(layout="wide")
st.title("gSpatial LangGraph Agent")

# Container for status messages
status_container = st.container()

# Top fixed area (Question input)
with st.container():
    cols = st.columns([5, 1])
    with cols[0]:
        st.subheader("Enter Your Question")
    with cols[1]:
        st.write("")
        run_btn = st.button("Run", type="primary", use_container_width=True)
    
    # Example queries covering different spatial operations
    example_queries = [
        # Distance queries
        "What is the distance between Greenwich Village Elem School and Loisaida?",
        "What is the distance between Mount Sinai School of Medicine and Nyct 207th St Subway Shops and Yard?",
        
        # Buffer queries
        "Create a 20.0 meter buffer around General Theological Smry.",
        "Create a 15.0 meter buffer around Museo del Barrio.",
        
        # Topological operation queries
        "Does Grand Central Trmnl lie within Museo del Barrio?",
        "Does Hunter Colg lie within Riverside Park?",
        
        # Set operation queries
        "What is the intersection of United Nations Headquarters and Madison Square Gardens & Penn Sta?",
        "What is the union of Rockefeller Univ and Saint Vincent Hosp?",
        
        # Single operation queries
        "What is the area of Matthews-Palmer Playground?",
        "What is the area of Morningside Park?"
    ]
    
    # Display example queries as clickable buttons
    st.write("Try these examples:")
    cols = st.columns(2)  # Create 2 columns for better layout
    for i, query in enumerate(example_queries):
        if cols[i % 2].button(query, use_container_width=True, key=f"example_{i}"):
            st.session_state.user_input = query
    
    # Initialize session state for user input if it doesn't exist
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
    
    # Text area for user input
    user_input = st.text_area(
        "Enter your spatial query:", 
        value=st.session_state.user_input,
        height=100, 
        label_visibility="collapsed",
        placeholder="Example: Find parks in Gangnam District, Seoul"
    )
    
    # Update session state when user types in the text area
    if user_input != st.session_state.user_input:
        st.session_state.user_input = user_input

# Results area (bottom)
if run_btn:
    if not user_input.strip():
        st.warning("Please enter your question.")
    else:
        try:
            # Clear previous results
            for key in st.session_state.keys():
                if key.startswith('expand_'):
                    del st.session_state[key]
            
            # Initialize workflow
            with status_container:
                st.subheader("Execution Results")
                with st.status("Running workflow...", expanded=True) as status:
                    status.write("Initializing workflow...")
                    workflow = create_workflow()
                    
                    # Initialize state
                    state = {
                        "question": user_input,
                        "query_type": None,
                        "entities": None,
                        "cypher_query": None,
                        "query_result": None,
                        "response": None,
                        "error": None
                    }
                    
                    # Run workflow steps
                    steps = [
                        ("classify_query", "1. Analyzing question type..."),
                        ("extract_entities", "2. Extracting entities..."),
                        ("generate_cypher", "3. Generating Cypher query..."),
                        ("execute_cypher", "4. Executing query..."),
                        ("generate_response", "5. Generating response...")
                    ]
                    
                    for step, message in steps:
                        status.write(f"### {message}")
                        
                        # Execute the step
                        if step == "classify_query":
                            from agent.nodes import classify_query
                            result = classify_query(state)
                            state.update(result)
                            
                            with st.expander("🔍 Question Type Analysis", expanded=True):
                                st.json({"query_type": state["query_type"]})
                        
                        elif step == "extract_entities":
                            from agent.nodes import extract_entities
                            result = extract_entities(state)
                            state.update(result)
                            
                            with st.expander("🔍 Extracted Entities", expanded=True):
                                st.json({"entities": state["entities"]})
                        
                        elif step == "generate_cypher":
                            from agent.nodes import generate_cypher
                            result = generate_cypher(state)
                            state.update(result)
                            
                            with st.expander("🔍 Generated Cypher Query", expanded=True):
                                st.code(state["cypher_query"], language="cypher")
                        
                        elif step == "execute_cypher":
                            from agent.nodes import execute_cypher
                            result = execute_cypher(state)
                            state.update(result)
                            
                            with st.expander("🔍 Query Execution Results", expanded=True):
                                if state.get("error"):
                                    st.error(f"❌ Query execution error: {state['error']}")
                                else:
                                    st.json(state["query_result"])
                        
                        elif step == "generate_response":
                            from agent.nodes import generate_response
                            result = generate_response(state)
                            state.update(result)
                            
                            with st.expander("🔍 Question Type Analysis", expanded=True):
                                st.json({"query_type": state["query_type"]})
                        
                        elif step == "extract_entities":
                            from agent.nodes import extract_entities
                            result = extract_entities(state)
                            state.update(result)
                            
                            with st.expander("🔍 Extracted Entities", expanded=True):
                                st.json({"entities": state["entities"]})
                        
                        elif step == "generate_cypher":
                            from agent.nodes import generate_cypher
                            result = generate_cypher(state)
                            state.update(result)
                            
                            with st.expander("🔍 Generated Cypher Query", expanded=True):
                                st.code(state["cypher_query"], language="cypher")
                        
                        elif step == "execute_cypher":
                            from agent.nodes import execute_cypher
                            result = execute_cypher(state)
                            state.update(result)
                            
                            with st.expander("🔍 Query Execution Results", expanded=True):
                                if state.get("error"):
                                    st.error(f"❌ Query execution error: {state['error']}")
                                else:
                                    st.json(state["query_result"])
                        
                        elif step == "generate_response":
                            from agent.nodes import generate_response
                            result = generate_response(state)
                            state.update(result)
                    
                    # Display final results
                    status.write("### ✅ Processing complete!")
                    
                    # Show final response in a nice card
                    st.divider()
                    st.subheader("💬 Final Response")
                    st.info(state.get("response", "Unable to generate a response."), icon="💡")
                    
                    # Show debug info in an expander
                    with st.expander("🔧 Final State (Debug)", expanded=False):
                        st.write("#### State Summary")
                        st.json({k: v for k, v in state.items() if k != "query_result"})
                        
                        if state.get("query_result"):
                            st.write("#### Query Result Sample (First Item)")
                            sample = (state["query_result"][:1] 
                                     if isinstance(state["query_result"], list) and len(state["query_result"]) > 0 
                                     else state["query_result"])
                            st.json(sample)
        
        except Exception as e:
            with status_container:
                st.error(f"❌ An error occurred: {str(e)}")
                with st.expander("Detailed error information", expanded=False):
                    st.text(traceback.format_exc())