import streamlit as st
from agent.flow import create_workflow
import os
from dotenv import load_dotenv
import traceback

# 환경 변수 로드
load_dotenv()

st.title("GSpatial LangGraph Agent")

# 사용자 입력
user_input = st.text_input("공간 쿼리를 입력하세요:", "")

if user_input:
    try:
        st.write("워크플로우 생성 중...")
        workflow = create_workflow()
        st.write("워크플로우 생성 완료")
        
        inputs = {"question": user_input}
        st.write("워크플로우 실행 중...")
        
        for output in workflow.stream(inputs):
            st.write("워크플로우 스트리밍 중...")
            st.json(output)  # 중간 출력 확인
            
            for key, value in output.items():
                if key == "response":
                    st.write("### 응답")
                    st.write(value)
                elif key == "results":
                    st.write("### 쿼리 결과")
                    st.json(value)
                elif key == "cypher_query":
                    with st.expander("생성된 Cypher 쿼리 보기"):
                        st.code(value, language="cypher")
    
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
        st.text(traceback.format_exc())  # 상세 에러 출력