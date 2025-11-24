from typing import Any, Dict

from app.kg_pipeline.config.logging_config import get_logger

logger = get_logger(__name__)


class InformationRetriever:
    def __init__(self, graph):
        self.graph = graph
        logger.info("Information retriever initialized")

    def retrieve(self, cypher_result: Dict) -> Dict[str, Any]:
        retrieval_result: Dict[str, Any] = {
            "total_count": 0,
            "results": [],
            "success": False,
            "error": None,
            "cypher_used": {
                "count_query": cypher_result.get("count_query", ""),
                "result_query": cypher_result.get("result_query", ""),
            },
        }

        try:
            params = cypher_result.get("embeddings", {})

            count_query = cypher_result.get("count_query", "")
            if count_query:
                try:
                    count_result = self.graph.query(count_query, params)
                    if count_result and len(count_result) > 0:
                        retrieval_result["total_count"] = count_result[0].get("total_count", 0)
                    logger.debug(f"Count query result: {retrieval_result['total_count']}")
                except Exception as exc:
                    logger.warning(f"COUNT query failed: {exc}")
                    retrieval_result["total_count"] = -1

            result_query = cypher_result.get("result_query", "")
            if result_query:
                try:
                    results = self.graph.query(result_query, params)
                    retrieval_result["results"] = results
                    retrieval_result["success"] = True
                    logger.info(f"Successfully retrieved {len(results)} results")
                except Exception as exc:
                    retrieval_result["error"] = str(exc)
                    retrieval_result["success"] = False
                    logger.error(f"RESULT query failed: {exc}")
            else:
                retrieval_result["error"] = "No result query provided"
                retrieval_result["success"] = False

            return retrieval_result

        except Exception as exc:
            retrieval_result["error"] = str(exc)
            retrieval_result["success"] = False
            logger.error(f"Retrieval failed: {exc}")
            return retrieval_result
