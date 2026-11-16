import datetime
from typing import List

from fastapi import Depends
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_, select

from src.app.dashboard.models.database.models import DashboardLayout
from src.app.database import SessionLocal, get_db
from src.app.groups.models.database.models import Group, GroupMembership
from src.app.people.models.database.models import Person, PersonEmail, PersonPhone
from src.app.users.models.database.models import User

WIDGETS = (
    ("this_week", "This week"),
    ("services_to_plan", "Services to plan"),
    ("people_overview", "People at a glance"),
    ("birthdays", "Upcoming birthdays"),
    ("anniversaries", "Upcoming anniversaries"),
    ("recent_people", "Recently added people"),
    ("contact_gaps", "Missing contact details"),
    ("not_in_group", "People not in a group"),
    ("groups_overview", "Groups at a glance"),
    ("top_songs", "Most used songs"),
)
WIDGET_IDS = tuple(widget_id for widget_id, _ in WIDGETS)
HIDDEN_BY_DEFAULT = {"anniversaries"}


class WidgetSetting(BaseModel):
    id: str
    visible: bool = True


class WidgetCatalogueEntry(BaseModel):
    id: str
    label: str


class DashboardLayoutView(BaseModel):
    widgets: List[WidgetSetting]
    catalogue: List[WidgetCatalogueEntry]
    customised: bool = False


class DashboardLayoutInput(BaseModel):
    widgets: List[WidgetSetting] = Field(default_factory=list)


class StatusCount(BaseModel):
    status: str
    count: int


class DashboardSummary(BaseModel):
    people_total: int
    people_new_last_30_days: int
    people_by_status: List[StatusCount]
    people_without_email: int
    people_without_mobile: int
    people_without_group: int
    groups_active: int
    group_memberships_active: int


def default_widgets():
    return [WidgetSetting(id=widget_id, visible=widget_id not in HIDDEN_BY_DEFAULT) for widget_id in WIDGET_IDS]


def normalise_widgets(widgets):
    """Keep known widgets in the saved order, drop unknown ones, append widgets added since."""
    seen = set()
    result = []
    for widget in widgets:
        widget_id = widget["id"] if isinstance(widget, dict) else widget.id
        visible = widget.get("visible", True) if isinstance(widget, dict) else widget.visible
        if widget_id in WIDGET_IDS and widget_id not in seen:
            result.append(WidgetSetting(id=widget_id, visible=bool(visible)))
            seen.add(widget_id)
    for widget in default_widgets():
        if widget.id not in seen:
            result.append(widget)
    return result


def _catalogue():
    return [WidgetCatalogueEntry(id=widget_id, label=label) for widget_id, label in WIDGETS]


class DashboardService:
    def __init__(self, db: SessionLocal = Depends(get_db)):
        self.db = db

    def layout(self, user_id):
        saved = self._saved(user_id)
        if saved is None:
            return DashboardLayoutView(widgets=default_widgets(), catalogue=_catalogue(), customised=False)
        return DashboardLayoutView(widgets=normalise_widgets(saved.widgets or []), catalogue=_catalogue(), customised=True)

    def save_layout(self, user_id, payload: DashboardLayoutInput):
        widgets = [widget.model_dump() for widget in normalise_widgets(payload.widgets)]
        saved = self._saved(user_id)
        if saved is None:
            saved = DashboardLayout(user_id=user_id, widgets=widgets)
            self.db.add(saved)
        else:
            saved.widgets = widgets
        self.db.commit()
        return self.layout(user_id)

    def reset_layout(self, user_id):
        saved = self._saved(user_id)
        if saved is not None:
            self.db.delete(saved)
            self.db.commit()
        return self.layout(user_id)

    def summary(self, today: datetime.date | None = None):
        today = today or datetime.date.today()
        open_people = or_(Person.lifecycle_status.is_(None), Person.lifecycle_status.notin_(["archived", "deceased"]))
        base = self.db.query(Person).filter(open_people, Person.archived_at.is_(None))
        status_rows = (
            self.db.query(func.coalesce(Person.lifecycle_status, "unknown"), func.count(Person.id))
            .filter(open_people, Person.archived_at.is_(None))
            .group_by(func.coalesce(Person.lifecycle_status, "unknown"))
            .all()
        )
        has_email = select(PersonEmail.person_id)
        has_phone = select(PersonPhone.person_id)
        in_group = select(GroupMembership.person_id).where(GroupMembership.status == "active")
        return DashboardSummary(
            people_total=base.count(),
            people_new_last_30_days=base.filter(Person.registered_date >= today - datetime.timedelta(days=30)).count(),
            people_by_status=sorted(
                [StatusCount(status=status, count=count) for status, count in status_rows],
                key=lambda row: -row.count,
            ),
            people_without_email=base.filter(
                or_(Person.email.is_(None), Person.email == ""), Person.id.notin_(has_email)
            ).count(),
            people_without_mobile=base.filter(
                or_(Person.mobile_number.is_(None), Person.mobile_number == ""), Person.id.notin_(has_phone)
            ).count(),
            people_without_group=base.filter(Person.id.notin_(in_group)).count(),
            groups_active=self.db.query(Group).filter(Group.status == "active").count(),
            group_memberships_active=(
                self.db.query(GroupMembership)
                .join(Group, and_(Group.id == GroupMembership.group_id, Group.status == "active"))
                .filter(GroupMembership.status == "active")
                .count()
            ),
        )

    def user_id_for(self, current_user):
        """The signed-in principal is a token carrying the email as `username`; staff rows key on users.id."""
        user_id = getattr(current_user, "id", None)
        if user_id is not None:
            return user_id
        email = getattr(current_user, "username", None) or getattr(current_user, "email", None)
        if not email:
            return None
        row = self.db.query(User.id).filter(func.lower(User.email) == email.lower()).first()
        return row[0] if row else None

    def _saved(self, user_id):
        return self.db.query(DashboardLayout).filter(DashboardLayout.user_id == user_id).first()
