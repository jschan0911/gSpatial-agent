import streamlit as st
from agent.flow import create_workflow
import os
import json
from dotenv import load_dotenv
import traceback

# 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(layout="wide")
st.title("gSpatial LangGraph Agent")

# 상태 메시지를 위한 컨테이너
status_container = st.container()

# 상단 고정 영역 (질문 입력)
with st.container():
    cols = st.columns([5, 1])
    with cols[0]:
        st.subheader("질문 입력")
    with cols[1]:
        st.write("")
        run_btn = st.button("실행", type="primary", use_container_width=True)
    
    user_input = st.text_area(
        "공간 쿼리를 입력하세요:", 
        "", 
        height=100, 
        label_visibility="collapsed",
        placeholder="예: 서울시 강남구의 공원을 찾아줘"
    )

# 결과 영역 (하단)
if run_btn:
    if not user_input.strip():
        st.warning("질문을 입력해주세요.")
    else:
        try:
            # Clear previous results
            for key in st.session_state.keys():
                if key.startswith('expand_'):
                    del st.session_state[key]
            
            # Initialize workflow
            with status_container:
                st.subheader("실행 결과")
                with st.status("워크플로우 실행 중...", expanded=True) as status:
                    status.write("워크플로우를 초기화하는 중...")
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
                        ("classify_query", "1. 질문 유형 분석 중..."),
                        ("extract_entities", "2. 엔티티 추출 중..."),
                        ("generate_cypher", "3. Cypher 쿼리 생성 중..."),
                        ("execute_cypher", "4. 쿼리 실행 중..."),
                        ("generate_response", "5. 응답 생성 중...")
                    ]
                    
                    for step, message in steps:
                        status.write(f"### {message}")
                        
                        # Execute the step
                        if step == "classify_query":
                            from agent.nodes import classify_query
                            result = classify_query(state)
                            state.update(result)
                            
                            with st.expander("🔍 질문 유형 분석 결과", expanded=True):
                                st.json({"query_type": state["query_type"]})
                        
                        elif step == "extract_entities":
                            from agent.nodes import extract_entities
                            result = extract_entities(state)
                            state.update(result)
                            
                            with st.expander("🔍 추출된 엔티티", expanded=True):
                                st.json({"entities": state["entities"]})
                        
                        elif step == "generate_cypher":
                            from agent.nodes import generate_cypher
                            result = generate_cypher(state)
                            state.update(result)
                            
                            with st.expander("🔍 생성된 Cypher 쿼리", expanded=True):
                                st.code(state["cypher_query"], language="cypher")
                        
                        elif step == "execute_cypher":
                            from agent.nodes import execute_cypher
                            result = execute_cypher(state)
                            state.update(result)
                            
                            with st.expander("🔍 쿼리 실행 결과", expanded=True):
                                if state.get("error"):
                                    st.error(f"❌ 쿼리 실행 오류: {state['error']}")
                                else:
                                    st.json(state["query_result"])
                        
                        elif step == "generate_response":
                            from agent.nodes import generate_response
                            result = generate_response(state)
                            state.update(result)
                            
                            with st.expander("🔍 질문 유형 분석 결과", expanded=True):
                                st.json({"query_type": state["query_type"]})
                        
                        elif step == "extract_entities":
                            from agent.nodes import extract_entities
                            result = extract_entities(state)
                            state.update(result)
                            
                            with st.expander("🔍 추출된 엔티티", expanded=True):
                                st.json({"entities": state["entities"]})
                        
                        elif step == "generate_cypher":
                            from agent.nodes import generate_cypher
                            result = generate_cypher(state)
                            state.update(result)
                            
                            with st.expander("🔍 생성된 Cypher 쿼리", expanded=True):
                                st.code(state["cypher_query"], language="cypher")
                        
                        elif step == "execute_cypher":
                            from agent.nodes import execute_cypher
                            result = execute_cypher(state)
                            state.update(result)
                            
                            with st.expander("🔍 쿼리 실행 결과", expanded=True):
                                if state.get("error"):
                                    st.error(f"❌ 쿼리 실행 오류: {state['error']}")
                                else:
                                    st.json(state["query_result"])
                        
                        elif step == "generate_response":
                            from agent.nodes import generate_response
                            result = generate_response(state)
                            state.update(result)
                    
                    # Display final results
                    status.write("### ✅ 처리 완료!")
                    
                    # Show final response in a nice card
                    st.divider()
                    st.subheader("💬 최종 응답")
                    st.info(state.get("response", "응답을 생성할 수 없습니다."), icon="💡")
                    
                    # Show debug info in an expander
                    with st.expander("🔧 최종 상태 (디버그)", expanded=False):
                        st.write("#### 상태 요약")
                        st.json({k: v for k, v in state.items() if k != "query_result"})
                        
                        if state.get("query_result"):
                            st.write("#### 쿼리 결과 샘플 (첫 번째 항목)")
                            sample = (state["query_result"][:1] 
                                     if isinstance(state["query_result"], list) and len(state["query_result"]) > 0 
                                     else state["query_result"])
                            st.json(sample)
        
        except Exception as e:
            with status_container:
                st.error(f"❌ 오류 발생: {str(e)}")
                with st.expander("자세한 오류 정보", expanded=False):
                    st.text(traceback.format_exc())