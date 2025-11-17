"""
Simplified V3 Pricing Test - No OpenAI Dependencies
Tests ONLY the V3 pricing calculation and database save.
"""

import logging
from decimal import Decimal

from src.job_pricing.core.database import get_session
from src.job_pricing.models import JobPricingRequest
from src.job_pricing.services.pricing_calculation_service_v3 import PricingCalculationServiceV3
from src.job_pricing.services.salary_recommendation_service_v2 import SalaryRecommendationServiceV2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_v3_pricing_algorithm():
    """Test V3 pricing algorithm directly (no OpenAI dependencies)."""

    logger.info("=" * 80)
    logger.info("V3 PRICING ALGORITHM TEST (No OpenAI)")
    logger.info("=" * 80)

    session = get_session()

    try:
        # Step 1: Create a job pricing request
        logger.info("\n[STEP 1] Creating JobPricingRequest...")
        request = JobPricingRequest(
            job_title='Software Engineer',
            job_description='Python developer',
            location_text='Singapore',
            requested_by='test_user',
            requestor_email='test@example.com',
            status='pending',
            urgency='normal'
        )
        session.add(request)
        session.flush()
        logger.info(f"✓ Request created with ID: {request.id}")

        # Step 2: Test V3 pricing calculation directly
        logger.info("\n[STEP 2] Running V3 Pricing Calculation...")
        pricing_service = PricingCalculationServiceV3(session)
        pricing_result = pricing_service.calculate_pricing(request)

        logger.info(f"\n✓ V3 Pricing Completed!")
        logger.info(f"  Target Salary:     SGD ${pricing_result.target_salary:,.0f}")
        logger.info(f"  Recommended Range: SGD ${pricing_result.recommended_min:,.0f} - ${pricing_result.recommended_max:,.0f}")
        logger.info(f"  Confidence Score:  {pricing_result.confidence_score:.0f}/100")
        logger.info(f"  Data Sources Used: {len(pricing_result.source_contributions)}")

        logger.info(f"\n📈 Percentiles:")
        logger.info(f"  P10: ${pricing_result.p10:,.0f}")
        logger.info(f"  P25: ${pricing_result.p25:,.0f}")
        logger.info(f"  P50: ${pricing_result.p50:,.0f}")
        logger.info(f"  P75: ${pricing_result.p75:,.0f}")
        logger.info(f"  P90: ${pricing_result.p90:,.0f}")

        logger.info(f"\n📂 Data Sources:")
        for contrib in pricing_result.source_contributions:
            logger.info(f"  • {contrib.source_name:20s} | "
                       f"Weight: {contrib.weight:>6.2%} | "
                       f"Sample: {contrib.sample_size:>3d}")

        # Step 3: Test database save with fixed field mapping
        logger.info("\n[STEP 3] Testing Database Save (Field Mapping Fix)...")

        from src.job_pricing.models import (
            JobPricingResult,
            DataSourceContribution as DataSourceContributionModel
        )

        # Create JobPricingResult
        confidence_factors = {
            "data_sources": [
                {
                    "source": c.source_name,
                    "weight": float(c.weight),
                    "sample_size": int(c.sample_size),
                    "recency_days": int(c.recency_days) if c.recency_days else None,
                    "match_quality": float(c.match_quality),
                }
                for c in pricing_result.source_contributions
            ],
            "total_sample": int(sum(c.sample_size for c in pricing_result.source_contributions)),
        }

        alternative_scenarios_serializable = {}
        for scenario_name, scenario_data in pricing_result.alternative_scenarios.items():
            alternative_scenarios_serializable[scenario_name] = {
                k: float(v) if isinstance(v, Decimal) else v
                for k, v in scenario_data.items()
            }

        # Get confidence level
        score = pricing_result.confidence_score
        if score >= 75:
            confidence_level = "High"
        elif score >= 50:
            confidence_level = "Medium"
        else:
            confidence_level = "Low"

        job_result = JobPricingResult(
            request_id=request.id,
            recommended_min=pricing_result.recommended_min,
            recommended_max=pricing_result.recommended_max,
            target_salary=pricing_result.target_salary,
            p10=pricing_result.p10,
            p25=pricing_result.p25,
            p50=pricing_result.p50,
            p75=pricing_result.p75,
            p90=pricing_result.p90,
            confidence_score=Decimal(str(pricing_result.confidence_score)),
            confidence_level=confidence_level,
            confidence_factors=confidence_factors,
            summary_text=pricing_result.explanation,
            alternative_scenarios=alternative_scenarios_serializable,
            total_data_points=int(sum(c.sample_size for c in pricing_result.source_contributions)),
            data_sources_used=len(pricing_result.source_contributions),
        )

        session.add(job_result)
        session.flush()
        logger.info(f"✓ JobPricingResult saved with ID: {job_result.id}")

        # Step 4: Test DataSourceContribution save with FIXED field mapping
        logger.info("\n[STEP 4] Saving DataSourceContributions (FIXED MAPPING)...")

        for contrib in pricing_result.source_contributions:
            logger.info(f"\n  Saving contribution for: {contrib.source_name}")
            logger.info(f"    weight_applied:  {contrib.weight}")
            logger.info(f"    sample_size:     {contrib.sample_size}")
            logger.info(f"    quality_score:   {contrib.match_quality}")
            logger.info(f"    recency_days:    {contrib.recency_days}")

            # THIS IS THE FIXED MAPPING!
            source_contrib = DataSourceContributionModel(
                result_id=job_result.id,
                source_name=contrib.source_name,
                weight_applied=Decimal(str(contrib.weight)),  # FIXED: was 'weight'
                sample_size=contrib.sample_size,
                quality_score=Decimal(str(contrib.match_quality)),  # FIXED: was 'match_quality_score'
                recency_weight=Decimal(str(1.0 - (contrib.recency_days / 365.0))) if contrib.recency_days else None,  # FIXED: was 'data_recency_days'
            )
            session.add(source_contrib)

        session.commit()
        logger.info("\n✓ All DataSourceContributions saved successfully!")

        # Step 5: Verify everything was saved
        logger.info("\n[STEP 5] Verifying Database Records...")

        saved_request = session.query(JobPricingRequest).filter_by(id=request.id).first()
        assert saved_request is not None
        logger.info(f"✓ JobPricingRequest verified (ID: {saved_request.id})")

        saved_result = session.query(JobPricingResult).filter_by(id=job_result.id).first()
        assert saved_result is not None
        logger.info(f"✓ JobPricingResult verified (ID: {saved_result.id})")

        contributions = session.query(DataSourceContributionModel).filter_by(result_id=job_result.id).all()
        assert len(contributions) > 0
        logger.info(f"✓ {len(contributions)} DataSourceContribution records verified")

        for contrib in contributions:
            logger.info(f"  • {contrib.source_name:20s} | "
                       f"weight_applied={contrib.weight_applied}, "
                       f"sample={contrib.sample_size}, "
                       f"quality={contrib.quality_score}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("=" * 80)
        logger.info("\n🎉 V3 ALGORITHM + DATABASE FIELD MAPPING = 100% WORKING! 🎉\n")

        return pricing_result

    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error("❌ TEST FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {e}", exc_info=True)
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    test_v3_pricing_algorithm()
