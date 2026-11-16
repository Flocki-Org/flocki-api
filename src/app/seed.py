"""Idempotent reference data and group roles for a new or existing database."""

from fastapi import Depends

from src.app.database import SessionLocal, get_db
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


def _label(value: str) -> str:
    return value.replace("_", " ").title()


class ReferenceSeed:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def seed(self) -> None:
        self._seed_reference_values()
        self._seed_group_roles()
        self.db.commit()

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
