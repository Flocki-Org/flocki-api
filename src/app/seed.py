"""Idempotent reference data, group roles and event types for a new or existing database."""

from fastapi import Depends

from src.app.database import SessionLocal, get_db
from src.app.events.models.database import models as event_models
from src.app.groups.models.database import models as group_models
from src.app.people.models.database import models as people_models

REFERENCE_VALUES = {
    "gender": ["male", "female", "unknown", "other"],
    "marital_status": ["single", "married", "divorced", "remarried", "widowed", "separated"],
    "lifecycle_status": ["visitor", "regular_attender", "member", "inactive", "archived", "deceased"],
    "membership_status": ["none", "adherent", "member", "former"],
    "phone_type": ["mobile", "home", "work", "other"],
    "address_type": ["home", "postal", "business", "student_accommodation", "church", "other"],
    "relationship_type": ["spouse", "parent", "child", "sibling", "guardian", "dependent", "other"],
    "preferred_contact_method": ["email", "mobile", "phone", "none"],
    "group_status": ["active", "inactive", "archived"],
    "meeting_frequency": ["weekly", "fortnightly", "monthly", "ad_hoc", "none"],
}

GROUP_ROLES = (
    ("Leader", True, 1),
    ("Assistant leader", True, 2),
    ("Member", False, 3),
    ("Administrator", False, 4),
    ("Coordinator", True, 5),
)

# (name, colour, has order of service, tracks attendance, default location)
EVENT_TYPES = (
    ("Sunday Service", "#0369A1", True, True, "church"),
    ("Special Service", "#B45309", True, True, "church"),
    ("Bible Study", "#15803D", False, True, "address"),
    ("Prayer Meeting", "#7C3AED", False, True, "address"),
    ("Youth / Kids", "#DB2777", False, False, "church"),
    ("Ministry Gathering", "#0F766E", False, False, "address"),
    ("Social / Community", "#CA8A04", False, False, "address"),
    ("Church Meeting", "#475569", False, False, "church"),
)


def _label(value: str) -> str:
    return value.replace("_", " ").title()


class ReferenceSeed:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def seed(self) -> None:
        self._seed_reference_values()
        self._seed_group_roles()
        self._seed_event_types()
        self.db.commit()

    def _seed_event_types(self) -> None:
        # Seed once: staff may rename or retune these, so later boots never re-add or reset them.
        if self.db.query(event_models.EventType.id).first() is not None:
            return
        for order, (name, colour, order_of_service, attendance, location) in enumerate(EVENT_TYPES, start=1):
            self.db.add(
                event_models.EventType(
                    name=name,
                    colour=colour,
                    has_order_of_service=order_of_service,
                    tracks_attendance=attendance,
                    default_location=location,
                    display_order=order,
                    active=True,
                )
            )

    def _seed_reference_values(self) -> None:
        for domain, values in REFERENCE_VALUES.items():
            for order, value in enumerate(values, start=1):
                existing = (
                    self.db.query(people_models.ReferenceValue)
                    .filter(
                        people_models.ReferenceValue.domain == domain,
                        people_models.ReferenceValue.value == value,
                    )
                    .first()
                )
                if existing is None:
                    self.db.add(
                        people_models.ReferenceValue(
                            domain=domain,
                            value=value,
                            label=_label(value),
                            active=True,
                            display_order=order,
                        )
                    )

    def _seed_group_roles(self) -> None:
        for name, is_leader, order in GROUP_ROLES:
            existing = (
                self.db.query(group_models.GroupRole)
                .filter(group_models.GroupRole.name == name)
                .first()
            )
            if existing is None:
                self.db.add(
                    group_models.GroupRole(
                        name=name,
                        is_leader=is_leader,
                        display_order=order,
                        active=True,
                    )
                )


def seed_reference_data() -> None:
    db = SessionLocal()
    try:
        ReferenceSeed(db=db).seed()
    finally:
        db.close()
