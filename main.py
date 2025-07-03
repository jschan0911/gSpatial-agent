import os
from dotenv import load_dotenv
from agent.flow import run_agent

def main():
    # Load environment variables
    load_dotenv()
    
    print("Neo4j Cypher Agent (LangGraph Version)")
    print("Type 'exit' to quit\n")
    
    while True:
        try:
            # Get user input
            question = input("질문을 입력하세요: ")
            
            if question.lower() in ['exit', 'quit']:
                print("프로그램을 종료합니다.")
                break
                
            if not question.strip():
                continue
                
            # Run the agent
            result = run_agent(question)
            
            # Display the results
            print("\n" + "="*50)
            print("최종 응답:")
            print("="*50)
            print(result.get("response", "No response generated."))
            
            if result.get("error"):
                print(f"\n오류 발생: {result['error']}")
            
            if result.get("query_result") is not None:
                print("\n" + "-"*50)
                print("상세 쿼리 결과 (최대 5개 항목):")
                print("-"*50)
                for i, item in enumerate(result["query_result"][:5], 1):
                    print(f"{i}. {item}")
                
                if len(result["query_result"]) > 5:
                    print(f"\n...총 {len(result['query_result'])}개 중 5개 항목만 표시됨")
            
            print("\n" + "="*50 + "\n")
            
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"\n오류가 발생했습니다: {str(e)}\n")

if __name__ == "__main__":
    main()