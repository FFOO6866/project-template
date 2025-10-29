"""
Multi-lingual Translation Service
=================================

Production-ready translation system with:
- OpenAI GPT-4 translation engine
- Redis caching layer (7-day TTL)
- ETIM standard translations
- Language auto-detection
- Technical term preservation
- Translation quality metrics

Supported languages (13+):
- Primary: English, Chinese (Simplified), Malay, Tamil
- Extended: German, French, Spanish, Italian, Dutch, Portuguese, Japanese, Korean, Thai

Usage:
    from src.translation import TranslationService

    service = TranslationService()
    result = service.translate("Safety helmet", target_lang="zh")
    # Returns: {"translation": "安全头盔", "confidence": 0.95}
"""

from .multilingual_service import TranslationService, TranslationResult
from .language_detector import LanguageDetector, detect_language
from .redis_cache_manager import TranslationCacheManager

__all__ = [
    'TranslationService',
    'TranslationResult',
    'LanguageDetector',
    'detect_language',
    'TranslationCacheManager'
]
