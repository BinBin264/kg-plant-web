import json
from typing import Any, Dict

from langchain_core.prompts.prompt import PromptTemplate

from app.kg_pipeline.config.logging_config import get_logger
from app.kg_pipeline.utils.retry import retry_with_backoff

logger = get_logger(__name__)


class AnswerSynthesizer:
    def __init__(self, llm, translator):
        self.llm = llm
        self.translator = translator
        self.synthesis_prompt = PromptTemplate(
            input_variables=["query", "intent", "results", "total_count"],
            template="""Generate a comprehensive Vietnamese answer based on database results.

            User Question: {query}
            Intent: {intent}
            Total Results: {total_count}
            
            Database Results:
            {results}
            
            ### Answer Guidelines:
            
            1. **Structure by intent:**
               - symptom_diagnosis: List diseases with similarity scores
               - disease_info: Detailed disease information
               - crop_care: Care instructions step by step
               - treatment: Organic → Chemical options
               - prevention: Preventive measures list
            
            2. **Format rules:**
               - Always mention crop names with diseases
               - Include similarity scores if available
               - Use bullet points for lists
               - Limit to top 5-10 results
               - If total > displayed, mention "và X kết quả khác"
            
            3. **If no results:**
               - Apologize politely
               - Suggest alternative search terms
               - Mention similar topics in database
            
            Generate answer in Vietnamese:""",
        )
        logger.info("Answer synthesizer initialized")

    @retry_with_backoff(max_retries=3)
    def synthesize(self, clarification: Dict, retrieval_result: Dict) -> Dict[str, Any]:
        results_str = json.dumps(retrieval_result["results"][:10], ensure_ascii=False, indent=2)

        try:
            prompt = self.synthesis_prompt.format(
                query=clarification["clarified_query"],
                intent=clarification["intent"],
                results=results_str,
                total_count=retrieval_result["total_count"],
            )
            response = self.llm.invoke(prompt)
            answer_vi = response.content.strip()
            logger.debug("Answer synthesized successfully in Vietnamese")
        except Exception as exc:
            logger.error(f"Answer synthesis failed: {exc}")
            if retrieval_result["results"]:
                answer_vi = f"Tìm thấy {len(retrieval_result['results'])} kết quả:\n"
                for idx, result in enumerate(retrieval_result["results"][:5], 1):
                    answer_vi += f"\n{idx}. {json.dumps(result, ensure_ascii=False)}"
            else:
                answer_vi = "Xin lỗi, không tìm thấy kết quả phù hợp."

        original_lang = clarification["language"]
        if original_lang != self.translator.data_language:
            try:
                answer = self.translator.translate_response(answer_vi, original_lang)
                logger.debug(f"Answer translated to {original_lang}")
            except Exception as exc:
                logger.warning(f"Translation failed: {exc}, using Vietnamese answer")
                answer = answer_vi
        else:
            answer = answer_vi

        return {
            "answer": answer,
            "answer_vi": answer_vi,
            "success": True,
            "metadata": {
                "total_results": retrieval_result["total_count"],
                "displayed_results": len(retrieval_result["results"][:10]),
                "original_language": original_lang,
            },
        }
