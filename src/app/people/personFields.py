"""Column names that can be written on people without touching relationships."""

LEGACY_PERSON_FIELDS = (
    "first_name",
    "last_name",
    "email",
    "mobile_number",
    "date_of_birth",
    "gender",
    "marriage_date",
    "marital_status",
    "registered_date",
)

PROFILE_PERSON_FIELDS = (
    "preferred_name",
    "middle_name",
    "title",
    "biography",
    "preferred_contact_method",
    "contact_preferences",
    "membership_status",
    "member_since",
    "date_first_attended",
    "baptism_status",
    "baptism_date",
    "baptism_location",
    "confirmation_date",
    "previous_church",
    "membership_transfer_notes",
    "date_joined",
    "date_membership_ended",
    "reason_for_leaving",
    "ministry_involvement",
    "pastoral_notes",
    "lifecycle_status",
    "school_grade",
    "school_name",
    "occupation",
    "employer",
    "nationality",
    "preferred_language",
    "timezone",
    "volunteer_status",
    "skills",
    "interests",
    "allergies",
    "special_requirements",
    "emergency_notes",
)

WRITABLE_PERSON_COLUMNS = LEGACY_PERSON_FIELDS + PROFILE_PERSON_FIELDS

# Values are accepted even when they are not in reference data, so a church can
# record the wording it actually uses. These are the suggested defaults.
RELATIONSHIP_TYPES = (
    "spouse",
    "parent",
    "child",
    "sibling",
    "guardian",
    "dependent",
    "other",
)

INVERSE_RELATIONSHIP = {
    "spouse": "spouse",
    "sibling": "sibling",
    "parent": "child",
    "child": "parent",
    "guardian": "dependent",
    "dependent": "guardian",
    "other": "other",
}

SENSITIVE_PERSON_FIELDS = {
    "biography",
    "pastoral_notes",
    "allergies",
    "special_requirements",
    "emergency_notes",
    "contact_preferences",
    "membership_transfer_notes",
    "reason_for_leaving",
    "ministry_involvement",
}


def writable_person_updates(person) -> dict:
    """Scalar columns explicitly provided on a create/update model."""
    raw = person.model_dump(exclude_unset=True)
    return {key: value for key, value in raw.items() if key in WRITABLE_PERSON_COLUMNS}
