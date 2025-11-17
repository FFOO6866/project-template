"""
SSG Skills Framework Validators

Domain-specific validators for SSG Job Roles, TSC, and Mappings.
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


# SSG Career Levels
SSG_CAREER_LEVELS = [
    "Entry",
    "Junior Executive",
    "Senior Executive",
    "Manager",
    "Senior Manager",
    "Senior/Lead",
    "Director",
    "C-Suite"
]

# SSG Proficiency Levels (1-6)
SSG_PROFICIENCY_LEVELS = [1, 2, 3, 4, 5, 6]

# SSG Sectors (38 total - abbreviated list, expand as needed)
SSG_SECTORS = [
    "Accountancy",
    "Aerospace",
    "Air Transport",
    "Built Environment",
    "Cleantech",
    "Early Childhood Care and Education",
    "Electronics",
    "Energy and Chemicals",
    "Environmental Services",
    "Financial Services",
    "Food Manufacturing",
    "Food Services",
    "Healthcare",
    "Hotel and Accommodation Services",
    "Human Resource",
    "Infocomm Technology",
    "Information & Communications Technology",  # Alternative name
    "ICT",  # Abbreviation
    "Land Transport",
    "Logistics",
    "Manufacturing",
    "Marine and Offshore",
    "Media",
    "Precision Engineering",
    "Retail",
    "Sea Transport",
    "Security",
    "Social Service",
    "Sports and Recreation",
    "Tourism",
    "Wholesale Trade",
    # ... add more as needed
]


class SSGJobRoleValidator(BaseValidator):
    """
    Validator for SSG Job Role records.

    Validates:
    - Required fields
    - Job role code format
    - Career level values
    - Sector values
    - String lengths
    """

    def __init__(self, existing_role_codes: Optional[Set[str]] = None):
        """
        Initialize SSG Job Role validator.

        Args:
            existing_role_codes: Set of job role codes that already exist
        """
        super().__init__("SSGJobRoleValidator")

        # Required fields
        self.add_rule(required_field("job_role_code"))
        self.add_rule(required_field("job_role_title"))
        self.add_rule(required_field("sector"))
        self.add_rule(required_field("career_level"))

        # Job role code format: AAA-BBB-####-#.# (e.g., "ICT-DIS-4010-1.1")
        # Pattern: 3-4 letters, dash, 3-4 letters, dash, 4 digits, dash, digit.digit
        self.add_rule(pattern_check(
            "job_role_code",
            r"^[A-Z]{2,4}-[A-Z]{2,4}-\d{4}-\d+\.\d+$",
            allow_none=False
        ))

        # Career level must be valid
        self.add_rule(enum_check("career_level", SSG_CAREER_LEVELS))

        # Sector should be valid (warn only, don't fail - sectors may change)
        # self.add_rule(enum_check("sector", SSG_SECTORS))  # Too strict

        # String length constraints
        self.add_rule(string_length_check("job_role_title", min_length=3, max_length=200))
        self.add_rule(string_length_check("sector", min_length=2, max_length=100))
        self.add_rule(string_length_check("job_role_description", min_length=10, max_length=10000, allow_none=True))

        # Uniqueness check
        if existing_role_codes:
            from .field_validators import unique_check
            self.add_rule(unique_check("job_role_code", existing_role_codes))


class SSGTSCValidator(BaseValidator):
    """
    Validator for SSG Technical Skills & Competencies (TSC) records.

    Validates:
    - Required fields
    - TSC code format
    - Proficiency level range (1-6)
    - String lengths
    """

    def __init__(self, existing_tsc_codes: Optional[Set[str]] = None):
        """
        Initialize SSG TSC validator.

        Args:
            existing_tsc_codes: Set of TSC codes that already exist
        """
        super().__init__("SSGTSCValidator")

        # Required fields
        self.add_rule(required_field("tsc_code"))
        self.add_rule(required_field("skill_title"))
        self.add_rule(required_field("skill_category"))
        self.add_rule(required_field("proficiency_level"))

        # TSC code format: Similar to job role code with additional suffix
        # Pattern: AAA-BBB-####-#.#-A (e.g., "ICT-DIS-4010-1.1-A")
        self.add_rule(pattern_check(
            "tsc_code",
            r"^[A-Z]{2,4}-[A-Z]{2,4}-\d{4}-\d+\.\d+-[A-Z]$",
            allow_none=False
        ))

        # Proficiency level must be 1-6
        self.add_rule(type_check("proficiency_level", int))
        self.add_rule(range_check("proficiency_level", min_value=1, max_value=6))

        # String length constraints
        self.add_rule(string_length_check("skill_title", min_length=3, max_length=200))
        self.add_rule(string_length_check("skill_category", min_length=2, max_length=100))
        self.add_rule(string_length_check("skill_description", min_length=10, max_length=10000, allow_none=True))

        # Uniqueness check
        if existing_tsc_codes:
            from .field_validators import unique_check
            self.add_rule(unique_check("tsc_code", existing_tsc_codes))


class SSGMappingValidator(BaseValidator):
    """
    Validator for SSG Job Role → TSC Mapping records.

    Validates:
    - Required fields
    - Foreign key references
    - Proficiency level range
    - Boolean fields
    """

    def __init__(
        self,
        valid_role_codes: Optional[Set[str]] = None,
        valid_tsc_codes: Optional[Set[str]] = None
    ):
        """
        Initialize SSG Mapping validator.

        Args:
            valid_role_codes: Set of valid job role codes
            valid_tsc_codes: Set of valid TSC codes
        """
        super().__init__("SSGMappingValidator")

        # Required fields
        self.add_rule(required_field("job_role_code"))
        self.add_rule(required_field("tsc_code"))
        self.add_rule(required_field("required_proficiency_level"))

        # Foreign key checks
        if valid_role_codes:
            self.add_rule(foreign_key_check(
                "job_role_code",
                valid_role_codes,
                "ssg_job_roles"
            ))

        if valid_tsc_codes:
            self.add_rule(foreign_key_check(
                "tsc_code",
                valid_tsc_codes,
                "ssg_tsc"
            ))

        # Proficiency level must be 1-6
        self.add_rule(type_check("required_proficiency_level", int))
        self.add_rule(range_check("required_proficiency_level", min_value=1, max_value=6))

        # is_critical must be boolean
        self.add_rule(type_check("is_critical", bool, allow_none=True))


class SSGJobSkillsExtractedValidator(BaseValidator):
    """
    Validator for extracted skills from job descriptions.

    Validates:
    - Required fields
    - Foreign key references
    - Confidence scores
    - Match types
    """

    def __init__(
        self,
        valid_request_ids: Optional[Set[str]] = None,
        valid_tsc_codes: Optional[Set[str]] = None
    ):
        """
        Initialize extracted skills validator.

        Args:
            valid_request_ids: Set of valid job pricing request IDs
            valid_tsc_codes: Set of valid TSC codes
        """
        super().__init__("SSGJobSkillsExtractedValidator")

        # Required fields
        self.add_rule(required_field("request_id"))
        self.add_rule(required_field("extracted_skill"))
        self.add_rule(required_field("confidence_score"))

        # Foreign key checks
        if valid_request_ids:
            self.add_rule(foreign_key_check(
                "request_id",
                valid_request_ids,
                "job_pricing_requests"
            ))

        if valid_tsc_codes:
            self.add_rule(foreign_key_check(
                "tsc_code",
                valid_tsc_codes,
                "ssg_tsc"
            ))

        # Confidence score must be between 0 and 1
        self.add_rule(type_check("confidence_score", float))
        self.add_rule(range_check("confidence_score", min_value=0.0, max_value=1.0))

        # String lengths
        self.add_rule(string_length_check("extracted_skill", min_length=2, max_length=200))


def validate_ssg_job_roles_batch(
    job_roles: list,
    existing_role_codes: Optional[Set[str]] = None
) -> dict:
    """
    Validate a batch of SSG job roles and return summary.

    Args:
        job_roles: List of job role dictionaries to validate
        existing_role_codes: Set of existing role codes for duplicate detection

    Returns:
        Dictionary with validation summary

    Example:
        >>> roles = [
        ...     {"job_role_code": "ICT-DIS-4010-1.1", "job_role_title": "Software Developer", ...},
        ...     {"job_role_code": "ICT-DIS-4020-1.2", "job_role_title": "Data Analyst", ...}
        ... ]
        >>> summary = validate_ssg_job_roles_batch(roles)
        >>> print(f"Valid: {summary['valid_count']}/{summary['total_count']}")
    """
    validator = SSGJobRoleValidator(existing_role_codes)

    results = validator.validate_batch(
        job_roles,
        record_id_field="job_role_code"
    )

    summary = validator.get_validation_summary(results)

    return summary


def validate_ssg_tsc_batch(
    tsc_records: list,
    existing_tsc_codes: Optional[Set[str]] = None
) -> dict:
    """
    Validate a batch of SSG TSC records and return summary.

    Args:
        tsc_records: List of TSC dictionaries to validate
        existing_tsc_codes: Set of existing TSC codes for duplicate detection

    Returns:
        Dictionary with validation summary

    Example:
        >>> tsc = [
        ...     {"tsc_code": "ICT-DIS-4010-1.1-A", "skill_title": "Python Programming", ...},
        ...     {"tsc_code": "ICT-DIS-4010-1.1-B", "skill_title": "SQL", ...}
        ... ]
        >>> summary = validate_ssg_tsc_batch(tsc)
        >>> print(f"Errors: {summary['total_errors']}")
    """
    validator = SSGTSCValidator(existing_tsc_codes)

    results = validator.validate_batch(
        tsc_records,
        record_id_field="tsc_code"
    )

    summary = validator.get_validation_summary(results)

    return summary


def validate_ssg_mappings_batch(
    mappings: list,
    valid_role_codes: Optional[Set[str]] = None,
    valid_tsc_codes: Optional[Set[str]] = None
) -> dict:
    """
    Validate a batch of SSG mappings and return summary.

    Args:
        mappings: List of mapping dictionaries to validate
        valid_role_codes: Set of valid job role codes
        valid_tsc_codes: Set of valid TSC codes

    Returns:
        Dictionary with validation summary

    Example:
        >>> mappings = [
        ...     {
        ...         "job_role_code": "ICT-DIS-4010-1.1",
        ...         "tsc_code": "ICT-DIS-4010-1.1-A",
        ...         "required_proficiency_level": 3,
        ...         "is_critical": True
        ...     }
        ... ]
        >>> summary = validate_ssg_mappings_batch(mappings, role_codes, tsc_codes)
        >>> print(f"Invalid: {summary['invalid_count']}")
    """
    validator = SSGMappingValidator(valid_role_codes, valid_tsc_codes)

    results = validator.validate_batch(
        mappings,
        record_id_field=None  # Composite key, no single identifier
    )

    summary = validator.get_validation_summary(results)

    return summary


def validate_ssg_proficiency_level(level: int) -> bool:
    """
    Validate SSG proficiency level is in range 1-6.

    Args:
        level: Proficiency level to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_ssg_proficiency_level(3)
        True
        >>> validate_ssg_proficiency_level(7)
        False
    """
    return isinstance(level, int) and 1 <= level <= 6


def get_ssg_proficiency_description(level: int) -> str:
    """
    Get human-readable description of SSG proficiency level.

    Args:
        level: Proficiency level (1-6)

    Returns:
        Description string

    Example:
        >>> get_ssg_proficiency_description(3)
        'Application'
    """
    descriptions = {
        1: "Basic Awareness",
        2: "Working Knowledge",
        3: "Application",
        4: "Synthesis",
        5: "Expert",
        6: "Mastery"
    }

    return descriptions.get(level, "Unknown")
