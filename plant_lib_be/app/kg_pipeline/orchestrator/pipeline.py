import os
import time
from typing import Any, Dict, Optional

from app.kg_pipeline.config.logging_config import get_logger

logger = get_logger(__name__)


class Pipeline:
    def __init__(
        self,
        agent1_clarifier,
        agent2_cypher,
        agent3_retriever,
        agent4_synthesizer,
        session_manager,
        embedder,
    ):
        self.agent1 = agent1_clarifier
        self.agent2 = agent2_cypher
        self.agent3 = agent3_retriever
        self.agent4 = agent4_synthesizer
        self.session_manager = session_manager
        self.embedder = embedder
        logger.info("Multi-agent pipeline initialized")

    def process_query(
        self,
        session_token: str,
        query: str,
        image_path: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        start_time = time.time()

        logger.info(f"Processing query: {query[:80]}...")
        if image_path:
            logger.info(f"With image: {os.path.basename(image_path)}")

        result: Dict[str, Any] = {
            "query": query,
            "image_path": image_path,
            "answer": "",
            "success": False,
            "from_cache": False,
            "pipeline": {},
            "metadata": {},
        }

        try:
            session = self.session_manager.get_session(session_token)
            if not session:
                logger.error("Invalid or expired session token")
                result["answer"] = "Invalid or expired session"
                result["success"] = False
                return result

            session_id = session["id"]
            user_id = session["user_id"]

            if use_cache:
                cached_result = self.session_manager.get_cached_query(session_id, query, image_path)
                if cached_result:
                    logger.info("Using cached result")
                    cached_result["from_cache"] = True
                    return cached_result

            logger.info("Agent 1: Clarifying query")
            clarification = self.agent1.clarify(query)
            result["pipeline"]["clarification"] = clarification

            if image_path and os.path.exists(image_path):
                logger.info("Processing image")
                try:
                    image_embedding = self.embedder.embed(image_path)
                    image_results = self.agent3.graph.query(
                        """
                        CALL db.index.vector.queryNodes('image_vector', 5, $image_embedding)
                        YIELD node as img, score
                        MATCH (d:Disease)-[:HAS_IMAGE]->(img)
                        MATCH (c:Crop)<-[:AFFECTED_BY]-(d)
                        RETURN c.name AS crop_name, d.name AS disease_name, score
                        ORDER BY score DESC LIMIT 3
                        """,
                        {"image_embedding": image_embedding},
                    )

                    if image_results:
                        image_context = ", ".join([f"{r['disease_name']} ({r['crop_name']})" for r in image_results])
                        clarification["clarified_query"] += f"\nDựa trên hình ảnh, có thể là: {image_context}"
                        logger.info(f"Found {len(image_results)} image matches")
                except Exception as exc:
                    logger.warning(f"Image processing failed: {exc}")

            logger.info("Agent 2: Generating Cypher")
            cypher_result = self.agent2.generate_cypher(clarification)
            result["pipeline"]["cypher"] = cypher_result

            logger.info("Agent 3: Retrieving information")
            retrieval_result = self.agent3.retrieve(cypher_result)
            result["pipeline"]["retrieval"] = retrieval_result

            logger.info("Agent 4: Synthesizing answer")
            synthesis_result = self.agent4.synthesize(clarification, retrieval_result)
            result["pipeline"]["synthesis"] = synthesis_result

            result["answer"] = synthesis_result["answer"]
            result["success"] = synthesis_result["success"]
            result["metadata"] = synthesis_result["metadata"]

            processing_time = int((time.time() - start_time) * 1000)
            result["metadata"]["processing_time_ms"] = processing_time

            self.session_manager.save_chat_history(
                session_id=session_id,
                user_id=user_id,
                query=query,
                answer=result["answer"],
                query_language=clarification.get("language", "vi"),
                intent=clarification.get("intent", "unknown"),
                answer_language=result["metadata"].get("original_language", "vi"),
                pipeline_data=result["pipeline"],
                image_path=image_path,
                total_results=result["metadata"].get("total_results", 0),
                processing_time=processing_time,
                from_cache=False,
            )

            if use_cache:
                self.session_manager.set_cached_query(
                    session_id=session_id,
                    query=query,
                    result=result,
                    image_path=image_path,
                )

            logger.info(f"Query processing completed in {processing_time}ms")
            return result

        except Exception as exc:
            result["answer"] = f"Xin lỗi, đã xảy ra lỗi: {str(exc)}"
            result["success"] = False
            logger.error(f"Pipeline failed: {exc}", exc_info=True)
            return result
