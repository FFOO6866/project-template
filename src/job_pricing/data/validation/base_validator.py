"""
Base Validator

Provides foundational validation framework for data ingestion.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """
    Represents a single validation error.

    Attributes:
        field: Field name that failed validation
        error_type: Type of validation error (e.g., 'required', 'type', 'range')
        message: Human-readable error message
        value: The value that failed validation
        record_id: Identifier for the record (e.g., job_code)
    """
    field: str
    error_type: str
    message: str
    value: Any
    record_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/reporting."""
        return {
            "field": self.field,
            "error_type": self.error_type,
            "message": self.message,
            "value": str(self.value) if self.value is not None else None,
            "record_id": self.record_id,
        }


@dataclass
class ValidationResult:
    """
    Results from validation run.

    Attributes:
        is_valid: True if all validations passed
        errors: List of validation errors
        warnings: List of validation warnings (non-fatal)
        record_id: Identifier for the validated record
        validation_timestamp: When validation was performed
        validator_name: Name of validator that ran
    """
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    record_id: Optional[str] = None
    validation_timestamp: datetime = field(default_factory=datetime.now)
    validator_name: str = "BaseValidator"

    def add_error(self, error: ValidationError):
        """Add an error and mark result as invalid."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: ValidationError):
        """Add a warning (doesn't invalidate result)."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/reporting."""
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "record_id": self.record_id,
            "validation_timestamp": self.validation_timestamp.isoformat(),
            "validator_name": self.validator_name,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        if self.is_valid:
            status = "✓ VALID"
        else:
            status = f"✗ INVALID ({len(self.errors)} errors)"

        if self.warnings:
            status += f", {len(self.warnings)} warnings"

        if self.record_id:
            status += f" - Record: {self.record_id}"

        return status


class BaseValidator:
    """
    Base class for data validators.

    Provides common validation framework with extensible rule system.
    Subclasses should override validation rules for specific data types.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Initialize validator.

        Args:
            name: Optional name for this validator instance
        """
        self.name = name or self.__class__.__name__
        self.validation_rules: List[Callable] = []

    def validate(self, data: Dict[str, Any], record_id: Optional[str] = None) -> ValidationResult:
        """
        Validate a single record.

        Args:
            data: Dictionary of field values to validate
            record_id: Optional identifier for the record

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(
            is_valid=True,
            record_id=record_id,
            validator_name=self.name
        )

        # Run all validation rules
        for rule in self.validation_rules:
            try:
                rule_result = rule(data, record_id)

                if rule_result:
                    if isinstance(rule_result, ValidationError):
                        result.add_error(rule_result)
                    elif isinstance(rule_result, list):
                        for error in rule_result:
                            if isinstance(error, ValidationError):
                                result.add_error(error)

            except Exception as e:
                logger.error(f"Validation rule failed: {rule.__name__}: {e}")
                result.add_error(ValidationError(
                    field="__system__",
                    error_type="rule_exception",
                    message=f"Validation rule {rule.__name__} raised exception: {e}",
                    value=None,
                    record_id=record_id
                ))

        return result

    def validate_batch(
        self,
        data_list: List[Dict[str, Any]],
        record_id_field: Optional[str] = None
    ) -> List[ValidationResult]:
        """
        Validate multiple records.

        Args:
            data_list: List of records to validate
            record_id_field: Field name to use as record identifier

        Returns:
            List of ValidationResult objects
        """
        results = []

        for i, data in enumerate(data_list):
            record_id = data.get(record_id_field) if record_id_field else f"Record {i+1}"
            result = self.validate(data, record_id)
            results.append(result)

        return results

    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Generate summary statistics from validation results.

        Args:
            results: List of validation results to summarize

        Returns:
            Dictionary with summary statistics
        """
        total_records = len(results)
        valid_records = sum(1 for r in results if r.is_valid)
        invalid_records = total_records - valid_records

        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)

        # Group errors by type
        error_types = {}
        for result in results:
            for error in result.errors:
                error_types[error.error_type] = error_types.get(error.error_type, 0) + 1

        # Group errors by field
        error_fields = {}
        for result in results:
            for error in result.errors:
                error_fields[error.field] = error_fields.get(error.field, 0) + 1

        return {
            "total_records": total_records,
            "valid_records": valid_records,
            "invalid_records": invalid_records,
            "validation_rate": (valid_records / total_records * 100) if total_records > 0 else 0,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "avg_errors_per_record": total_errors / total_records if total_records > 0 else 0,
            "error_types": error_types,
            "error_fields": error_fields,
            "most_common_error_type": max(error_types, key=error_types.get) if error_types else None,
            "most_problematic_field": max(error_fields, key=error_fields.get) if error_fields else None,
        }

    def add_rule(self, rule: Callable[[Dict[str, Any], Optional[str]], Optional[ValidationError]]):
        """
        Add a validation rule to this validator.

        Args:
            rule: Callable that takes (data, record_id) and returns ValidationError or None
        """
        self.validation_rules.append(rule)

    def remove_rule(self, rule: Callable):
        """
        Remove a validation rule from this validator.

        Args:
            rule: Rule function to remove
        """
        if rule in self.validation_rules:
            self.validation_rules.remove(rule)


def create_validation_rule(
    field: str,
    error_type: str,
    condition: Callable[[Any], bool],
    message_template: str
) -> Callable:
    """
    Factory function to create validation rules.

    Args:
        field: Field name to validate
        error_type: Type of validation (e.g., 'required', 'range')
        condition: Function that returns True if validation passes
        message_template: Error message template (can use {field}, {value})

    Returns:
        Validation rule function

    Example:
        >>> rule = create_validation_rule(
        ...     field="age",
        ...     error_type="range",
        ...     condition=lambda v: 0 <= v <= 120,
        ...     message_template="Age {value} is outside valid range [0, 120]"
        ... )
    """
    def validation_rule(data: Dict[str, Any], record_id: Optional[str] = None) -> Optional[ValidationError]:
        value = data.get(field)

        if not condition(value):
            message = message_template.format(field=field, value=value)
            return ValidationError(
                field=field,
                error_type=error_type,
                message=message,
                value=value,
                record_id=record_id
            )

        return None

    # Set function name for better debugging
    validation_rule.__name__ = f"validate_{field}_{error_type}"

    return validation_rule
