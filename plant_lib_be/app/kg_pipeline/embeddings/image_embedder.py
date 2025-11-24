import os
from typing import List, Optional

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from app.kg_pipeline.config import get_logger, settings

logger = get_logger(__name__)


class ImageEmbedder:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading image embedding model: {settings.embedding.image_model}")

        self.model = CLIPModel.from_pretrained(settings.embedding.image_model)
        self.processor = CLIPProcessor.from_pretrained(settings.embedding.image_model)
        self.model.to(self.device)

        self.embedding_dim = self.model.config.projection_dim
        logger.info(f"Image embedder initialized (dim: {self.embedding_dim}, device: {self.device})")

    def _validate_image_path(self, image_path: str) -> str:
        if not image_path:
            raise ValueError("Empty image path")
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        file_size = os.path.getsize(image_path)
        if file_size > 10 * 1024 * 1024:
            raise ValueError(f"Image too large: {file_size / 1024 / 1024:.1f}MB (max 10MB)")

        valid_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in valid_extensions:
            raise ValueError(f"Invalid image format: {ext} (supported: {valid_extensions})")
        return image_path

    def embed(self, image_path: str) -> List[float]:
        image_path = self._validate_image_path(image_path)
        image = Image.open(image_path).convert("RGB")

        max_width, max_height = settings.embedding.image_max_size
        if image.size[0] > max_width or image.size[1] > max_height:
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            logger.debug(f"Image resized to {image.size}")

        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {key: tensor.to(self.device) for key, tensor in inputs.items()}

        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

        return image_features.cpu().squeeze().tolist()

    def embed_batch(self, image_paths: List[str]) -> List[Optional[List[float]]]:
        embeddings: List[Optional[List[float]]] = []
        for image_path in image_paths:
            try:
                embedding = self.embed(image_path)
                embeddings.append(embedding)
            except Exception as exc:
                logger.warning(f"Failed to embed image {image_path}: {exc}")
                embeddings.append(None)
        return embeddings

    def get_dimension(self) -> int:
        return self.embedding_dim
