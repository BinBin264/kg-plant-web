import json
from typing import Any, Dict

from langchain_core.prompts.prompt import PromptTemplate

from app.kg_pipeline.config.logging_config import get_logger
from app.kg_pipeline.utils.retry import retry_with_backoff

logger = get_logger(__name__)


class QueryClarifier:
    def __init__(self, llm, translator):
        self.llm = llm
        self.translator = translator
        self.prompt = PromptTemplate(
            input_variables=["query", "language"],
            template="""You are a query clarifier for plant disease database.

            User Query: {query}
            Language: {language}
            
            Your task: Clarify the query by:
            1. Identify intent (disease_info, symptom_diagnosis, crop_care, treatment, prevention)
            2. Extract entities (crop names, disease names, symptoms). When extracting crop names, remove prefixes like 'Cây ' and capitalize the first letter, e.g., 'Cây lúa' => 'Lúa', 'Cây cà chua' => 'Cà chua'.
            3. Rephrase clearly (keep concise, max 2 sentences)
            
            Output JSON format:
            {{
                "intent": "<intent_type>",
                "entities": {{
                    "crops": ["crop1", "crop2"],
                    "diseases": ["disease1"],
                    "symptoms": ["symptom1", "symptom2"]
                }},
                "clarified_query": "<clear, concise query>",
                "search_strategy": "<vector|pattern|hybrid>"
            }}
            
            Example:
            Input: "Cây lúa bị lá vàng"
            Output:
            {{
                "intent": "symptom_diagnosis",
                "entities": {{
                    "crops": ["Lúa"],
                    "symptoms": ["lá vàng"]
                }},
                "clarified_query": "Tìm bệnh trên cây lúa có triệu chứng lá vàng",
                "search_strategy": "hybrid"
            }}
            
            Respond ONLY with valid JSON:""",
        )
        logger.info("Query clarifier initialized")

    @retry_with_backoff(max_retries=3)
    def clarify(self, query: str) -> Dict[str, Any]:
        translated_query, detected_lang = self.translator.process_query(query)
        prompt_text = self.prompt.format(query=translated_query, language=detected_lang)

        try:
            response = self.llm.invoke(prompt_text)
            response_text = response.content.strip()

            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            clarification = json.loads(response_text)
            clarification["original_query"] = query
            clarification["translated_query"] = translated_query
            clarification["language"] = detected_lang

            logger.info(
                f"Query clarified: intent={clarification['intent']}, strategy={clarification['search_strategy']}"
            )
            return clarification

        except json.JSONDecodeError as exc:
            logger.warning(f"Failed to parse clarification JSON: {exc}")
            return {
                "intent": "general",
                "entities": {"crops": [], "diseases": [], "symptoms": []},
                "clarified_query": translated_query,
                "search_strategy": "hybrid",
                "original_query": query,
                "translated_query": translated_query,
                "language": detected_lang,
            }
