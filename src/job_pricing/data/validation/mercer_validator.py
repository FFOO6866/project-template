"""
Mercer Data Validators

Domain-specific validators for Mercer Job Library and Market Data.
"""

from typing import Optional, Set
from .base_validator import BaseValidator, ValidationError
from .field_validators import (
    required_field,
    type_check,
    range_check,
    enum_check,
    string_length_check,
    pattern_check,
    foreign_key_check,
)


# Mercer Career Levels
MERCER_CAREER_LEVELS = [
    # Management Track
    "M1", "M2", "M3", "M4", "M5", "M6",
    # Professional Track
    "P1", "P2", "P3", "P4", "P5", "P6",
    # Executive Track
    "E1", "E2", "E3", "E4", "E5"
]

# Mercer Benchmark Cuts
MERCER_BENCHMARK_CUTS = [
    "P10", "P25", "P50", "P75", "P90",
    "MIN", "MAX", "AVG"
]

# Common currencies
CURRENCIES = [
    "SGD", "USD", "EUR", "GBP", "JPY", "CNY", "AUD", "HKD", "MYR", "INR"
]


class MercerJobLibraryValidator(BaseValidator):
    """
    Validator for Mercer Job Library records.

    Validates:
    - Required fields
    - Job code format
    - Career level values
    - IPE value logic (min < mid < max)
    - String lengths
    - Data types
    """

    def __init__(self, existing_job_codes: Optional[Set[str]] = None):
        """
        Initialize Mercer Job Library validator.

        Args:
            existing_job_codes: Set of job codes that already exist (for duplicate detection)
        """
        super().__init__("MercerJobLibraryValidator")

        # Required fields
        self.add_rule(required_field("job_code"))
        self.add_rule(required_field("job_title"))
        self.add_rule(required_field("family"))
        self.add_rule(required_field("career_level"))
        self.add_rule(required_field("job_description"))

        # Job code format: XXX.XX.XXX.XXX (e.g., "ICT.02.003.M40")
        # Pattern: 3 letters, dot, 2 digits, dot, 3 digits, dot, alphanumeric
        self.add_rule(pattern_check(
            "job_code",
            r"^[A-Z]{3}\.\d{2}\.\d{3}\.[A-Z0-9]{2,4}$",
            allow_none=False
        ))

        # Career level must be valid
        self.add_rule(enum_check("career_level", MERCER_CAREER_LEVELS))

        # String length constraints
        self.add_rule(string_length_check("job_title", min_length=3, max_length=200))
        self.add_rule(string_length_check("family", min_length=2, max_length=100))
        self.add_rule(string_length_check("job_description", min_length=10, max_length=10000))

        # Type checks
        self.add_rule(type_check("ipe_minimum", (int, float), allow_none=True))
        self.add_rule(type_check("ipe_midpoint", (int, float), allow_none=True))
        self.add_rule(type_check("ipe_maximum", (int, float), allow_none=True))

        # IPE values should be positive
        self.add_rule(range_check("ipe_minimum", min_value=0, allow_none=True))
        self.add_rule(range_check("ipe_midpoint", min_value=0, allow_none=True))
        self.add_rule(range_check("ipe_maximum", min_value=0, allow_none=True))

        # IPE logic: min < mid < max
        self.add_rule(self._validate_ipe_logic)

        # Uniqueness check if existing codes provided
        if existing_job_codes:
            from .field_validators import unique_check
            self.add_rule(unique_check("job_code", existing_job_codes))

    @staticmethod
    def _validate_ipe_logic(data: dict, record_id: Optional[str] = None) -> Optional[ValidationError]:
        """
        Validate IPE value logic: minimum < midpoint < maximum.

        Args:
            data: Record data
            record_id: Record identifier

        Returns:
            ValidationError if logic is invalid, None otherwise
        """
        ipe_min = data.get("ipe_minimum")
        ipe_mid = data.get("ipe_midpoint")
        ipe_max = data.get("ipe_maximum")

        # Skip validation if any value is None
        if ipe_min is None or ipe_mid is None or ipe_max is None:
            return None

        # Check: min < mid < max
        if not (ipe_min < ipe_mid < ipe_max):
            return ValidationError(
                field="ipe_values",
                error_type="logic_error",
                message=f"IPE values must satisfy: minimum ({ipe_min}) < midpoint ({ipe_mid}) < maximum ({ipe_max})",
                value={"min": ipe_min, "mid": ipe_mid, "max": ipe_max},
                record_id=record_id
            )

        return None


class MercerMarketDataValidator(BaseValidator):
    """
    Validator for Mercer Market Data records.

    Validates:
    - Required fields
    - Foreign key to job library
    - Benchmark cut values
    - Salary ranges
    - Currency codes
    - Date formats
    """

    def __init__(self, valid_job_codes: Optional[Set[str]] = None):
        """
        Initialize Mercer Market Data validator.

        Args:
            valid_job_codes: Set of valid job codes from Mercer Job Library
        """
        super().__init__("MercerMarketDataValidator")

        # Required fields
        self.add_rule(required_field("job_code"))
        self.add_rule(required_field("country_code"))
        self.add_rule(required_field("benchmark_cut"))
        self.add_rule(required_field("base_salary"))
        self.add_rule(required_field("currency"))

        # Foreign key check if valid codes provided
        if valid_job_codes:
            self.add_rule(foreign_key_check(
                "job_code",
                valid_job_codes,
                "mercer_job_library"
            ))

        # Benchmark cut must be valid
        self.add_rule(enum_check("benchmark_cut", MERCER_BENCHMARK_CUTS))

        # Currency must be valid
        self.add_rule(enum_check("currency", CURRENCIES))

        # Country code format (ISO 3166-1 alpha-2)
        self.add_rule(pattern_check(
            "country_code",
            r"^[A-Z]{2}$",
            allow_none=False
        ))

        # Salary values must be positive
        self.add_rule(type_check("base_salary", (int, float)))
        self.add_rule(range_check("base_salary", min_value=0))

        self.add_rule(type_check("total_cash", (int, float), allow_none=True))
        self.add_rule(range_check("total_cash", min_value=0, allow_none=True))

        # String length constraints
        self.add_rule(string_length_check("location", min_length=2, max_length=100, allow_none=True))
        self.add_rule(string_length_check("industry", min_length=2, max_length=100, allow_none=True))

        # Salary logic: base_salary <= total_cash (if both present)
        self.add_rule(self._validate_salary_logic)

    @staticmethod
    def _validate_salary_logic(data: dict, record_id: Optional[str] = None) -> Optional[ValidationError]:
        """
        Validate salary logic: base_salary <= total_cash.

        Args:
            data: Record data
            record_id: Record identifier

        Returns:
            ValidationError if logic is invalid, None otherwise
        """
        base_salary = data.get("base_salary")
        total_cash = data.get("total_cash")

        # Skip if total_cash is not provided
        if total_cash is None:
            return None

        # Check: base_salary <= total_cash
        if base_salary > total_cash:
            return ValidationError(
                field="salary_values",
                error_type="logic_error",
                message=f"Base salary ({base_salary}) cannot exceed total cash ({total_cash})",
                value={"base_salary": base_salary, "total_cash": total_cash},
                record_id=record_id
            )

        return None


class MercerJobMappingValidator(BaseValidator):
    """
    Validator for Mercer Job Mappings (AI-generated job matches).

    Validates:
    - Required fields
    - Foreign key references
    - Confidence scores
    - Match types
    """

    def __init__(
        self,
        valid_request_ids: Optional[Set[str]] = None,
        valid_job_codes: Optional[Set[str]] = None
    ):
        """
        Initialize Mercer Job Mapping validator.

        Args:
            valid_request_ids: Set of valid job pricing request IDs
            valid_job_codes: Set of valid Mercer job codes
        """
        super().__init__("MercerJobMappingValidator")

        # Required fields
        self.add_rule(required_field("request_id"))
        self.add_rule(required_field("mercer_job_code"))
        self.add_rule(required_field("confidence_score"))
        self.add_rule(required_field("match_type"))

        # Foreign key checks
        if valid_request_ids:
            self.add_rule(foreign_key_check(
                "request_id",
                valid_request_ids,
                "job_pricing_requests"
            ))

        if valid_job_codes:
            self.add_rule(foreign_key_check(
                "mercer_job_code",
                valid_job_codes,
                "mercer_job_library"
            ))

        # Confidence score must be between 0 and 1
        self.add_rule(type_check("confidence_score", float))
        self.add_rule(range_check("confidence_score", min_value=0.0, max_value=1.0))

        # Match type must be valid
        self.add_rule(enum_check("match_type", [
            "exact", "high_confidence", "medium_confidence",
            "low_confidence", "manual", "fallback"
        ]))


def validate_mercer_job_batch(
    jobs: list,
    existing_job_codes: Optional[Set[str]] = None
) -> dict:
    """
    Validate a batch of Mercer jobs and return summary.

    Args:
        jobs: List of job dictionaries to validate
        existing_job_codes: Set of existing job codes for duplicate detection

    Returns:
        Dictionary with validation summary

    Example:
        >>> jobs = [
        ...     {"job_code": "ICT.01.001.M40", "job_title": "Software Engineer", ...},
        ...     {"job_code": "ICT.01.002.P30", "job_title": "Data Analyst", ...}
        ... ]
        >>> summary = validate_mercer_job_batch(jobs)
        >>> print(f"Valid: {summary['valid_count']}/{summary['total_count']}")
    """
    validator = MercerJobLibraryValidator(existing_job_codes)

    results = validator.validate_batch(
        jobs,
        record_id_field="job_code"
    )

    summary = validator.get_validation_summary(results)

    return summary


def validate_mercer_market_data_batch(
    market_data: list,
    valid_job_codes: Optional[Set[str]] = None
) -> dict:
    """
    Validate a batch of Mercer market data and return summary.

    Args:
        market_data: List of market data dictionaries to validate
        valid_job_codes: Set of valid job codes from job library

    Returns:
        Dictionary with validation summary

    Example:
        >>> data = [
        ...     {"job_code": "ICT.01.001.M40", "benchmark_cut": "P50", ...},
        ...     {"job_code": "ICT.01.002.P30", "benchmark_cut": "P75", ...}
        ... ]
        >>> summary = validate_mercer_market_data_batch(data, valid_job_codes)
        >>> print(f"Errors: {summary['total_errors']}")
    """
    validator = MercerMarketDataValidator(valid_job_codes)

    results = validator.validate_batch(
        market_data,
        record_id_field="job_code"
    )

    summary = validator.get_validation_summary(results)

    return summary
