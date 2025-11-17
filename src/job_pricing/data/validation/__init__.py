"""
Data Validation Utilities

Provides comprehensive validation framework for data ingestion.
"""

from .base_validator import BaseValidator, ValidationResult, ValidationError
from .field_validators import (
    required_field,
    type_check,
    range_check,
    enum_check,
    unique_check,
    foreign_key_check,
)
from .mercer_validator import MercerJobLibraryValidator, MercerMarketDataValidator
from .ssg_validator import SSGJobRoleValidator, SSGTSCValidator, SSGMappingValidator
from .quality_metrics import calculate_quality_metrics, generate_quality_report

__all__ = [
    # Base classes
    "BaseValidator",
    "ValidationResult",
    "ValidationError",
    # Field validators
    "required_field",
    "type_check",
    "range_check",
    "enum_check",
    "unique_check",
    "foreign_key_check",
    # Domain validators
    "MercerJobLibraryValidator",
    "MercerMarketDataValidator",
    "SSGJobRoleValidator",
    "SSGTSCValidator",
    "SSGMappingValidator",
    # Quality metrics
    "calculate_quality_metrics",
    "generate_quality_report",
]
