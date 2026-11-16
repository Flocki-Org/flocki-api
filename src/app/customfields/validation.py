import datetime
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

FIELD_TYPES = (
    "text",
    "long_text",
    "number",
    "decimal",
    "date",
    "boolean",
    "single_select",
    "multi_select",
    "url",
    "email",
    "phone",
)

SELECT_TYPES = {"single_select", "multi_select"}
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE = re.compile(r"^[0-9+\-().\s]{3,40}$")


class CustomFieldValidationError(ValueError):
    pass


def empty_value_columns() -> dict:
    return {
        "value_text": None,
        "value_number": None,
        "value_decimal": None,
        "value_date": None,
        "value_bool": None,
        "value_json": None,
    }


def normalise_custom_value(field_type: str, value: Any, option_values: Optional[list[str]] = None, required: bool = False) -> dict:
    if field_type not in FIELD_TYPES:
        raise CustomFieldValidationError(f"Unsupported custom field type '{field_type}'")

    if _is_blank(value):
        if required:
            raise CustomFieldValidationError("A value is required")
        return empty_value_columns()

    columns = empty_value_columns()
    options = set(option_values or [])

    if field_type in {"text", "long_text"}:
        text = str(value).strip()
        if field_type == "text" and len(text) > 1000:
            raise CustomFieldValidationError("Text values are limited to 1000 characters")
        columns["value_text"] = text
    elif field_type == "number":
        if isinstance(value, bool) or not _is_int(value):
            raise CustomFieldValidationError("Number fields require a whole number")
        columns["value_number"] = int(value)
    elif field_type == "decimal":
        try:
            decimal = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise CustomFieldValidationError("Decimal fields require a numeric value") from exc
        columns["value_decimal"] = decimal
    elif field_type == "date":
        columns["value_date"] = _as_date(value)
    elif field_type == "boolean":
        columns["value_bool"] = _as_bool(value)
    elif field_type == "single_select":
        selected = str(value)
        if options and selected not in options:
            raise CustomFieldValidationError(f"'{selected}' is not one of the allowed options")
        columns["value_text"] = selected
    elif field_type == "multi_select":
        if not isinstance(value, (list, tuple)):
            raise CustomFieldValidationError("Multi-select fields require a list of options")
        selected = [str(item) for item in value]
        unknown = [item for item in selected if options and item not in options]
        if unknown:
            raise CustomFieldValidationError(f"Unknown options: {', '.join(unknown)}")
        columns["value_json"] = selected
    elif field_type == "url":
        url = str(value).strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            raise CustomFieldValidationError("URL fields must start with http:// or https://")
        columns["value_text"] = url
    elif field_type == "email":
        email = str(value).strip()
        if not _EMAIL.match(email):
            raise CustomFieldValidationError("Email fields require an email address")
        columns["value_text"] = email
    elif field_type == "phone":
        phone = str(value).strip()
        if not _PHONE.match(phone):
            raise CustomFieldValidationError("Phone fields require a phone number")
        columns["value_text"] = phone
    return columns


def display_custom_value(field_type: str, row) -> Any:
    if row is None:
        return None
    if field_type in {"text", "long_text", "single_select", "url", "email", "phone"}:
        return row.value_text
    if field_type == "number":
        return row.value_number
    if field_type == "decimal":
        return row.value_decimal
    if field_type == "date":
        return row.value_date
    if field_type == "boolean":
        return row.value_bool
    if field_type == "multi_select":
        return row.value_json or []
    return row.value_text


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, tuple)) and len(value) == 0:
        return True
    return False


def _is_int(value: Any) -> bool:
    if isinstance(value, int):
        return True
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value.strip()):
        return True
    return False


def _as_date(value: Any) -> datetime.date:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value[:10])
        except ValueError as exc:
            raise CustomFieldValidationError("Date fields require an ISO date (YYYY-MM-DD)") from exc
    raise CustomFieldValidationError("Date fields require an ISO date (YYYY-MM-DD)")


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false", "yes", "no", "1", "0"}:
        return value.strip().lower() in {"true", "yes", "1"}
    raise CustomFieldValidationError("Boolean fields require true or false")
