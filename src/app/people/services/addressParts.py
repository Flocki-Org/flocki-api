import re
from typing import Optional

# One normalizer for typed addresses, Geoapify suggestions, and Elvanto imports.
# Elvanto people and families usually send address, address2, city, state, postcode,
# and country. Coordinates may arrive as lat/lng. Structured Flocki keys are also accepted.

_LINE = re.compile(r"^(?P<number>\d+[A-Za-z]?(?:[/-]\d+[A-Za-z]?)?)\s+(?P<street>.+)$")
_UNIT = re.compile(r"^(unit|apt|apartment|flat|suite|#)\b", re.I)


def _bag(raw: dict) -> dict:
    values = {}
    for key, value in (raw or {}).items():
        if value is None:
            continue
        compact = re.sub(r"[^a-z0-9]", "", str(key).lower())
        values[compact] = value
    return values


def _text(values: dict, *keys: str) -> str:
    for key in keys:
        value = values.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _float(values: dict, *keys: str) -> Optional[float]:
    for key in keys:
        value = values.get(key)
        if value is None or value == "":
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def split_street_line(line: str) -> tuple[str, str]:
    text = (line or "").strip()
    match = _LINE.match(text)
    if not match:
        return "", text
    return match.group("number"), match.group("street").strip()


def _second_line(line: str, suburb: str) -> tuple[str, str, str]:
    """Return suburb, building, unit for an Elvanto second address line."""
    text = (line or "").strip()
    if not text:
        return suburb, "", ""
    if _UNIT.match(text):
        return suburb, "", text
    if not suburb:
        return text, "", ""
    return suburb, text, ""


def normalize_address(raw: dict) -> dict:
    values = _bag(raw)
    street_number = _text(values, "streetnumber", "housenumber")
    street = _text(values, "street")
    if not street_number or not street:
        line = _text(values, "address", "addressline1", "line1", "address1")
        number, parsed_street = split_street_line(line)
        street_number = street_number or number
        street = street or parsed_street
    suburb = _text(values, "suburb", "district", "neighbourhood", "neighborhood", "quarter")
    suburb, building, unit = _second_line(
        _text(values, "address2", "addressline2", "line2"),
        suburb,
    )
    building = _text(values, "building") or building
    unit = _text(values, "unit") or unit
    return {
        "type": _text(values, "type") or "home",
        "street_number": street_number,
        "street": street,
        "suburb": suburb,
        "city": _text(values, "city", "town", "village", "municipality"),
        "province": _text(values, "province", "state", "region", "county"),
        "country": _text(values, "country"),
        "postal_code": _text(values, "postalcode", "postcode", "zip"),
        "building": building or None,
        "unit": unit or None,
        "latitude": _float(values, "latitude", "lat"),
        "longitude": _float(values, "longitude", "lon", "lng"),
    }


def suggestion_from_geoapify(row: dict) -> dict:
    parts = normalize_address({
        "housenumber": row.get("housenumber"),
        "street": row.get("street"),
        "suburb": row.get("suburb"),
        "district": row.get("district"),
        "neighbourhood": row.get("neighbourhood"),
        "quarter": row.get("quarter"),
        "city": row.get("city"),
        "town": row.get("town"),
        "village": row.get("village"),
        "municipality": row.get("municipality"),
        "state": row.get("state"),
        "county": row.get("county"),
        "country": row.get("country"),
        "postcode": row.get("postcode"),
        "lat": row.get("lat"),
        "lon": row.get("lon"),
    })
    if not parts["street"]:
        number, street = split_street_line(str(row.get("address_line1") or ""))
        parts["street_number"] = parts["street_number"] or number
        parts["street"] = street
    if row.get("result_type") == "building" and row.get("name"):
        parts["building"] = str(row["name"]).strip() or None
    label = str(row.get("formatted") or "").strip()
    if not label:
        label = ", ".join(
            piece for piece in (
                " ".join(part for part in (parts["street_number"], parts["street"]) if part),
                parts["suburb"],
                parts["city"],
                parts["postal_code"],
                parts["country"],
            ) if piece
        )
    parts["label"] = label
    return parts
