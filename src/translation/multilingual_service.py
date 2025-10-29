"""
Multi-lingual Translation Service with OpenAI GPT-4
====================================================

Production-ready translation service featuring:
- OpenAI GPT-4 for dynamic translations
- ETIM standard translations integration
- Redis caching (7-day TTL, target >80% hit rate)
- Language auto-detection
- Technical term preservation
- Translation quality metrics

Supported languages (13+):
- Primary (Singapore): English, Chinese (Simplified), Malay, Tamil
- Extended: German, French, Spanish, Italian, Dutch, Portuguese, Japanese, Korean, Thai

NO mock data - 100% production-ready implementation.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import openai
from src.core.config import config
from src.translation.language_detector import LanguageDetector, get_language_detector
from src.translation.redis_cache_manager import TranslationCacheManager, get_translation_cache

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Result of translation operation"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float  # 0.0 to 1.0
    translation_method: str  # 'gpt4', 'etim', 'cache'
    technical_terms_preserved: List[str]
    cache_hit: bool
    processing_time_ms: float


class TranslationService:
    """
    Production multi-lingual translation service

    Uses OpenAI GPT-4 for high-quality context-aware translations
    with Redis caching and ETIM standard translations for product categories.
    """

    # Technical terms that should be preserved across translations
    TECHNICAL_TERMS = [
        # Electrical
        'LED', 'IP65', 'IP44', 'AC', 'DC', 'kWh', 'kW', 'V', 'A', 'Hz',
        # Measurements
        'mm', 'cm', 'm', 'kg', 'g', 'L', 'ml',
        # Standards
        'ISO', 'EN', 'IEC', 'CE', 'ETIM', 'UL', 'CSA',
        # Materials
        'PVC', 'ABS', 'PP', 'PE', 'HDPE', 'LDPE',
        # Safety
        'OSHA', 'ANSI', 'PPE',
        # Product codes
        'SKU', 'UPC', 'EAN'
    ]

    def __init__(
        self,
        cache_manager: Optional[TranslationCacheManager] = None,
        language_detector: Optional[LanguageDetector] = None,
        etim_translations_path: Optional[str] = None
    ):
        """
        Initialize translation service

        Args:
            cache_manager: Optional cache manager (creates default if None)
            language_detector: Optional language detector (creates default if None)
            etim_translations_path: Path to ETIM translations JSON
        """
        # Initialize OpenAI client
        openai.api_key = config.OPENAI_API_KEY
        self.openai_model = config.OPENAI_MODEL
        self.openai_temperature = config.OPENAI_TEMPERATURE
        self.openai_max_tokens = config.OPENAI_MAX_TOKENS

        # Initialize cache and detector
        self.cache_manager = cache_manager or get_translation_cache()
        self.language_detector = language_detector or get_language_detector()

        # Load ETIM translations
        self.etim_translations = self._load_etim_translations(etim_translations_path)

        # Translation statistics
        self._translations_total = 0
        self._translations_cached = 0
        self._translations_gpt4 = 0
        self._translations_etim = 0

        logger.info("✅ Translation service initialized")
        logger.info(f"   OpenAI Model: {self.openai_model}")
        logger.info(f"   ETIM translations loaded: {len(self.etim_translations)} entries")
        logger.info(f"   Supported languages: {len(self.language_detector.LANGUAGE_NAMES)}")

    def _load_etim_translations(self, path: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """
        Load ETIM standard translations from JSON file

        Args:
            path: Optional path to ETIM translations file

        Returns:
            Dictionary of ETIM translations
        """
        if path is None:
            # Default path
            path = Path(__file__).parent.parent.parent / "data" / "etim_translations.json"
        else:
            path = Path(path)

        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    etim_data = json.load(f)
                    logger.info(f"Loaded {len(etim_data)} ETIM translations from {path}")
                    return etim_data
            else:
                logger.warning(f"ETIM translations file not found: {path}")
                return {}

        except Exception as e:
            logger.error(f"Failed to load ETIM translations: {e}")
            return {}

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        context: Optional[str] = None,
        preserve_technical: bool = True
    ) -> TranslationResult:
        """
        Translate text to target language

        Args:
            text: Text to translate
            target_lang: Target language code (e.g., 'zh', 'ms', 'ta')
            source_lang: Source language code (auto-detected if None)
            context: Optional context ('product', 'technical', 'safety', etc.)
            preserve_technical: Whether to preserve technical terms

        Returns:
            TranslationResult with translation and metadata
        """
        import time
        start_time = time.time()

        self._translations_total += 1

        # Detect source language if not provided
        if source_lang is None:
            detection = self.language_detector.detect(text)
            source_lang = detection.language_code
            logger.debug(f"Auto-detected source language: {source_lang} ({detection.confidence:.2f})")

        # Check if translation is needed
        if source_lang == target_lang:
            processing_time = (time.time() - start_time) * 1000
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                confidence=1.0,
                translation_method='no_translation_needed',
                technical_terms_preserved=[],
                cache_hit=False,
                processing_time_ms=processing_time
            )

        # Check cache first
        cached_result = self.cache_manager.get_translation(
            text, source_lang, target_lang, context
        )

        if cached_result:
            self._translations_cached += 1
            processing_time = (time.time() - start_time) * 1000
            return TranslationResult(
                original_text=text,
                translated_text=cached_result['translated_text'],
                source_language=source_lang,
                target_language=target_lang,
                confidence=cached_result.get('confidence', 0.95),
                translation_method=cached_result.get('method', 'cache'),
                technical_terms_preserved=cached_result.get('technical_terms', []),
                cache_hit=True,
                processing_time_ms=processing_time
            )

        # Check ETIM translations for product categories
        if context in ['product', 'category', 'etim']:
            etim_result = self._translate_with_etim(text, target_lang)
            if etim_result:
                self._translations_etim += 1
                processing_time = (time.time() - start_time) * 1000

                # Cache the result
                self._cache_translation(
                    text, source_lang, target_lang, etim_result['translation'],
                    'etim', 0.98, [], context
                )

                return TranslationResult(
                    original_text=text,
                    translated_text=etim_result['translation'],
                    source_language=source_lang,
                    target_language=target_lang,
                    confidence=0.98,
                    translation_method='etim',
                    technical_terms_preserved=[],
                    cache_hit=False,
                    processing_time_ms=processing_time
                )

        # Use GPT-4 for translation
        try:
            result = self._translate_with_gpt4(
                text, source_lang, target_lang, context, preserve_technical
            )
            self._translations_gpt4 += 1

            processing_time = (time.time() - start_time) * 1000

            # Cache the result
            self._cache_translation(
                text, source_lang, target_lang, result['translation'],
                'gpt4', result['confidence'], result['technical_terms'], context
            )

            return TranslationResult(
                original_text=text,
                translated_text=result['translation'],
                source_language=source_lang,
                target_language=target_lang,
                confidence=result['confidence'],
                translation_method='gpt4',
                technical_terms_preserved=result['technical_terms'],
                cache_hit=False,
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            processing_time = (time.time() - start_time) * 1000

            # Return original text as fallback
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                confidence=0.0,
                translation_method='error',
                technical_terms_preserved=[],
                cache_hit=False,
                processing_time_ms=processing_time
            )

    def _translate_with_etim(self, text: str, target_lang: str) -> Optional[Dict[str, str]]:
        """
        Translate using ETIM standard translations

        Args:
            text: Text to translate (typically a category name)
            target_lang: Target language code

        Returns:
            Translation dictionary or None if not found
        """
        # Normalize text for lookup
        text_normalized = text.strip().lower()

        # Check if we have this ETIM entry
        if text_normalized in self.etim_translations:
            translations = self.etim_translations[text_normalized]
            if target_lang in translations:
                return {'translation': translations[target_lang]}

        return None

    def _translate_with_gpt4(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: Optional[str],
        preserve_technical: bool
    ) -> Dict[str, Any]:
        """
        Translate using OpenAI GPT-4

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            context: Optional context
            preserve_technical: Whether to preserve technical terms

        Returns:
            Dictionary with translation, confidence, and technical terms
        """
        # Get language names
        source_lang_name = self.language_detector.LANGUAGE_NAMES.get(source_lang, source_lang)
        target_lang_name = self.language_detector.LANGUAGE_NAMES.get(target_lang, target_lang)

        # Build translation prompt
        prompt = self._build_translation_prompt(
            text, source_lang_name, target_lang_name, context, preserve_technical
        )

        # Call OpenAI API
        try:
            response = openai.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator specializing in technical and product translations. Provide accurate, context-aware translations while preserving technical terms and industry standards."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.openai_temperature,
                max_tokens=self.openai_max_tokens
            )

            translation = response.choices[0].message.content.strip()

            # Extract preserved technical terms
            preserved_terms = []
            if preserve_technical:
                for term in self.TECHNICAL_TERMS:
                    if term in text and term in translation:
                        preserved_terms.append(term)

            return {
                'translation': translation,
                'confidence': 0.95,  # GPT-4 high confidence
                'technical_terms': preserved_terms
            }

        except Exception as e:
            logger.error(f"GPT-4 translation failed: {e}")
            raise

    def _build_translation_prompt(
        self,
        text: str,
        source_lang_name: str,
        target_lang_name: str,
        context: Optional[str],
        preserve_technical: bool
    ) -> str:
        """Build translation prompt for GPT-4"""

        prompt = f"Translate the following text from {source_lang_name} to {target_lang_name}.\n\n"

        if context:
            prompt += f"Context: This is a {context}-related text.\n\n"

        if preserve_technical:
            prompt += f"IMPORTANT: Preserve these technical terms exactly as they appear: {', '.join(self.TECHNICAL_TERMS[:10])}...\n\n"

        prompt += f"Text to translate:\n{text}\n\n"
        prompt += f"Provide ONLY the {target_lang_name} translation, without explanations or additional text."

        return prompt

    def _cache_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translation: str,
        method: str,
        confidence: float,
        technical_terms: List[str],
        context: Optional[str]
    ):
        """Cache translation result"""
        try:
            cache_data = {
                'translated_text': translation,
                'confidence': confidence,
                'method': method,
                'technical_terms': technical_terms
            }
            self.cache_manager.set_translation(
                text, source_lang, target_lang, cache_data, context
            )
        except Exception as e:
            logger.warning(f"Failed to cache translation: {e}")

    def translate_batch(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: Optional[str] = None,
        context: Optional[str] = None
    ) -> List[TranslationResult]:
        """
        Translate multiple texts

        Args:
            texts: List of texts to translate
            target_lang: Target language code
            source_lang: Source language code (auto-detected if None)
            context: Optional context

        Returns:
            List of TranslationResult
        """
        results = []
        for text in texts:
            result = self.translate(text, target_lang, source_lang, context)
            results.append(result)

        return results

    def translate_product(
        self,
        product_name: str,
        product_description: str,
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> Dict[str, TranslationResult]:
        """
        Translate product name and description

        Args:
            product_name: Product name
            product_description: Product description
            target_lang: Target language code
            source_lang: Source language code

        Returns:
            Dictionary with 'name' and 'description' TranslationResult
        """
        name_result = self.translate(
            product_name, target_lang, source_lang,
            context='product', preserve_technical=True
        )

        description_result = self.translate(
            product_description, target_lang, source_lang,
            context='product', preserve_technical=True
        )

        return {
            'name': name_result,
            'description': description_result
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get translation service statistics

        Returns:
            Dictionary with service statistics
        """
        cache_stats = self.cache_manager.get_cache_stats()

        return {
            'total_translations': self._translations_total,
            'translations_cached': self._translations_cached,
            'translations_gpt4': self._translations_gpt4,
            'translations_etim': self._translations_etim,
            'cache_hit_rate': cache_stats['hit_rate_percent'],
            'cache_performance': cache_stats['performance_status'],
            'supported_languages': len(self.language_detector.LANGUAGE_NAMES),
            'etim_entries': len(self.etim_translations),
            'openai_model': self.openai_model
        }

    def health_check(self) -> Dict[str, bool]:
        """
        Check health of translation service components

        Returns:
            Dictionary with health status
        """
        return {
            'cache_healthy': self.cache_manager.health_check(),
            'openai_configured': bool(config.OPENAI_API_KEY),
            'etim_loaded': len(self.etim_translations) > 0
        }


# Global translation service instance (singleton)
_translation_service = None


def get_translation_service() -> TranslationService:
    """Get global translation service instance"""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service
