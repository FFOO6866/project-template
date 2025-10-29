#!/usr/bin/env python3
"""
Translation Accuracy Test for Asian Languages
==============================================

Comprehensive accuracy testing for:
- Chinese (Simplified) - zh
- Malay - ms
- Tamil - ta

Tests translation quality, technical term preservation,
and context-aware translation with real GPT-4 API.

NO MOCK DATA - Production validation only.
"""

import os
import sys
import logging
import time
import json
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Test cases with expected translations (reference)
TEST_CASES_CHINESE = [
    {
        'en': 'Safety helmet',
        'zh_expected': '安全头盔',
        'context': 'product',
        'technical_terms': []
    },
    {
        'en': 'LED light fixture IP65',
        'zh_expected': 'LED灯具',  # LED and IP65 should be preserved
        'context': 'technical',
        'technical_terms': ['LED', 'IP65']
    },
    {
        'en': 'Industrial cleaning products',
        'zh_expected': '工业清洁产品',
        'context': 'product',
        'technical_terms': []
    },
    {
        'en': 'Power tool with 24V DC motor',
        'zh_expected': '电动工具',
        'context': 'technical',
        'technical_terms': ['DC', '24V']
    },
    {
        'en': 'Safety goggles for construction work',
        'zh_expected': '建筑工作用安全护目镜',
        'context': 'product',
        'technical_terms': []
    }
]

TEST_CASES_MALAY = [
    {
        'en': 'Safety helmet',
        'ms_expected': 'Topi keledar keselamatan',
        'context': 'product',
        'technical_terms': []
    },
    {
        'en': 'Cleaning products',
        'ms_expected': 'Produk pembersihan',
        'context': 'product',
        'technical_terms': []
    },
    {
        'en': 'LED light',
        'ms_expected': 'Lampu LED',
        'context': 'product',
        'technical_terms': ['LED']
    },
    {
        'en': 'Power tools for construction',
        'ms_expected': 'Alat berkuasa untuk pembinaan',
        'context': 'product',
        'technical_terms': []
    },
    {
        'en': 'Safety equipment and PPE',
        'ms_expected': 'Peralatan keselamatan',
        'context': 'product',
        'technical_terms': ['PPE']
    }
]

TEST_CASES_TAMIL = [
    {
        'en': 'Safety helmet',
        'ta_expected': 'பாதுகாப்பு தலைக்கவசம்',
        'context': 'product',
        'technical_terms': []
    },
    {
        'en': 'Cleaning products',
        'ta_expected': 'சுத்தம் செய்யும் பொருட்கள்',
        'context': 'product',
        'technical_terms': []
    },
    {
        'en': 'LED lighting fixture',
        'ta_expected': 'LED விளக்கு பொருத்து',
        'context': 'product',
        'technical_terms': ['LED']
    },
    {
        'en': 'Power tools',
        'ta_expected': 'மின்சார கருவிகள்',
        'context': 'product',
        'technical_terms': []
    },
    {
        'en': 'Safety equipment',
        'ta_expected': 'பாதுகாப்பு உபகரணங்கள்',
        'context': 'product',
        'technical_terms': []
    }
]


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate simple character overlap similarity (0.0 to 1.0)
    For production use, consider using more sophisticated methods
    """
    if not str1 or not str2:
        return 0.0

    # Simple character set overlap for Asian languages
    set1 = set(str1)
    set2 = set(str2)

    if not set1 or not set2:
        return 0.0

    overlap = len(set1 & set2)
    total = len(set1 | set2)

    return overlap / total if total > 0 else 0.0


def test_chinese_translation():
    """Test Chinese (Simplified) translation accuracy"""
    logger.info("=" * 80)
    logger.info("CHINESE (SIMPLIFIED) TRANSLATION ACCURACY TEST")
    logger.info("=" * 80)

    from src.translation import TranslationService

    service = TranslationService()
    results = []

    for i, test_case in enumerate(TEST_CASES_CHINESE, 1):
        logger.info(f"\nTest Case {i}:")
        logger.info(f"  English: {test_case['en']}")
        logger.info(f"  Expected (reference): {test_case['zh_expected']}")

        start_time = time.time()
        result = service.translate(
            text=test_case['en'],
            target_lang='zh',
            context=test_case['context'],
            preserve_technical=True
        )
        elapsed_time = (time.time() - start_time) * 1000

        logger.info(f"  GPT-4 Translation: {result.translated_text}")
        logger.info(f"  Confidence: {result.confidence:.2f}")
        logger.info(f"  Method: {result.translation_method}")
        logger.info(f"  Processing time: {elapsed_time:.1f}ms")

        # Check technical term preservation
        terms_preserved = all(
            term in result.translated_text for term in test_case['technical_terms']
        )

        if test_case['technical_terms']:
            logger.info(f"  Technical terms preserved: {'✅' if terms_preserved else '❌'}")
            if result.technical_terms_preserved:
                logger.info(f"    Preserved: {', '.join(result.technical_terms_preserved)}")

        # Calculate similarity (for reference only)
        similarity = calculate_similarity(result.translated_text, test_case['zh_expected'])
        logger.info(f"  Similarity to reference: {similarity:.2%}")

        results.append({
            'english': test_case['en'],
            'translation': result.translated_text,
            'expected': test_case['zh_expected'],
            'confidence': result.confidence,
            'terms_preserved': terms_preserved,
            'similarity': similarity,
            'processing_time_ms': elapsed_time
        })

    # Summary
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    avg_similarity = sum(r['similarity'] for r in results) / len(results)
    terms_accuracy = sum(1 for r in results if r['terms_preserved']) / len(results) * 100

    logger.info(f"\n{'=' * 80}")
    logger.info("CHINESE TRANSLATION SUMMARY:")
    logger.info(f"  Total test cases: {len(results)}")
    logger.info(f"  Average confidence: {avg_confidence:.2f}")
    logger.info(f"  Average similarity: {avg_similarity:.2%}")
    logger.info(f"  Technical terms accuracy: {terms_accuracy:.1f}%")
    logger.info("")

    return results


def test_malay_translation():
    """Test Malay translation accuracy"""
    logger.info("=" * 80)
    logger.info("MALAY TRANSLATION ACCURACY TEST")
    logger.info("=" * 80)

    from src.translation import TranslationService

    service = TranslationService()
    results = []

    for i, test_case in enumerate(TEST_CASES_MALAY, 1):
        logger.info(f"\nTest Case {i}:")
        logger.info(f"  English: {test_case['en']}")
        logger.info(f"  Expected (reference): {test_case['ms_expected']}")

        start_time = time.time()
        result = service.translate(
            text=test_case['en'],
            target_lang='ms',
            context=test_case['context'],
            preserve_technical=True
        )
        elapsed_time = (time.time() - start_time) * 1000

        logger.info(f"  GPT-4 Translation: {result.translated_text}")
        logger.info(f"  Confidence: {result.confidence:.2f}")
        logger.info(f"  Method: {result.translation_method}")
        logger.info(f"  Processing time: {elapsed_time:.1f}ms")

        # Check technical term preservation
        terms_preserved = all(
            term in result.translated_text for term in test_case['technical_terms']
        )

        if test_case['technical_terms']:
            logger.info(f"  Technical terms preserved: {'✅' if terms_preserved else '❌'}")

        # Calculate similarity (for reference only)
        similarity = calculate_similarity(result.translated_text, test_case['ms_expected'])
        logger.info(f"  Similarity to reference: {similarity:.2%}")

        results.append({
            'english': test_case['en'],
            'translation': result.translated_text,
            'expected': test_case['ms_expected'],
            'confidence': result.confidence,
            'terms_preserved': terms_preserved,
            'similarity': similarity,
            'processing_time_ms': elapsed_time
        })

    # Summary
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    avg_similarity = sum(r['similarity'] for r in results) / len(results)
    terms_accuracy = sum(1 for r in results if r['terms_preserved']) / len(results) * 100

    logger.info(f"\n{'=' * 80}")
    logger.info("MALAY TRANSLATION SUMMARY:")
    logger.info(f"  Total test cases: {len(results)}")
    logger.info(f"  Average confidence: {avg_confidence:.2f}")
    logger.info(f"  Average similarity: {avg_similarity:.2%}")
    logger.info(f"  Technical terms accuracy: {terms_accuracy:.1f}%")
    logger.info("")

    return results


def test_tamil_translation():
    """Test Tamil translation accuracy"""
    logger.info("=" * 80)
    logger.info("TAMIL TRANSLATION ACCURACY TEST")
    logger.info("=" * 80)

    from src.translation import TranslationService

    service = TranslationService()
    results = []

    for i, test_case in enumerate(TEST_CASES_TAMIL, 1):
        logger.info(f"\nTest Case {i}:")
        logger.info(f"  English: {test_case['en']}")
        logger.info(f"  Expected (reference): {test_case['ta_expected']}")

        start_time = time.time()
        result = service.translate(
            text=test_case['en'],
            target_lang='ta',
            context=test_case['context'],
            preserve_technical=True
        )
        elapsed_time = (time.time() - start_time) * 1000

        logger.info(f"  GPT-4 Translation: {result.translated_text}")
        logger.info(f"  Confidence: {result.confidence:.2f}")
        logger.info(f"  Method: {result.translation_method}")
        logger.info(f"  Processing time: {elapsed_time:.1f}ms")

        # Check technical term preservation
        terms_preserved = all(
            term in result.translated_text for term in test_case['technical_terms']
        )

        if test_case['technical_terms']:
            logger.info(f"  Technical terms preserved: {'✅' if terms_preserved else '❌'}")

        # Calculate similarity (for reference only)
        similarity = calculate_similarity(result.translated_text, test_case['ta_expected'])
        logger.info(f"  Similarity to reference: {similarity:.2%}")

        results.append({
            'english': test_case['en'],
            'translation': result.translated_text,
            'expected': test_case['ta_expected'],
            'confidence': result.confidence,
            'terms_preserved': terms_preserved,
            'similarity': similarity,
            'processing_time_ms': elapsed_time
        })

    # Summary
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    avg_similarity = sum(r['similarity'] for r in results) / len(results)
    terms_accuracy = sum(1 for r in results if r['terms_preserved']) / len(results) * 100

    logger.info(f"\n{'=' * 80}")
    logger.info("TAMIL TRANSLATION SUMMARY:")
    logger.info(f"  Total test cases: {len(results)}")
    logger.info(f"  Average confidence: {avg_confidence:.2f}")
    logger.info(f"  Average similarity: {avg_similarity:.2%}")
    logger.info(f"  Technical terms accuracy: {terms_accuracy:.1f}%")
    logger.info("")

    return results


def generate_accuracy_report(chinese_results, malay_results, tamil_results):
    """Generate comprehensive accuracy report"""
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE TRANSLATION ACCURACY REPORT")
    logger.info("=" * 80)

    all_results = {
        'Chinese (Simplified)': chinese_results,
        'Malay': malay_results,
        'Tamil': tamil_results
    }

    for language, results in all_results.items():
        logger.info(f"\n{language}:")
        logger.info(f"  Test cases: {len(results)}")

        if results:
            avg_confidence = sum(r['confidence'] for r in results) / len(results)
            avg_similarity = sum(r['similarity'] for r in results) / len(results)
            avg_time = sum(r['processing_time_ms'] for r in results) / len(results)
            terms_accuracy = sum(1 for r in results if r['terms_preserved']) / len(results) * 100

            logger.info(f"  Average confidence: {avg_confidence:.2f}")
            logger.info(f"  Average similarity to reference: {avg_similarity:.2%}")
            logger.info(f"  Average processing time: {avg_time:.1f}ms")
            logger.info(f"  Technical terms preservation: {terms_accuracy:.1f}%")

    logger.info("\n" + "=" * 80)
    logger.info("OVERALL ASSESSMENT:")
    logger.info("=" * 80)

    total_cases = sum(len(r) for r in all_results.values())
    total_confidence = sum(
        sum(result['confidence'] for result in results)
        for results in all_results.values()
    ) / total_cases

    logger.info(f"Total test cases: {total_cases}")
    logger.info(f"Overall average confidence: {total_confidence:.2f}")

    # Quality assessment
    if total_confidence >= 0.90:
        logger.info("✅ Translation quality: EXCELLENT (≥0.90)")
    elif total_confidence >= 0.80:
        logger.info("✅ Translation quality: GOOD (0.80-0.89)")
    elif total_confidence >= 0.70:
        logger.info("⚠️  Translation quality: ACCEPTABLE (0.70-0.79)")
    else:
        logger.info("❌ Translation quality: NEEDS IMPROVEMENT (<0.70)")

    logger.info("")
    logger.info("Note: Reference translations are for comparison only.")
    logger.info("GPT-4 may produce different but equally valid translations.")
    logger.info("")


def main():
    """Run all translation accuracy tests"""
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 12 + "TRANSLATION ACCURACY TEST FOR ASIAN LANGUAGES" + " " * 21 + "║")
    logger.info("║" + " " * 24 + "Chinese | Malay | Tamil" + " " * 30 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("")

    start_time = time.time()

    # Run tests
    chinese_results = test_chinese_translation()
    malay_results = test_malay_translation()
    tamil_results = test_tamil_translation()

    # Generate report
    generate_accuracy_report(chinese_results, malay_results, tamil_results)

    total_time = time.time() - start_time

    logger.info(f"Total execution time: {total_time:.2f}s")
    logger.info("")

    # Save results to JSON
    output_file = "translation_accuracy_results.json"
    results_data = {
        'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'chinese': chinese_results,
        'malay': malay_results,
        'tamil': tamil_results,
        'total_execution_time_seconds': total_time
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Results saved to: {output_file}")
    logger.info("")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
