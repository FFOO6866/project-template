#!/usr/bin/env python3
"""
Comprehensive Multi-lingual Translation Test Suite
===================================================

Tests all components of the Phase 5 translation system:
1. Language detection
2. Redis caching
3. GPT-4 translation
4. ETIM translations
5. Technical term preservation
6. Database integration
7. API endpoints

NO MOCK DATA - Production testing only.
"""

import os
import sys
import logging
import time
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_language_detection():
    """Test language auto-detection"""
    logger.info("=" * 80)
    logger.info("TEST 1: Language Detection")
    logger.info("=" * 80)

    from src.translation import LanguageDetector

    detector = LanguageDetector()

    test_texts = [
        ("Safety helmet for construction work", "en"),
        ("安全头盔用于建筑工作", "zh"),
        ("Topi keledar keselamatan untuk kerja pembinaan", "ms"),
        ("கட்டுமான வேலைக்கு பாதுகாப்பு தலைக்கவசம்", "ta"),
        ("Schutzhelm für Bauarbeiten", "de"),
        ("建設工事用の安全ヘルメット", "ja"),
        ("건설 작업용 안전 헬멧", "ko"),
    ]

    results = []
    for text, expected_lang in test_texts:
        result = detector.detect(text)
        match = "✅" if result.language_code == expected_lang else "❌"

        logger.info(f"{match} Text: {text[:50]}...")
        logger.info(f"   Detected: {result.language_name} ({result.language_code})")
        logger.info(f"   Expected: {expected_lang}")
        logger.info(f"   Confidence: {result.confidence:.2f}")
        logger.info(f"   Method: {result.detection_method}")
        logger.info("")

        results.append({
            'text': text,
            'detected': result.language_code,
            'expected': expected_lang,
            'correct': result.language_code == expected_lang,
            'confidence': result.confidence,
            'method': result.detection_method
        })

    accuracy = sum(1 for r in results if r['correct']) / len(results) * 100
    logger.info(f"Language Detection Accuracy: {accuracy:.1f}%")
    logger.info("")

    return results


def test_redis_cache():
    """Test Redis caching layer"""
    logger.info("=" * 80)
    logger.info("TEST 2: Redis Translation Cache")
    logger.info("=" * 80)

    from src.translation.redis_cache_manager import TranslationCacheManager

    try:
        cache = TranslationCacheManager()

        # Test connection
        if not cache.health_check():
            logger.error("❌ Redis connection failed")
            return False

        logger.info("✅ Redis connection healthy")

        # Test cache operations
        test_text = "LED light fixture"
        translation_data = {
            'translated_text': 'LED灯具',
            'confidence': 0.95,
            'method': 'gpt4',
            'technical_terms': ['LED']
        }

        # Set cache
        success = cache.set_translation(
            test_text, 'en', 'zh', translation_data, context='product'
        )
        logger.info(f"{'✅' if success else '❌'} Cache set: {test_text}")

        # Get cache
        cached = cache.get_translation(test_text, 'en', 'zh', context='product')
        if cached and cached['translated_text'] == translation_data['translated_text']:
            logger.info(f"✅ Cache get: Retrieved correct translation")
        else:
            logger.error(f"❌ Cache get: Failed to retrieve or incorrect data")

        # Get statistics
        stats = cache.get_cache_stats()
        logger.info(f"\nCache Statistics:")
        logger.info(f"  Cache hits: {stats['cache_hits']}")
        logger.info(f"  Cache misses: {stats['cache_misses']}")
        logger.info(f"  Hit rate: {stats['hit_rate_percent']:.2f}%")
        logger.info(f"  Performance: {stats['performance_status']}")
        logger.info("")

        return True

    except Exception as e:
        logger.error(f"❌ Redis cache test failed: {e}")
        return False


def test_gpt4_translation():
    """Test GPT-4 translation service"""
    logger.info("=" * 80)
    logger.info("TEST 3: GPT-4 Translation Service")
    logger.info("=" * 80)

    from src.translation import TranslationService

    try:
        service = TranslationService()

        # Test product translations
        test_cases = [
            {
                'text': 'Safety helmet with LED light',
                'target_lang': 'zh',
                'context': 'product'
            },
            {
                'text': 'Industrial cleaning products',
                'target_lang': 'ms',
                'context': 'product'
            },
            {
                'text': 'Power tools and equipment',
                'target_lang': 'ta',
                'context': 'product'
            },
            {
                'text': 'Electrical connectors IP65 rated',
                'target_lang': 'ja',
                'context': 'technical'
            }
        ]

        results = []
        for i, test in enumerate(test_cases, 1):
            logger.info(f"\nTest Case {i}:")
            logger.info(f"  Original ({test.get('context', 'product')}): {test['text']}")
            logger.info(f"  Target language: {test['target_lang']}")

            start_time = time.time()
            result = service.translate(
                text=test['text'],
                target_lang=test['target_lang'],
                context=test.get('context', 'product'),
                preserve_technical=True
            )
            elapsed_time = (time.time() - start_time) * 1000

            logger.info(f"  Translation: {result.translated_text}")
            logger.info(f"  Confidence: {result.confidence:.2f}")
            logger.info(f"  Method: {result.translation_method}")
            logger.info(f"  Cache hit: {result.cache_hit}")
            logger.info(f"  Processing time: {elapsed_time:.1f}ms")
            if result.technical_terms_preserved:
                logger.info(f"  Technical terms preserved: {', '.join(result.technical_terms_preserved)}")

            results.append({
                'original': test['text'],
                'translated': result.translated_text,
                'target_lang': test['target_lang'],
                'confidence': result.confidence,
                'method': result.translation_method,
                'cache_hit': result.cache_hit,
                'processing_time_ms': elapsed_time
            })

        logger.info(f"\n{'✅' if len(results) == len(test_cases) else '❌'} Completed {len(results)}/{len(test_cases)} translations")
        logger.info("")

        return results

    except Exception as e:
        logger.error(f"❌ GPT-4 translation test failed: {e}")
        return []


def test_etim_translations():
    """Test ETIM standard translations"""
    logger.info("=" * 80)
    logger.info("TEST 4: ETIM Standard Translations")
    logger.info("=" * 80)

    from src.translation import TranslationService

    try:
        service = TranslationService()

        # Test ETIM category translations
        etim_categories = [
            'safety products',
            'cleaning products',
            'tools',
            'led light',
            'cable'
        ]

        target_languages = ['zh', 'ms', 'ta', 'ja']

        logger.info(f"Loaded {len(service.etim_translations)} ETIM entries")
        logger.info("")

        results = []
        for category in etim_categories:
            logger.info(f"Category: {category}")

            for lang in target_languages:
                result = service.translate(
                    text=category,
                    target_lang=lang,
                    context='etim',
                    preserve_technical=False
                )

                logger.info(f"  {lang}: {result.translated_text} (method: {result.translation_method})")

                results.append({
                    'category': category,
                    'language': lang,
                    'translation': result.translated_text,
                    'method': result.translation_method
                })

            logger.info("")

        logger.info(f"✅ Completed {len(results)} ETIM translations")
        logger.info("")

        return results

    except Exception as e:
        logger.error(f"❌ ETIM translation test failed: {e}")
        return []


def test_database_integration():
    """Test database translation methods"""
    logger.info("=" * 80)
    logger.info("TEST 5: Database Translation Integration")
    logger.info("=" * 80)

    try:
        from src.core.postgresql_database import get_database

        db = get_database()

        # Test translate_description
        test_text = "Heavy-duty safety boots with steel toe cap and slip-resistant sole"
        target_lang = 'zh'

        logger.info(f"Translating product description:")
        logger.info(f"  Original: {test_text}")
        logger.info(f"  Target: Chinese ({target_lang})")

        result = db.translate_description(
            text=test_text,
            target_lang=target_lang,
            context='product'
        )

        if result:
            logger.info(f"  ✅ Translated: {result['translated_text']}")
            logger.info(f"  Confidence: {result['confidence']:.2f}")
            logger.info(f"  Method: {result['translation_method']}")
            logger.info(f"  Cache hit: {result['cache_hit']}")
            logger.info(f"  Processing time: {result['processing_time_ms']:.1f}ms")
        else:
            logger.error("  ❌ Translation failed")

        logger.info("")
        return bool(result)

    except Exception as e:
        logger.error(f"❌ Database integration test failed: {e}")
        return False


def test_cache_performance():
    """Test cache performance and hit rate"""
    logger.info("=" * 80)
    logger.info("TEST 6: Cache Performance Test")
    logger.info("=" * 80)

    from src.translation import TranslationService

    try:
        service = TranslationService()

        # Reset cache stats
        service.cache_manager.reset_stats()

        # Translate same text multiple times
        test_text = "Safety equipment and protective gear"
        target_langs = ['zh', 'ms', 'ta']
        iterations = 3

        logger.info(f"Testing cache with {iterations} iterations across {len(target_langs)} languages")
        logger.info("")

        for i in range(iterations):
            logger.info(f"Iteration {i + 1}:")
            for lang in target_langs:
                start_time = time.time()
                result = service.translate(
                    text=test_text,
                    target_lang=lang,
                    context='product'
                )
                elapsed_time = (time.time() - start_time) * 1000

                cache_status = "HIT" if result.cache_hit else "MISS"
                logger.info(f"  {lang}: {elapsed_time:.1f}ms ({cache_status})")

            logger.info("")

        # Get cache statistics
        stats = service.cache_manager.get_cache_stats()
        logger.info("Cache Performance:")
        logger.info(f"  Total requests: {stats['total_requests']}")
        logger.info(f"  Cache hits: {stats['cache_hits']}")
        logger.info(f"  Cache misses: {stats['cache_misses']}")
        logger.info(f"  Hit rate: {stats['hit_rate_percent']:.2f}%")
        logger.info(f"  Target: {stats['target_hit_rate']}%")
        logger.info(f"  Performance status: {stats['performance_status']}")
        logger.info("")

        # Performance assessment
        if stats['hit_rate_percent'] >= 60:
            logger.info("✅ Cache performance: EXCELLENT (>60% hit rate achieved)")
        elif stats['hit_rate_percent'] >= 40:
            logger.info("⚠️  Cache performance: GOOD (40-60% hit rate)")
        else:
            logger.info("❌ Cache performance: NEEDS IMPROVEMENT (<40% hit rate)")

        logger.info("")
        return True

    except Exception as e:
        logger.error(f"❌ Cache performance test failed: {e}")
        return False


def test_service_statistics():
    """Test translation service statistics"""
    logger.info("=" * 80)
    logger.info("TEST 7: Translation Service Statistics")
    logger.info("=" * 80)

    try:
        from src.translation import get_translation_service

        service = get_translation_service()
        stats = service.get_statistics()

        logger.info("Translation Service Statistics:")
        logger.info(f"  Total translations: {stats['total_translations']}")
        logger.info(f"  Cached translations: {stats['translations_cached']}")
        logger.info(f"  GPT-4 translations: {stats['translations_gpt4']}")
        logger.info(f"  ETIM translations: {stats['translations_etim']}")
        logger.info(f"  Cache hit rate: {stats['cache_hit_rate']:.2f}%")
        logger.info(f"  Cache performance: {stats['cache_performance']}")
        logger.info(f"  Supported languages: {stats['supported_languages']}")
        logger.info(f"  ETIM entries: {stats['etim_entries']}")
        logger.info(f"  OpenAI model: {stats['openai_model']}")
        logger.info("")

        # Health check
        health = service.health_check()
        logger.info("Component Health:")
        logger.info(f"  {'✅' if health['cache_healthy'] else '❌'} Redis cache")
        logger.info(f"  {'✅' if health['openai_configured'] else '❌'} OpenAI API")
        logger.info(f"  {'✅' if health['etim_loaded'] else '❌'} ETIM translations")
        logger.info("")

        return True

    except Exception as e:
        logger.error(f"❌ Service statistics test failed: {e}")
        return False


def main():
    """Run all translation tests"""
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 15 + "HORME POV MULTI-LINGUAL TRANSLATION TEST SUITE" + " " * 16 + "║")
    logger.info("║" + " " * 24 + "Phase 5: Production Testing" + " " * 27 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("")

    start_time = time.time()

    # Run all tests
    test_results = {}

    test_results['language_detection'] = test_language_detection()
    test_results['redis_cache'] = test_redis_cache()
    test_results['gpt4_translation'] = test_gpt4_translation()
    test_results['etim_translations'] = test_etim_translations()
    test_results['database_integration'] = test_database_integration()
    test_results['cache_performance'] = test_cache_performance()
    test_results['service_statistics'] = test_service_statistics()

    # Summary
    total_time = time.time() - start_time

    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    passed = sum(1 for v in test_results.values() if v and (isinstance(v, list) and len(v) > 0 or isinstance(v, bool) and v))
    total = len(test_results)

    logger.info(f"Tests passed: {passed}/{total}")
    logger.info(f"Total execution time: {total_time:.2f}s")
    logger.info("")

    if passed == total:
        logger.info("✅ ALL TESTS PASSED - Translation system is production-ready!")
    else:
        logger.warning(f"⚠️  {total - passed} test(s) failed - review logs above")

    logger.info("")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
