"""
V3 Multi-Source Pricing Test
Tests V3 pricing with both Mercer and MCF data sources.
"""

import logging
from decimal import Decimal

from src.job_pricing.core.database import get_session
from src.job_pricing.models import JobPricingRequest
from src.job_pricing.services.pricing_calculation_service_v3 import PricingCalculationServiceV3

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_multi_source_pricing():
    """Test V3 pricing with Mercer + MCF data sources."""

    logger.info("=" * 80)
    logger.info("V3 MULTI-SOURCE PRICING TEST (Mercer + MCF)")
    logger.info("=" * 80)

    session = get_session()

    try:
        # Create request
        logger.info("\n[STEP 1] Creating JobPricingRequest...")
        request = JobPricingRequest(
            job_title='Software Engineer',
            job_description='Python developer with 3-5 years experience',
            location_text='Singapore',
            requested_by='test_user',
            requestor_email='test@example.com',
            status='pending',
            urgency='normal'
        )
        session.add(request)
        session.flush()
        logger.info(f"Request created: {request.job_title}")

        # Run V3 pricing
        logger.info("\n[STEP 2] Running V3 Pricing with Multi-Source Aggregation...")
        logger.info("Expected sources:")
        logger.info("  - Mercer (40% weight, 37 market data records)")
        logger.info("  - MCF (25% weight, 105 scraped jobs)")
        logger.info("")

        pricing_service = PricingCalculationServiceV3(session)
        pricing_result = pricing_service.calculate_pricing(request)

        # Display results
        logger.info("\n" + "=" * 80)
        logger.info("RESULTS")
        logger.info("=" * 80)

        logger.info(f"\nSALARY RECOMMENDATION:")
        logger.info(f"  Target:     SGD ${pricing_result.target_salary:,.0f}")
        logger.info(f"  Range:      SGD ${pricing_result.recommended_min:,.0f} - ${pricing_result.recommended_max:,.0f}")
        logger.info(f"  Confidence: {pricing_result.confidence_score:.0f}/100")

        logger.info(f"\nPERCENTILES:")
        logger.info(f"  P10: ${pricing_result.p10:,.0f}")
        logger.info(f"  P25: ${pricing_result.p25:,.0f}")
        logger.info(f"  P50: ${pricing_result.p50:,.0f}")
        logger.info(f"  P75: ${pricing_result.p75:,.0f}")
        logger.info(f"  P90: ${pricing_result.p90:,.0f}")

        logger.info(f"\nDATA SOURCES ({len(pricing_result.source_contributions)}):")
        for contrib in pricing_result.source_contributions:
            logger.info(f"  {contrib.source_name:20s} | "
                       f"Weight: {contrib.weight:>6.2%} | "
                       f"Sample: {contrib.sample_size:>3d} | "
                       f"Age: {contrib.recency_days:>3d} days | "
                       f"Quality: {contrib.match_quality:>6.2%}")

        logger.info(f"\nALTERNATIVE SCENARIOS:")
        for name, scenario in pricing_result.alternative_scenarios.items():
            logger.info(f"  {name:15s}: ${scenario['min']:,.0f} - ${scenario['max']:,.0f}")

        # Analyze data source coverage
        logger.info("\n" + "=" * 80)
        logger.info("DATA SOURCE ANALYSIS")
        logger.info("=" * 80)

        sources_found = {c.source_name for c in pricing_result.source_contributions}
        expected_sources = {"mercer", "my_careers_future"}

        if "mercer" in sources_found:
            logger.info("MERCER DATA: Found")
            mercer = [c for c in pricing_result.source_contributions if c.source_name == "mercer"][0]
            logger.info(f"  - Sample size: {mercer.sample_size}")
            logger.info(f"  - Survey age: {mercer.recency_days} days")
            logger.info(f"  - Match quality: {mercer.match_quality:.2%}")
            logger.info(f"  - P50: ${mercer.p50:,.0f}")
        else:
            logger.warning("MERCER DATA: Not found (likely no match for this job)")

        if "my_careers_future" in sources_found:
            logger.info("\nMCF DATA: Found")
            mcf = [c for c in pricing_result.source_contributions if c.source_name == "my_careers_future"][0]
            logger.info(f"  - Jobs found: {mcf.sample_size}")
            logger.info(f"  - Data age: {mcf.recency_days} days")
            logger.info(f"  - Match quality: {mcf.match_quality:.2%}")
        else:
            logger.warning("\nMCF DATA: Not found")

        # Calculate coverage
        total_weight = sum(c.weight for c in pricing_result.source_contributions)
        logger.info(f"\nTOTAL DATA COVERAGE: {total_weight:.0%}")

        if total_weight >= 0.65:  # 65%+ coverage (Mercer + MCF)
            logger.info("STATUS: EXCELLENT (Multi-source data)")
        elif total_weight >= 0.25:  # 25%+ coverage (MCF only)
            logger.info("STATUS: GOOD (Single source)")
        else:
            logger.info("STATUS: LIMITED (Insufficient data)")

        logger.info("\n" + "=" * 80)
        logger.info("TEST PASSED")
        logger.info("=" * 80)

        return pricing_result

    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error("TEST FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {e}", exc_info=True)
        raise

    finally:
        session.close()


if __name__ == "__main__":
    test_multi_source_pricing()
