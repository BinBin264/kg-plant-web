from typing import List

import torch
from sentence_transformers import SentenceTransformer

from app.kg_pipeline.config import get_logger, settings

logger = get_logger(__name__)


class TextEmbedder:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading text embedding model: {settings.embedding.text_model}")

        self.model = SentenceTransformer(settings.embedding.text_model)
        self.model.to(self.device)

        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Text embedder initialized (dim: {self.embedding_dim}, device: {self.device})")

    def _validate_text(self, text: str) -> str:
        if not text:
            raise ValueError("Empty text provided")

        text = str(text).strip()
        if not text:
            raise ValueError("Text is empty after stripping")

        if len(text) > settings.embedding.text_max_length:
            logger.warning(f"Text truncated from {len(text)} to {settings.embedding.text_max_length} chars")
            text = text[: settings.embedding.text_max_length]

        text = text.encode("utf-8", errors="ignore").decode("utf-8")
        text = text.replace("\x00", "")
        return text

    def embed(self, text: str) -> List[float]:
        text = self._validate_text(text)
        with torch.no_grad():
            embedding = self.model.encode(
                text,
                convert_to_tensor=True,
                device=self.device,
                show_progress_bar=False,
            )
            return embedding.cpu().tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        validated_texts: List[str] = []
        for text in texts:
            try:
                validated_texts.append(self._validate_text(text))
            except ValueError as exc:
                logger.warning(f"Skipping invalid text: {exc}")
                validated_texts.append("")

        with torch.no_grad():
            embeddings = self.model.encode(
                validated_texts,
                convert_to_tensor=True,
                device=self.device,
                show_progress_bar=False,
                batch_size=settings.embedding.text_batch_size,
            )
            return embeddings.cpu().tolist()

    def get_dimension(self) -> int:
        return self.embedding_dim
