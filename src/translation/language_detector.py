"""
Language Detection Service
===========================

Auto-detect language from text using multiple detection methods:
1. langdetect library (primary)
2. Character set analysis (fallback for Asian languages)
3. Common word patterns

No mock data - real production implementation.
"""

import logging
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LanguageDetectionResult:
    """Result of language detection"""
    language_code: str  # ISO 639-1 code
    language_name: str
    confidence: float  # 0.0 to 1.0
    detection_method: str


class LanguageDetector:
    """
    Production language detection service

    Supports 13+ languages with high accuracy for:
    - Asian languages (Chinese, Japanese, Korean, Tamil, Thai)
    - European languages (English, German, French, Spanish, Italian, Dutch, Portuguese)
    - Southeast Asian (Malay)
    """

    # Language codes to names mapping (ISO 639-1)
    LANGUAGE_NAMES = {
        'en': 'English',
        'zh': 'Chinese (Simplified)',
        'ms': 'Malay',
        'ta': 'Tamil',
        'de': 'German',
        'fr': 'French',
        'es': 'Spanish',
        'it': 'Italian',
        'nl': 'Dutch',
        'pt': 'Portuguese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'th': 'Thai'
    }

    # Character ranges for script detection
    SCRIPT_RANGES = {
        'zh': (0x4E00, 0x9FFF),      # CJK Unified Ideographs
        'ja': (0x3040, 0x30FF),      # Hiragana + Katakana
        'ko': (0xAC00, 0xD7AF),      # Hangul Syllables
        'ta': (0x0B80, 0x0BFF),      # Tamil
        'th': (0x0E00, 0x0E7F),      # Thai
    }

    # Common words for pattern matching
    COMMON_WORDS = {
        'en': ['the', 'is', 'and', 'of', 'to', 'a', 'in', 'for'],
        'ms': ['dan', 'yang', 'untuk', 'adalah', 'ini', 'itu', 'pada', 'di'],
        'de': ['der', 'die', 'das', 'und', 'ist', 'ein', 'eine', 'für'],
        'fr': ['le', 'la', 'les', 'et', 'un', 'une', 'pour', 'dans'],
        'es': ['el', 'la', 'los', 'las', 'y', 'un', 'una', 'para'],
        'it': ['il', 'la', 'le', 'e', 'un', 'una', 'per', 'di'],
        'nl': ['de', 'het', 'een', 'en', 'van', 'voor', 'is'],
        'pt': ['o', 'a', 'os', 'as', 'e', 'um', 'uma', 'para']
    }

    def __init__(self):
        """Initialize language detector"""
        self._langdetect_available = False
        self._fasttext_available = False

        # Try to import langdetect
        try:
            import langdetect
            langdetect.DetectorFactory.seed = 0  # For consistent results
            self._langdetect_available = True
            logger.info("✅ langdetect library available")
        except ImportError:
            logger.warning("⚠️ langdetect not available, using fallback detection")

        # Try to import fasttext
        try:
            import fasttext
            self._fasttext_available = True
            logger.info("✅ fasttext library available")
        except ImportError:
            logger.debug("fasttext not available, using alternative methods")

    def detect(self, text: str) -> LanguageDetectionResult:
        """
        Detect language from text

        Args:
            text: Text to detect language from

        Returns:
            LanguageDetectionResult with detected language and confidence
        """
        if not text or not text.strip():
            return LanguageDetectionResult(
                language_code='en',
                language_name='English',
                confidence=0.0,
                detection_method='default'
            )

        text = text.strip()

        # Try langdetect first (most accurate for European languages)
        if self._langdetect_available:
            result = self._detect_with_langdetect(text)
            if result and result.confidence > 0.7:
                return result

        # Try script-based detection for Asian languages
        result = self._detect_by_script(text)
        if result and result.confidence > 0.8:
            return result

        # Try common word pattern matching
        result = self._detect_by_patterns(text)
        if result and result.confidence > 0.6:
            return result

        # Default to English
        logger.warning(f"Could not reliably detect language for text: {text[:50]}...")
        return LanguageDetectionResult(
            language_code='en',
            language_name='English',
            confidence=0.5,
            detection_method='default'
        )

    def _detect_with_langdetect(self, text: str) -> Optional[LanguageDetectionResult]:
        """Detect language using langdetect library"""
        try:
            import langdetect

            lang_code = langdetect.detect(text)

            # Get confidence from detect_langs
            lang_probs = langdetect.detect_langs(text)
            confidence = 0.0
            for lang_prob in lang_probs:
                if lang_prob.lang == lang_code:
                    confidence = lang_prob.prob
                    break

            # Map to our supported languages
            if lang_code not in self.LANGUAGE_NAMES:
                # Try to map common codes
                lang_mapping = {
                    'zh-cn': 'zh',
                    'zh-tw': 'zh',
                    'id': 'ms',  # Indonesian is similar to Malay
                }
                lang_code = lang_mapping.get(lang_code, 'en')

            return LanguageDetectionResult(
                language_code=lang_code,
                language_name=self.LANGUAGE_NAMES.get(lang_code, 'English'),
                confidence=confidence,
                detection_method='langdetect'
            )

        except Exception as e:
            logger.debug(f"langdetect failed: {e}")
            return None

    def _detect_by_script(self, text: str) -> Optional[LanguageDetectionResult]:
        """Detect language by character script analysis"""
        # Count characters in each script
        script_counts = {lang: 0 for lang in self.SCRIPT_RANGES}
        total_chars = 0

        for char in text:
            char_code = ord(char)
            total_chars += 1

            for lang, (start, end) in self.SCRIPT_RANGES.items():
                if start <= char_code <= end:
                    script_counts[lang] += 1
                    break

        if total_chars == 0:
            return None

        # Find dominant script
        max_count = 0
        detected_lang = None

        for lang, count in script_counts.items():
            if count > max_count:
                max_count = count
                detected_lang = lang

        # Require at least 30% of characters to be in the script
        if max_count > 0 and (max_count / total_chars) >= 0.3:
            confidence = min(max_count / total_chars, 1.0)
            return LanguageDetectionResult(
                language_code=detected_lang,
                language_name=self.LANGUAGE_NAMES[detected_lang],
                confidence=confidence,
                detection_method='script_analysis'
            )

        return None

    def _detect_by_patterns(self, text: str) -> Optional[LanguageDetectionResult]:
        """Detect language by common word patterns"""
        text_lower = text.lower()
        words = text_lower.split()

        if not words:
            return None

        # Count matches for each language
        lang_scores = {}

        for lang, common_words in self.COMMON_WORDS.items():
            matches = sum(1 for word in words if word in common_words)
            if matches > 0:
                lang_scores[lang] = matches / len(words)

        if not lang_scores:
            return None

        # Get best match
        detected_lang = max(lang_scores, key=lang_scores.get)
        confidence = lang_scores[detected_lang]

        # Require at least 10% match rate
        if confidence >= 0.1:
            return LanguageDetectionResult(
                language_code=detected_lang,
                language_name=self.LANGUAGE_NAMES[detected_lang],
                confidence=min(confidence * 3, 1.0),  # Scale up confidence
                detection_method='pattern_matching'
            )

        return None

    def detect_batch(self, texts: List[str]) -> List[LanguageDetectionResult]:
        """
        Detect language for multiple texts

        Args:
            texts: List of texts to detect

        Returns:
            List of LanguageDetectionResult
        """
        return [self.detect(text) for text in texts]

    def is_supported_language(self, lang_code: str) -> bool:
        """Check if language code is supported"""
        return lang_code in self.LANGUAGE_NAMES

    def get_supported_languages(self) -> Dict[str, str]:
        """Get all supported languages"""
        return self.LANGUAGE_NAMES.copy()


# Convenience function
def detect_language(text: str) -> LanguageDetectionResult:
    """
    Detect language from text (convenience function)

    Args:
        text: Text to detect language from

    Returns:
        LanguageDetectionResult
    """
    detector = LanguageDetector()
    return detector.detect(text)


# Global detector instance (singleton pattern)
_detector_instance = None


def get_language_detector() -> LanguageDetector:
    """Get global language detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = LanguageDetector()
    return _detector_instance
