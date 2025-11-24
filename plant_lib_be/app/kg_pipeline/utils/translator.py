from typing import Tuple

from langdetect import DetectorFactory, detect

from app.kg_pipeline.config import get_logger, settings
from app.kg_pipeline.utils.retry import retry_with_backoff

DetectorFactory.seed = 0
logger = get_logger(__name__)


class Translator:
    def __init__(self, llm):
        self.llm = llm
        self.data_language = settings.language.data_language
        self.auto_translate = settings.language.auto_translate
        self.cache = {}
        logger.info("Translator initialized")

    def detect_language(self, text: str) -> str:
        try:
            return detect(text)
        except Exception as exc:
            logger.warning(f"Language detection failed: {exc}")
            return self.data_language

    @retry_with_backoff(max_retries=3)
    def translate(self, text: str, target_lang: str, context: str = "general") -> str:
        cache_key = f"{text}:{target_lang}:{context}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        if context == "query":
            prompt = f"Translate to {target_lang} (Vietnamese), keep technical terms:\n{text}\n\nTranslation:"
        elif context == "response":
            prompt = f"Translate to {target_lang}, maintain formatting:\n{text}\n\nTranslation:"
        else:
            prompt = f"Translate to {target_lang}: {text}"

        try:
            response = self.llm.invoke(prompt)
            translated = response.content.strip()
            self.cache[cache_key] = translated
            return translated
        except Exception as exc:
            logger.error(f"Translation failed: {exc}")
            return text

    def process_query(self, query: str, force_translate: bool | None = None) -> Tuple[str, str]:
        detected_lang = self.detect_language(query)
        should_translate = force_translate if force_translate is not None else self.auto_translate

        if should_translate and detected_lang != self.data_language:
            logger.debug(f"Translating query: {detected_lang} -> {self.data_language}")
            translated_query = self.translate(query, self.data_language, context="query")
            return translated_query, detected_lang

        return query, detected_lang

    def translate_response(self, response: str, target_lang: str) -> str:
        if target_lang == self.data_language:
            return response
        logger.debug(f"Translating response: {self.data_language} -> {target_lang}")
        return self.translate(response, target_lang, context="response")

    def clear_cache(self):
        self.cache.clear()
        logger.info("Translation cache cleared")
