"""
Field Validators

Common validation functions for individual fields.
Can be composed to create complex validation rules.
"""

from typing import Any, List, Optional, Set, Type, Callable
from .base_validator import ValidationError, create_validation_rule


def required_field(field: str) -> Callable:
    """
    Validate that a field is present and not None/empty.

    Args:
        field: Field name to validate

    Returns:
        Validation rule function

    Example:
        >>> validator.add_rule(required_field("job_title"))
    """
    def rule(data: dict, record_id: Optional[str] = None) -> Optional[ValidationError]:
        value = data.get(field)

        if value is None or (isinstance(value, str) and value.strip() == ""):
            return ValidationError(
                field=field,
                error_type="required",
                message=f"Required field '{field}' is missing or empty",
                value=value,
                record_id=record_id
            )

        return None

    rule.__name__ = f"required_{field}"
    return rule


def type_check(field: str, expected_type: Type, allow_none: bool = False) -> Callable:
    """
    Validate that a field has the expected type.

    Args:
        field: Field name to validate
        expected_type: Expected Python type
        allow_none: If True, None values are acceptable

    Returns:
        Validation rule function

    Example:
        >>> validator.add_rule(type_check("ipe_minimum", int))
        >>> validator.add_rule(type_check("job_description", str, allow_none=True))
    """
    def rule(data: dict, record_id: Optional[str] = None) -> Optional[ValidationError]:
        value = data.get(field)

        if value is None:
            if allow_none:
                return None
            else:
                return ValidationError(
                    field=field,
                    error_type="type",
                    message=f"Field '{field}' is None but type {expected_type.__name__} expected",
                    value=value,
                    record_id=record_id
                )

        if not isinstance(value, expected_type):
            return ValidationError(
                field=field,
                error_type="type",
                message=f"Field '{field}' has type {type(value).__name__}, expected {expected_type.__name__}",
                value=value,
                record_id=record_id
            )

        return None

    rule.__name__ = f"type_check_{field}_{expected_type.__name__}"
    return rule


def range_check(
    field: str,
    min_value: Optional[Any] = None,
    max_value: Optional[Any] = None,
    allow_none: bool = False
) -> Callable:
    """
    Validate that a numeric field is within a range.

    Args:
        field: Field name to validate
        min_value: Minimum acceptable value (inclusive)
        max_value: Maximum acceptable value (inclusive)
        allow_none: If True, None values are acceptable

    Returns:
        Validation rule function

    Example:
        >>> validator.add_rule(range_check("ipe_minimum", min_value=0, max_value=1000))
    """
    def rule(data: dict, record_id: Optional[str] = None) -> Optional[ValidationError]:
        value = data.get(field)

        if value is None:
            if allow_none:
                return None
            else:
                return ValidationError(
                    field=field,
                    error_type="range",
                    message=f"Field '{field}' is None but range check requires a value",
                    value=value,
                    record_id=record_id
                )

        if min_value is not None and value < min_value:
            return ValidationError(
                field=field,
                error_type="range",
                message=f"Field '{field}' value {value} is below minimum {min_value}",
                value=value,
                record_id=record_id
            )

        if max_value is not None and value > max_value:
            return ValidationError(
                field=field,
                error_type="range",
                message=f"Field '{field}' value {value} exceeds maximum {max_value}",
                value=value,
                record_id=record_id
            )

        return None

    rule.__name__ = f"range_check_{field}_{min_value}_{max_value}"
    return rule


def enum_check(field: str, allowed_values: List[Any], allow_none: bool = False) -> Callable:
    """
    Validate that a field value is in a set of allowed values.

    Args:
        field: Field name to validate
        allowed_values: List of acceptable values
        allow_none: If True, None values are acceptable

    Returns:
        Validation rule function

    Example:
        >>> validator.add_rule(enum_check("career_level", ["M1", "M2", "M3", "P1", "P2", "P3"]))
    """
    allowed_set = set(allowed_values)

    def rule(data: dict, record_id: Optional[str] = None) -> Optional[ValidationError]:
        value = data.get(field)

        if value is None:
            if allow_none:
                return None
            else:
                return ValidationError(
                    field=field,
                    error_type="enum",
                    message=f"Field '{field}' is None but must be one of: {allowed_values}",
                    value=value,
                    record_id=record_id
                )

        if value not in allowed_set:
            return ValidationError(
                field=field,
                error_type="enum",
                message=f"Field '{field}' value '{value}' not in allowed values: {allowed_values}",
                value=value,
                record_id=record_id
            )

        return None

    rule.__name__ = f"enum_check_{field}"
    return rule


def unique_check(field: str, existing_values: Set[Any]) -> Callable:
    """
    Validate that a field value is unique (not in existing set).

    Args:
        field: Field name to validate
        existing_values: Set of values that already exist

    Returns:
        Validation rule function

    Example:
        >>> existing_codes = {"ICT.01.001.M40", "ICT.01.002.P30"}
        >>> validator.add_rule(unique_check("job_code", existing_codes))
    """
    def rule(data: dict, record_id: Optional[str] = None) -> Optional[ValidationError]:
        value = data.get(field)

        if value in existing_values:
            return ValidationError(
                field=field,
                error_type="unique",
                message=f"Field '{field}' value '{value}' already exists (duplicate)",
                value=value,
                record_id=record_id
            )

        return None

    rule.__name__ = f"unique_check_{field}"
    return rule


def foreign_key_check(field: str, valid_keys: Set[Any], reference_table: str) -> Callable:
    """
    Validate that a foreign key field references an existing record.

    Args:
        field: Field name to validate
        valid_keys: Set of valid foreign key values
        reference_table: Name of referenced table (for error message)

    Returns:
        Validation rule function

    Example:
        >>> valid_job_codes = {"ICT.01.001.M40", "ICT.01.002.P30"}
        >>> validator.add_rule(foreign_key_check("job_code", valid_job_codes, "mercer_job_library"))
    """
    def rule(data: dict, record_id: Optional[str] = None) -> Optional[ValidationError]:
        value = data.get(field)

        if value is not None and value not in valid_keys:
            return ValidationError(
                field=field,
                error_type="foreign_key",
                message=f"Field '{field}' value '{value}' does not exist in {reference_table}",
                value=value,
                record_id=record_id
            )

        return None

    rule.__name__ = f"foreign_key_check_{field}"
    return rule


def string_length_check(
    field: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    allow_none: bool = False
) -> Callable:
    """
    Validate that a string field length is within bounds.

    Args:
        field: Field name to validate
        min_length: Minimum string length
        max_length: Maximum string length
        allow_none: If True, None values are acceptable

    Returns:
        Validation rule function

    Example:
        >>> validator.add_rule(string_length_check("job_title", min_length=3, max_length=200))
    """
    def rule(data: dict, record_id: Optional[str] = None) -> Optional[ValidationError]:
        value = data.get(field)

        if value is None:
            if allow_none:
                return None
            else:
                return ValidationError(
                    field=field,
                    error_type="string_length",
                    message=f"Field '{field}' is None but length check requires a value",
                    value=value,
                    record_id=record_id
                )

        if not isinstance(value, str):
            return ValidationError(
                field=field,
                error_type="string_length",
                message=f"Field '{field}' is not a string (type: {type(value).__name__})",
                value=value,
                record_id=record_id
            )

        length = len(value)

        if min_length is not None and length < min_length:
            return ValidationError(
                field=field,
                error_type="string_length",
                message=f"Field '{field}' length {length} is below minimum {min_length}",
                value=value,
                record_id=record_id
            )

        if max_length is not None and length > max_length:
            return ValidationError(
                field=field,
                error_type="string_length",
                message=f"Field '{field}' length {length} exceeds maximum {max_length}",
                value=value,
                record_id=record_id
            )

        return None

    rule.__name__ = f"string_length_check_{field}_{min_length}_{max_length}"
    return rule


def pattern_check(field: str, pattern: str, allow_none: bool = False) -> Callable:
    """
    Validate that a string field matches a regex pattern.

    Args:
        field: Field name to validate
        pattern: Regular expression pattern
        allow_none: If True, None values are acceptable

    Returns:
        Validation rule function

    Example:
        >>> validator.add_rule(pattern_check("job_code", r"^[A-Z]{3}\.\d{2}\.\d{3}\.[MP]\d{2}$"))
    """
    import re
    regex = re.compile(pattern)

    def rule(data: dict, record_id: Optional[str] = None) -> Optional[ValidationError]:
        value = data.get(field)

        if value is None:
            if allow_none:
                return None
            else:
                return ValidationError(
                    field=field,
                    error_type="pattern",
                    message=f"Field '{field}' is None but pattern match requires a value",
                    value=value,
                    record_id=record_id
                )

        if not isinstance(value, str):
            return ValidationError(
                field=field,
                error_type="pattern",
                message=f"Field '{field}' is not a string (type: {type(value).__name__})",
                value=value,
                record_id=record_id
            )

        if not regex.match(value):
            return ValidationError(
                field=field,
                error_type="pattern",
                message=f"Field '{field}' value '{value}' does not match pattern '{pattern}'",
                value=value,
                record_id=record_id
            )

        return None

    rule.__name__ = f"pattern_check_{field}"
    return rule


def custom_check(
    field: str,
    check_function: Callable[[Any], bool],
    error_message: str,
    error_type: str = "custom"
) -> Callable:
    """
    Create a custom validation rule with arbitrary logic.

    Args:
        field: Field name to validate
        check_function: Function that returns True if validation passes
        error_message: Error message if validation fails
        error_type: Type of validation error

    Returns:
        Validation rule function

    Example:
        >>> def is_valid_ipe_range(data):
        ...     return data.get("ipe_minimum") < data.get("ipe_maximum")
        >>>
        >>> validator.add_rule(custom_check(
        ...     field="ipe_minimum",
        ...     check_function=lambda d: d.get("ipe_minimum") < d.get("ipe_maximum"),
        ...     error_message="IPE minimum must be less than IPE maximum"
        ... ))
    """
    def rule(data: dict, record_id: Optional[str] = None) -> Optional[ValidationError]:
        value = data.get(field)

        try:
            if not check_function(data):
                return ValidationError(
                    field=field,
                    error_type=error_type,
                    message=error_message,
                    value=value,
                    record_id=record_id
                )
        except Exception as e:
            return ValidationError(
                field=field,
                error_type="custom_exception",
                message=f"Custom validation raised exception: {e}",
                value=value,
                record_id=record_id
            )

        return None

    rule.__name__ = f"custom_check_{field}"
    return rule


def conditional_required(field: str, condition_field: str, condition_value: Any) -> Callable:
    """
    Validate that a field is required only if another field has a specific value.

    Args:
        field: Field name to validate
        condition_field: Field to check condition on
        condition_value: Value that triggers requirement

    Returns:
        Validation rule function

    Example:
        >>> # job_description is required only if career_level is "M5" or "M6"
        >>> validator.add_rule(conditional_required("job_description", "career_level", "M5"))
    """
    def rule(data: dict, record_id: Optional[str] = None) -> Optional[ValidationError]:
        condition = data.get(condition_field)

        if condition == condition_value:
            value = data.get(field)

            if value is None or (isinstance(value, str) and value.strip() == ""):
                return ValidationError(
                    field=field,
                    error_type="conditional_required",
                    message=f"Field '{field}' is required when '{condition_field}' is '{condition_value}'",
                    value=value,
                    record_id=record_id
                )

        return None

    rule.__name__ = f"conditional_required_{field}_if_{condition_field}_is_{condition_value}"
    return rule
