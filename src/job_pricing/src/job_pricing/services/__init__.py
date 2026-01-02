"""
Business Logic Services

Service layer for complex business operations.

IMPORTANT: Use PricingCalculationServiceV3 for production pricing calculations.
The legacy PricingCalculationService (V1) is deprecated and will be removed.
"""

import warnings

from .skill_matching_service import SkillMatchingService, SkillMatch
from .skill_extraction_service import SkillExtractionService, ExtractedSkill, extract_skills_from_job
from .job_processing_service import JobProcessingService, process_job_request
from .job_matching_service import JobMatchingService

# V3 - Production-ready multi-source pricing (RECOMMENDED)
from .pricing_calculation_service_v3 import PricingCalculationServiceV3

# V1 - Legacy pricing service (DEPRECATED)
# Kept for backward compatibility only - DO NOT USE FOR NEW CODE
from .pricing_calculation_service import PricingCalculationService as _PricingCalculationServiceV1
from .pricing_calculation_service import SalaryBand, PricingFactors


class PricingCalculationService(_PricingCalculationServiceV1):
    """
    DEPRECATED: Use PricingCalculationServiceV3 instead.

    This class wrapper exists for backward compatibility only.
    V1 has hardcoded placeholders and will be removed in a future release.

    Migration:
        # Before (deprecated)
        service = PricingCalculationService(session)

        # After (recommended)
        service = PricingCalculationServiceV3(session)

    See ADR-002 for complete migration guide.
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "PricingCalculationService (V1) is deprecated. "
            "Use PricingCalculationServiceV3 for production pricing calculations. "
            "See ADR-002 for migration guide.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


__all__ = [
    # Skill services
    "SkillMatchingService",
    "SkillMatch",
    "SkillExtractionService",
    "ExtractedSkill",
    "extract_skills_from_job",
    # Job processing
    "JobProcessingService",
    "process_job_request",
    "JobMatchingService",
    # Pricing services
    "PricingCalculationServiceV3",  # RECOMMENDED
    "PricingCalculationService",     # DEPRECATED - emits warning
    "SalaryBand",
    "PricingFactors",
]
