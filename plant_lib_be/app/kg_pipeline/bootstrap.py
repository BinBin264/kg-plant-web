from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

import google.generativeai as genai
from langchain_community.graphs import Neo4jGraph
from langchain_google_genai import ChatGoogleGenerativeAI

from app.kg_pipeline.agents import (
    AnswerSynthesizer,
    CypherGenerator,
    InformationRetriever,
    QueryClarifier,
)
from app.kg_pipeline.config import get_logger, settings, setup_logging
from app.kg_pipeline.database import SessionManager, db_connection, session_manager
from app.kg_pipeline.embeddings import ImageEmbedder, TextEmbedder
from app.kg_pipeline.orchestrator import Pipeline
from app.kg_pipeline.utils import APIKeyManager, Translator

logger = get_logger(__name__)
_bundle_lock = Lock()
_bundle: "PipelineBundle | None" = None


class EmbedderWrapper:
    def __init__(self, text_embedder: TextEmbedder, image_embedder: ImageEmbedder):
        self.text = text_embedder
        self.image = image_embedder

    def embed_text(self, text: str):
        return self.text.embed(text)

    def embed(self, path: str):
        return self.image.embed(path)

    def get_dimensions(self):
        return {"text": self.text.get_dimension(), "image": self.image.get_dimension()}


@dataclass
class PipelineBundle:
    pipeline: Pipeline
    session_manager: SessionManager
    api_key_manager: APIKeyManager


def _build_bundle() -> PipelineBundle:
    setup_logging()
    logger.info("=" * 60)
    logger.info("Initializing KG Plant Disease pipeline")
    logger.info("=" * 60)

    db_connection.create_tables()
    if not db_connection.test_connection():
        raise RuntimeError("KG database connection failed")

    if not settings.gemini.api_keys:
        raise RuntimeError("KG Gemini API keys are not configured")

    api_manager = APIKeyManager(settings.gemini.api_keys)
    genai.configure(api_key=api_manager.get_current_key())

    llm = ChatGoogleGenerativeAI(
        model=settings.gemini.chat_model,
        google_api_key=api_manager.get_current_key(),
        temperature=0.3,
    )
    logger.info(f"LLM initialized: {settings.gemini.chat_model}")

    graph = Neo4jGraph(
        url=settings.neo4j.url,
        username=settings.neo4j.username,
        password=settings.neo4j.password,
    )
    logger.info("Neo4j connected successfully")

    text_embedder = TextEmbedder()
    image_embedder = ImageEmbedder()
    embedder = EmbedderWrapper(text_embedder, image_embedder)
    dims = embedder.get_dimensions()
    logger.info(f"Embedders ready: text={dims['text']}D, image={dims['image']}D")

    translator = Translator(llm)
    agent1_clarifier = QueryClarifier(llm, translator)
    agent2_cypher = CypherGenerator(llm, embedder, graph)
    agent3_retriever = InformationRetriever(graph)
    agent4_synthesizer = AnswerSynthesizer(llm, translator)

    pipeline = Pipeline(
        agent1_clarifier,
        agent2_cypher,
        agent3_retriever,
        agent4_synthesizer,
        session_manager,
        embedder,
    )

    logger.info("KG pipeline initialization complete")
    return PipelineBundle(pipeline=pipeline, session_manager=session_manager, api_key_manager=api_manager)


def get_pipeline_bundle() -> PipelineBundle:
    global _bundle
    if _bundle:
        return _bundle
    with _bundle_lock:
        if _bundle:
            return _bundle
        _bundle = _build_bundle()
        return _bundle
