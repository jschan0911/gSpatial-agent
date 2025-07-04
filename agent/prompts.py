from langchain_core.prompts import PromptTemplate

# gSpatial operation documentation
gspatial_summary = """
Available gSpatial operation types:

1. Topological Operation: Checks spatial relationships between two objects
   - Available operations:
     • CONTAINS: Checks if the first object contains the second object
     • COVERED_BY: Checks if the first object is covered by the second object
     • CROSSES: Checks if two objects cross each other
     • DISJOINT: Checks if two objects are disjoint
     • EQUALS: Checks if two objects are equal
     • INTERSECTS: Checks if two objects intersect
     • OVERLAPS: Checks if two objects overlap
     • TOUCHES: Checks if two objects touch at their boundaries
     • WITHIN: Checks if the first object is within the second object
   - Parameters: operation name(str), n_list(list), m_list(list)
   - Output: n(node), m(node), result(bool)

2. Set Operation: Set operations on two sets of objects
   - Available operations:
     • INTERSECTION: Returns intersection
     • UNION: Returns union
     • DIFFERENCE: Returns difference (first - second)
   - Parameters: operation name(str), n_list(list), m_list(list)
   - Output: n(node), m(node), result(WKT geometry)

3. Numeric Parameter Operation (BUFFER): Creates distance-based buffer
   - Available operation: BUFFER
   - Distance parameter must always be in decimal format (e.g., 5.0). Always include .0 even for integer values.
   - Parameters: 'BUFFER', n_list(list), param(list<double>)
   - Output: n(node), result(WKT geometry)

4. Single Parameter Operation: Calculates properties or transformations of a single object
   - Available operations:
     • AREA: Calculates area
     • BBOX: Calculates minimum bounding box
     • BOUNDARY: Calculates boundary of the object
     • CENTROID: Calculates centroid
     • CONVEX_HULL: Calculates convex hull
     • DIMENSION: Returns dimension information (0:point, 1:line, 2:polygon)
     • ENVELOPE: Calculates bounding rectangle
     • LENGTH: Calculates length (for linestrings)
     • SRID: Returns spatial reference system ID
   - Parameters: operation name(str), n_list(list)
   - Output: n(node), result(geometry or numeric)

5. Measurement Operation (DISTANCE): Measures distance between two objects
   - Available operation:
     • DISTANCE: Calculates the shortest distance between two objects
   - Parameters: 'DISTANCE', n_list(list), m_list(list)
   - Output: n(node), m(node), result(double)
"""

# 1) Type Classification Prompt
classification_prompt = PromptTemplate(
    input_variables=["input", "schema"],
    template="""
Analyze the question below and select the most appropriate gSpatial operation type.
{gspatial_summary}
Schema:
{schema}
Question: {input}
Type (choose one from TOPOLOGICAL, SET, BUFFER, SINGLE, DISTANCE):
""".replace("{gspatial_summary}", gspatial_summary)
)

# 2) Entity Extraction Prompt
entity_extraction_prompt = PromptTemplate(
    input_variables=["input"],
    template="""
Extract all entities related to the spatial query from the following question.

Question: {input}

Entity types to extract:
- Location names (e.g., 'Seoul Station', 'Gangnam District', 'Han River')
- Distances (e.g., '1km', '500m')
- Spatial relationships (e.g., 'inside', 'near', 'closest to')
- Other relevant attributes

Output in JSON format. Each entity should have 'type' and 'value' fields.
"""
)

# 3) Cypher Generation Prompt
cypher_generation_prompt = PromptTemplate(
    input_variables=["query_type", "entities", "schema", "input"],
    template="""
Write a Cypher query that calls the gSpatial operation procedure based on the given information.
- Question: {input}
- Type: {query_type}
- Entities: {entities}
- Schema: {schema}

Refer to the following example structures for each type:

1) Topological Operation
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
* Distance must always be in decimal format (e.g., 5.0). Always include .0 even for integer values.

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

Output only the Cypher query, following the example patterns.
"""
)

# 4) Response Generation Prompt
response_generation_prompt = PromptTemplate(
    input_variables=["question", "query", "result"],
    template="""
You are given a user's question, the executed query, and its results. Generate a clear and helpful response in English.

Question: {question}
Executed Query: {query}
Query Results: {result}

Your response should:
1. Provide a direct answer to the question
2. Highlight key information from the query results
3. Include additional context or explanations if needed
4. Be concise and professional
5. Format numbers and data appropriately

Response:
"""
)

__all__ = [
    'gspatial_summary',
    'classification_prompt',
    'entity_extraction_prompt',
    'cypher_generation_prompt',
    'response_generation_prompt'
]
