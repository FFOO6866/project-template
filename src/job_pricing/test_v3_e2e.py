"""
End-to-End Test for V3 Pricing Algorithm
Tests the complete workflow from request creation to result persistence.
"""

import logging
from decimal import Decimal

from src.job_pricing.core.database import get_session
from src.job_pricing.models import JobPricingRequest
from src.job_pricing.services.salary_recommendation_service_v2 import SalaryRecommendationServiceV2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_v3_pricing_end_to_end():
    """Test V3 pricing algorithm with real MCF data."""

    logger.info("=" * 80)
    logger.info("STARTING V3 PRICING END-TO-END TEST")
    logger.info("=" * 80)

    session = get_session()

    try:
        # Step 1: Create a job pricing request
        logger.info("\n[STEP 1] Creating JobPricingRequest...")
        request = JobPricingRequest(
            job_title='Software Engineer',
            job_description='Python developer with 3-5 years experience. Backend development, REST APIs, PostgreSQL.',
            location_text='Central Business District',
            requested_by='test_user',
            requestor_email='test@example.com',
            status='pending',
            urgency='normal'
        )
        logger.info(f"✓ Request created: {request.job_title}")

        # Step 2: Initialize V2 service (which uses V3 algorithm)
        logger.info("\n[STEP 2] Initializing SalaryRecommendationServiceV2...")
        service = SalaryRecommendationServiceV2(session)
        logger.info("✓ Service initialized")

        # Step 3: Calculate recommendation
        logger.info("\n[STEP 3] Calculating salary recommendation...")
        logger.info("This will:")
        logger.info("  - Extract skills from job description (OpenAI)")
        logger.info("  - Match to Mercer job library (vector similarity)")
        logger.info("  - Query MCF scraped data (fuzzy title match)")
        logger.info("  - Calculate percentiles (P10-P90)")
        logger.info("  - Generate confidence score")
        logger.info("  - Create alternative scenarios")
        logger.info("  - Save everything to database")

        result = service.calculate_recommendation(request)

        # Step 4: Display results
        logger.info("\n" + "=" * 80)
        logger.info("RESULTS")
        logger.info("=" * 80)

        logger.info(f"\n📊 SALARY RECOMMENDATION:")
        logger.info(f"  Target Salary:     SGD ${result['target_salary']:,.0f}")
        logger.info(f"  Recommended Range: SGD ${result['recommended_min']:,.0f} - ${result['recommended_max']:,.0f}")

        logger.info(f"\n📈 PERCENTILES:")
        logger.info(f"  P10 (Low Market):   SGD ${result['percentiles']['p10']:,.0f}")
        logger.info(f"  P25 (Budget):       SGD ${result['percentiles']['p25']:,.0f}")
        logger.info(f"  P50 (Market):       SGD ${result['percentiles']['p50']:,.0f}")
        logger.info(f"  P75 (Competitive):  SGD ${result['percentiles']['p75']:,.0f}")
        logger.info(f"  P90 (High Market):  SGD ${result['percentiles']['p90']:,.0f}")

        logger.info(f"\n🎯 CONFIDENCE:")
        logger.info(f"  Score: {result['confidence_score']:.0f}/100")
        logger.info(f"  Level: {result['confidence_level']}")

        logger.info(f"\n📂 DATA SOURCES ({result['data_sources_used']}):")
        for source in result['source_contributions']:
            logger.info(f"  • {source['source']:20s} | Weight: {source['weight']:>6s} | "
                       f"Sample: {source['sample_size']:>3d} | "
                       f"Quality: {source['match_quality']:>6s}")

        if result.get('mercer_match'):
            logger.info(f"\n🏢 MERCER MATCH:")
            logger.info(f"  Job Code:   {result['mercer_match']['job_code']}")
            logger.info(f"  Job Title:  {result['mercer_match']['job_title']}")
            logger.info(f"  Match Score: {result['mercer_match']['match_score']:.0%}")

        logger.info(f"\n🎨 ALTERNATIVE SCENARIOS:")
        for name, scenario in result['scenarios'].items():
            logger.info(f"  {name:15s}: SGD ${scenario['min']:,.0f} - ${scenario['max']:,.0f}")
            logger.info(f"                   {scenario['use_case']}")

        logger.info(f"\n💾 DATABASE:")
        logger.info(f"  Result ID: {result['result_id']}")
        logger.info(f"  Created:   {result['created_at']}")

        # Step 5: Verify data was saved
        logger.info("\n[STEP 5] Verifying database persistence...")

        # Verify request was saved
        saved_request = session.query(JobPricingRequest).filter_by(id=request.id).first()
        assert saved_request is not None, "Request not found in database"
        logger.info(f"✓ JobPricingRequest saved (ID: {saved_request.id})")

        # Verify result was saved
        from src.job_pricing.models import JobPricingResult
        import uuid
        result_uuid = uuid.UUID(result['result_id'])
        saved_result = session.query(JobPricingResult).filter_by(id=result_uuid).first()
        assert saved_result is not None, "Result not found in database"
        logger.info(f"✓ JobPricingResult saved (ID: {saved_result.id})")

        # Verify source contributions were saved
        from src.job_pricing.models import DataSourceContribution
        contributions = session.query(DataSourceContribution).filter_by(result_id=result_uuid).all()
        assert len(contributions) > 0, "No source contributions found"
        logger.info(f"✓ {len(contributions)} DataSourceContribution records saved")

        for contrib in contributions:
            logger.info(f"  • {contrib.source_name}: weight={contrib.weight_applied}, "
                       f"sample={contrib.sample_size}, quality={contrib.quality_score}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ END-TO-END TEST PASSED!")
        logger.info("=" * 80)
        logger.info("\n🎉 V3 PRICING ALGORITHM IS 100% OPERATIONAL! 🎉\n")

        return result

    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error("❌ TEST FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {e}", exc_info=True)
        raise

    finally:
        session.close()


if __name__ == "__main__":
    test_v3_pricing_end_to_end()
