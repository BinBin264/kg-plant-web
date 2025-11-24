import json
from typing import Any, Dict

from langchain_core.prompts.prompt import PromptTemplate

from app.kg_pipeline.config.logging_config import get_logger
from app.kg_pipeline.utils.retry import retry_with_backoff

logger = get_logger(__name__)


class CypherGenerator:
    def __init__(self, llm, embedder, graph):
        self.llm = llm
        self.embedder = embedder
        self.graph = graph
        self.schema = graph.get_schema

        dims = embedder.get_dimensions()
        self.text_dim = dims["text"]
        self.image_dim = dims["image"]

        self.vector_indexes = {
            "disease_name": ("disease_name_vector", "Disease", "name_embedding"),
            "symptom": ("symptom_vector", "Symptom", "embedding"),
            "crop_name": ("crop_name_vector", "Crop", "name_embedding"),
            "image": ("image_vector", "Image", "embedding"),
            "summary": ("summary_vector", "Summary", "embedding"),
            "cause": ("cause_vector", "Cause", "embedding"),
            "organic_control": ("organic_control_vector", "OrganicControl", "embedding"),
            "chemical_control": ("chemical_control_vector", "ChemicalControl", "embedding"),
            "preventive_measure": ("preventive_measure_vector", "PreventiveMeasure", "embedding"),
            "introduction": ("introduction_vector", "Introduction", "embedding"),
            "care": ("care_vector", "Care", "embedding"),
            "soil": ("soil_vector", "Soil", "embedding"),
            "climate": ("climate_vector", "Climate", "embedding"),
        }

        self.cypher_prompt = PromptTemplate(
            input_variables=["schema", "clarified_query", "intent", "entities", "search_strategy", "vector_indexes"],
            template="""You are a Neo4j Cypher expert for plant disease database.

            ### Database Schema:
            {schema}
            
            ### Available Vector Indexes (for semantic search):
            {vector_indexes}
            
            ### Query Context:
            - Intent: {intent}
            - Entities: {entities}
            - Search Strategy: {search_strategy}
            - Clarified Query: {clarified_query}
            
            ### Cypher Generation Rules:
            
            **1. When to use Vector Search:**
            - For symptoms, descriptions, vague queries → Use vector search
            - Use format: `CALL db.index.vector.queryNodes('<index_name>', <top_k>, $embedding_<node_type>)`
            - MUST use parameter name: `$embedding_<node_type>` (e.g., $embedding_symptom, $embedding_crop_name)
            
            **2. When to use Pattern Matching:**
            - For exact names (crops, diseases) → Use `WHERE n.name CONTAINS '<name>'`
            - For IDs → Use `WHERE n.id = '<id>'`
            
            **3. Hybrid Strategy:**
            - Combine both: Vector search for symptoms + Pattern for crop names
            - Use UNION or OPTIONAL MATCH
            
            **4. Query Structure:**
            Always generate TWO queries:
            
            a) COUNT Query (estimate total results):
            ```cypher
            // Count query
            MATCH (n:NodeLabel)
            WHERE <conditions>
            RETURN COUNT(DISTINCT n) AS total_count
            ```
            
            b) RESULT Query (get actual data):
            ```cypher
            // Result query
            MATCH (n:NodeLabel)
            WHERE <conditions>
            WITH n
            OPTIONAL MATCH <relationships>
            RETURN <fields>
            LIMIT <number>
            ```
            
            **5. CRITICAL: Embedding Parameters**
            - If using vector search, you MUST list required embeddings
            - Format: `"embedding_<node_type>": "<description>"`
            
            ### Output JSON Format:
            {{
                "count_query": "<cypher for counting>",
                "result_query": "<cypher for results>",
                "requires_embeddings": true/false,
                "embedding_params": {{
                    "embedding_symptom": "Query about symptoms",
                    "embedding_crop_name": "Crop name to search"
                }},
                "explanation": "<brief explanation of query strategy>"
            }}
            
            ### Examples:
            
            **Example 1: Symptom diagnosis (vector search)**
            Input: "Tìm bệnh trên cây lúa có triệu chứng lá vàng"
            Output:
            {{
                "count_query": "CALL db.index.vector.queryNodes('symptom_vector', 10, $embedding_symptom) YIELD node AS s, score WHERE score > 0.7 MATCH (d:Disease)-[:HAS_SYMPTOM]->(s) MATCH (c:Crop)<-[:AFFECTED_BY]-(d) WHERE c.name CONTAINS 'Lúa' RETURN COUNT(DISTINCT d) AS total_count",
                "result_query": "CALL db.index.vector.queryNodes('symptom_vector', 5, $embedding_symptom) YIELD node AS s, score WHERE score > 0.7 MATCH (d:Disease)-[:HAS_SYMPTOM]->(s) MATCH (c:Crop)<-[:AFFECTED_BY]-(d) WHERE c.name CONTAINS 'Lúa' OPTIONAL MATCH (d)-[:HAS_ORGANIC_CONTROL]->(oc:OrganicControl) OPTIONAL MATCH (d)-[:HAS_CHEMICAL_CONTROL]->(cc:ChemicalControl) RETURN DISTINCT c.name AS crop_name, d.name AS disease_name, s.text AS symptom, score AS similarity, oc.text AS organic_treatment, cc.text AS chemical_treatment ORDER BY score DESC LIMIT 5",
                "requires_embeddings": true,
                "embedding_params": {{
                    "embedding_symptom": "lá vàng"
                }},
                "explanation": "Use vector search on symptoms with crop name pattern matching"
            }}
            
            **Example 2: Disease info (pattern matching)**
            Input: "Thông tin về bệnh đạo ôn"
            Output:
            {{
                "count_query": "MATCH (d:Disease) WHERE d.name CONTAINS 'đạo ôn' RETURN COUNT(d) AS total_count",
                "result_query": "MATCH (d:Disease) WHERE d.name CONTAINS 'đạo ôn' MATCH (c:Crop)<-[:AFFECTED_BY]-(d) OPTIONAL MATCH (d)-[:HAS_SYMPTOM]->(s:Symptom) OPTIONAL MATCH (d)-[:HAS_ORGANIC_CONTROL]->(oc:OrganicControl) RETURN d.name AS disease_name, d.scientific_name AS scientific_name, collect(DISTINCT c.name) AS affected_crops, collect(DISTINCT s.text)[0..3] AS symptoms, oc.text AS organic_treatment LIMIT 3",
                "requires_embeddings": false,
                "embedding_params": {{}},
                "explanation": "Pattern match disease name, no embeddings needed"
            }}
            
            Now generate Cypher for the given query. Respond ONLY with valid JSON:""",
        )
        logger.info(
            f"Cypher generator initialized (text_dim={self.text_dim}, image_dim={self.image_dim}, indexes={len(self.vector_indexes)})"
        )

    @retry_with_backoff(max_retries=3)
    def generate_cypher(self, clarification: Dict) -> Dict[str, Any]:
        vector_indexes_str = "\n".join(
            [f"- {key}: index='{idx}', label='{label}', property='{prop}'" for key, (idx, label, prop) in self.vector_indexes.items()]
        )

        prompt = self.cypher_prompt.format(
            schema=self.schema,
            clarified_query=clarification["clarified_query"],
            intent=clarification["intent"],
            entities=json.dumps(clarification["entities"], ensure_ascii=False),
            search_strategy=clarification["search_strategy"],
            vector_indexes=vector_indexes_str,
        )

        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()

            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            cypher_result = json.loads(response_text)

            if cypher_result.get("requires_embeddings", False):
                embeddings: Dict[str, Any] = {}
                for param_name, param_text in cypher_result.get("embedding_params", {}).items():
                    try:
                        embedding_vector = self.embedder.embed_text(param_text)
                        embeddings[param_name] = embedding_vector
                    except Exception as exc:
                        logger.error(f"Failed to generate embedding for {param_name}: {exc}")
                        embeddings[param_name] = [0.0] * self.text_dim

                cypher_result["embeddings"] = embeddings
            else:
                cypher_result["embeddings"] = {}

            logger.info(f"Cypher generated successfully: requires_embeddings={cypher_result.get('requires_embeddings')}")
            return cypher_result

        except json.JSONDecodeError as exc:
            logger.warning(f"Failed to parse Cypher JSON: {exc}")
            entities = clarification["entities"]
            crop_names = entities.get("crops", [])
            crop_filter = f"WHERE c.name CONTAINS '{crop_names[0]}'" if crop_names else ""
            return {
                "count_query": f"MATCH (c:Crop) {crop_filter} RETURN COUNT(c) AS total_count",
                "result_query": f"MATCH (c:Crop) {crop_filter} RETURN c.name AS crop_name LIMIT 5",
                "requires_embeddings": False,
                "embedding_params": {},
                "embeddings": {},
                "explanation": "Fallback: simple pattern matching",
            }
