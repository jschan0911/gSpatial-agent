from langchain_core.prompts import PromptTemplate

# gSpatial operation 설명
gspatial_summary = """
사용 가능한 gSpatial operation 유형:

1. Topological Operation: 두 객체 간의 공간적 관계를 검사
   - 사용 가능한 operation 이름:
     • CONTAINS: 첫 번째 객체가 두 번째 객체를 포함하는지 검사
     • COVERED_BY: 첫 번째 객체가 두 번째 객체에 의해 커버되는지 검사
     • CROSSES: 두 객체가 교차하는지 검사
     • DISJOINT: 두 객체가 서로 떨어져 있는지 검사
     • EQUALS: 두 객체가 동일한지 검사
     • INTERSECTS: 두 객체가 하나라도 교차하는지 검사
     • OVERLAPS: 두 객체가 부분적으로 겹치는지 검사
     • TOUCHES: 두 객체가 경계에서 만나는지 검사
     • WITHIN: 첫 번째 객체가 두 번째 객체 내부에 있는지 검사
   - 인자: operation name(str), n_list(list), m_list(list)
   - 출력: n(node), m(node), result(bool)

2. Set Operation: 두 객체 집합에 대한 집합 연산
   - 사용 가능한 operation 이름:
     • INTERSECTION: 교집합 반환
     • UNION: 합집합 반환
     • DIFFERENCE: 차집합(첫 번째 - 두 번째) 반환
   - 인자: operation name(str), n_list(list), m_list(list)
   - 출력: n(node), m(node), result(WKT geometry)

3. Numeric Parameter Operation (BUFFER): 거리 기반 버퍼 생성
   - 사용 가능한 operation 이름: BUFFER
   - distance 파라미터는 항상 소수점 형식(예: 5.0)으로 표현해야 함. 정수 입력 시에도 반드시 .0을 붙이세요.
   - 인자: 'BUFFER', n_list(list), param(list<double>)
   - 출력: n(node), result(WKT geometry)

4. Single Parameter Operation: 단일 객체 속성 또는 변환 계산
   - 사용 가능한 operation 이름:
     • AREA: 면적 계산
     • BBOX: 최소 경계 사각형 계산
     • BOUNDARY: 객체의 경계선 계산
     • CENTROID: 중심점 계산
     • CONVEX_HULL: 볼록 껍질 계산
     • DIMENSION: 차원 정보(0:점,1:선,2:면)
     • ENVELOPE: 객체의 외접 사각형 계산
     • LENGTH: 길이(선스트링) 계산
     • SRID: 공간 참조 시스템 ID 반환
   - 인자: operation name(str), n_list(list)
   - 출력: n(node), result(geometry or numeric)

5. Measurement Operation (DISTANCE): 두 객체 간 거리를 측정
   - 사용 가능한 operation 이름:
     • DISTANCE: 두 객체 간 최단 거리 계산
   - 인자: 'DISTANCE', n_list(list), m_list(list)
   - 출력: n(node), m(node), result(double)
"""

# 1) 유형 분류 프롬프트
classification_prompt = PromptTemplate(
    input_variables=["input", "schema"],
    template="""
아래 질문을 분석하여, 가장 적합한 gSpatial operation 유형을 선택하세요.
{gspatial_summary}
스키마:
{schema}
질문: {input}
유형 (TOPOLOGICAL, SET, BUFFER, SINGLE, DISTANCE 중 하나로):
""".replace("{gspatial_summary}", gspatial_summary)
)

# 2) 엔티티 추출 프롬프트
entity_extraction_prompt = PromptTemplate(
    input_variables=["input"],
    template="""
아래 질문에서 공간 쿼리와 관련된 모든 엔티티(위치명, 거리, 관계 등)를 추출하세요.

질문: {input}

추출할 엔티티 유형:
- 위치명 (예: '서울역', '강남구', '한강')
- 거리 (예: '1km', '500m')
- 공간 관계 (예: '안에', '근처에', '에서 가장 가까운')
- 기타 관련 속성

JSON 형식으로 출력하세요. 각 엔티티는 'type'과 'value' 필드를 가져야 합니다.
"""
)

# 3) Cypher 생성 프롬프트
cypher_generation_prompt = PromptTemplate(
    input_variables=["query_type", "entities", "schema", "input"],
    template="""
주어진 정보를 바탕으로 gSpatial operation 프로시저를 호출하는 Cypher 쿼리를 작성하세요.
- 질문: {input}
- 유형: {query_type}
- 엔티티: {entities}
- 스키마: {schema}

각 유형별 구조 예시를 참고하세요:

1) Topological
MATCH (n)
WITH collect(n) AS n_list
MATCH (m)
WITH n_list, collect(m) AS m_list
CALL gspatial.operation('WITHIN', [n_list, m_list]) YIELD n, m, result
WHERE result = true
RETURN n, m

2) Set
MATCH (n)
WITH collect(n) AS n_list
MATCH (m)
WITH n_list, collect(m) AS m_list
CALL gspatial.operation('UNION', [n_list, m_list]) YIELD result
RETURN result

3) Buffer
MATCH (n)
WITH collect(n) AS n_list
CALL gspatial.operation('BUFFER', [n_list, [distance]]) YIELD n, result
RETURN result
* distance는 항상 소수점 형식(예: 5.0)으로 표현해야 함. 정수 입력 시에도 반드시 .0을 붙이세요.

4) Single
MATCH (n)
WITH collect(n) AS n_list
CALL gspatial.operation('AREA', [n_list]) YIELD n, result
RETURN result

5) Distance
MATCH (n)
WITH collect(n) AS n_list
MATCH (m)
WITH n_list, collect(m) AS m_list
CALL gspatial.operation('DISTANCE', [n_list, m_list]) YIELD n, m, result
RETURN n, m, result

위 예시 패턴을 따라, Cypher 쿼리만 출력하세요.
"""
)

# 4) 응답 생성 프롬프트
response_generation_prompt = PromptTemplate(
    input_variables=["question", "query", "result"],
    template="""
사용자의 질문과 실행된 쿼리, 그리고 그 결과가 주어집니다. 이를 바탕으로 사용자에게 친절하게 답변을 생성하세요.

질문: {question}
실행된 쿼리: {query}
쿼리 결과: {result}

답변은 한국어로 작성하고, 다음 사항을 포함하세요:
1. 질문에 대한 직접적인 답변
2. 쿼리 결과에서 도출된 주요 정보
3. 필요한 경우 추가 설명이나 맥락

답변:
"""
)

__all__ = [
    'gspatial_summary',
    'classification_prompt',
    'entity_extraction_prompt',
    'cypher_generation_prompt',
    'response_generation_prompt'
]
