from src.app.people.services.addressParts import normalize_address, suggestion_from_geoapify


def test_elvanto_address_lines_become_flocki_fields():
    parts = normalize_address({
        "address": "12 Church Street",
        "address2": "Unit 3",
        "city": "Cape Town",
        "state": "Western Cape",
        "postcode": "8001",
        "country": "South Africa",
        "lat": "-33.92",
        "lng": "18.42",
    })

    assert parts["street_number"] == "12"
    assert parts["street"] == "Church Street"
    assert parts["unit"] == "Unit 3"
    assert parts["city"] == "Cape Town"
    assert parts["province"] == "Western Cape"
    assert parts["postal_code"] == "8001"
    assert parts["country"] == "South Africa"
    assert parts["latitude"] == -33.92
    assert parts["longitude"] == 18.42


def test_structured_import_keeps_explicit_fields():
    parts = normalize_address({
        "street_number": "4",
        "street": "Main Road",
        "suburb": "Gardens",
        "city": "Cape Town",
        "province": "Western Cape",
        "postal_code": "8001",
        "country": "South Africa",
        "building": "The Annex",
    })

    assert parts["street_number"] == "4"
    assert parts["street"] == "Main Road"
    assert parts["suburb"] == "Gardens"
    assert parts["building"] == "The Annex"


def test_second_address_line_can_be_a_suburb():
    parts = normalize_address({
        "address": "Main Road",
        "address2": "Gardens",
        "city": "Cape Town",
        "country": "South Africa",
    })

    assert parts["street"] == "Main Road"
    assert parts["suburb"] == "Gardens"
    assert parts["unit"] is None


def test_geoapify_result_maps_to_a_suggestion():
    suggestion = suggestion_from_geoapify({
        "housenumber": "21",
        "street": "Allan Road",
        "suburb": "Noordwyk",
        "city": "Midrand",
        "state": "Gauteng",
        "postcode": "1685",
        "country": "South Africa",
        "lat": -25.99,
        "lon": 28.12,
        "formatted": "21 Allan Road, Noordwyk, Midrand, 1685, South Africa",
        "address_line2": "Noordwyk, Midrand",
    })

    assert suggestion["label"].startswith("21 Allan Road")
    assert suggestion["street_number"] == "21"
    assert suggestion["street"] == "Allan Road"
    assert suggestion["suburb"] == "Noordwyk"
    assert suggestion["province"] == "Gauteng"
    assert suggestion["building"] is None
    assert suggestion["latitude"] == -25.99
    assert suggestion["longitude"] == 28.12
