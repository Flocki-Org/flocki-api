import datetime
from datetime import timedelta

from sqlalchemy import String as SqlString
from sqlalchemy import and_, extract, func, or_, select, cast

from src.app.customfields.models.database.models import CustomFieldValue
from src.app.departments.models.database.models import DepartmentPerson
from src.app.groups.models.database.models import GroupMembership
from src.app.people.models.database import models


def years_ago(years: int, today: datetime.date) -> datetime.date:
    try:
        return today.replace(year=today.year - years)
    except ValueError:
        return today.replace(year=today.year - years, month=2, day=28)


def apply_people_filters(query, filters):
    person = models.Person
    if filters.first_name:
        query = query.filter(person.first_name.ilike(f"%{filters.first_name}%"))
    if filters.preferred_name:
        query = query.filter(person.preferred_name.ilike(f"%{filters.preferred_name}%"))
    if filters.last_name:
        query = query.filter(person.last_name.ilike(f"%{filters.last_name}%"))
    if filters.full_name:
        combined = func.lower(
            func.coalesce(person.first_name, "")
            + " "
            + func.coalesce(person.preferred_name, "")
            + " "
            + func.coalesce(person.middle_name, "")
            + " "
            + func.coalesce(person.last_name, "")
        )
        query = query.filter(combined.contains(filters.full_name.lower()))
    if filters.email:
        term = f"%{filters.email}%"
        query = query.filter(or_(
            person.email.ilike(term),
            person.emails.any(models.PersonEmail.email.ilike(term)),
        ))
    if filters.phone:
        term = f"%{filters.phone}%"
        query = query.filter(or_(
            person.mobile_number.ilike(term),
            person.phones.any(models.PersonPhone.number.ilike(term)),
        ))
    if filters.gender:
        query = query.filter(person.gender == filters.gender)
    if filters.marital_status:
        query = query.filter(person.marital_status == filters.marital_status)
    today = datetime.date.today()
    if filters.age_min is not None:
        query = query.filter(person.date_of_birth <= years_ago(filters.age_min, today))
    if filters.age_max is not None:
        query = query.filter(person.date_of_birth > years_ago(filters.age_max + 1, today))
    if filters.date_of_birth:
        query = query.filter(person.date_of_birth == filters.date_of_birth)
    if filters.birthday_month:
        query = query.filter(extract("month", person.date_of_birth) == filters.birthday_month)
    if filters.membership_status:
        query = query.filter(person.membership_status == filters.membership_status)
    if filters.lifecycle_status:
        query = query.filter(person.lifecycle_status == filters.lifecycle_status)
    if filters.archived is True:
        query = query.filter(person.lifecycle_status == "archived")
    elif filters.archived is False:
        query = query.filter(or_(person.lifecycle_status.is_(None), person.lifecycle_status != "archived"))
    if filters.category_ids:
        query = query.filter(
            person.category_links.any(models.PersonCategoryLink.category_id.in_(filters.category_ids))
        )
    if filters.household_id:
        query = query.filter(person.households.any(models.Household.id == filters.household_id))
    if filters.group_id:
        query = query.filter(person.id.in_(
            select(GroupMembership.person_id).where(
                GroupMembership.group_id == filters.group_id,
                GroupMembership.status == "active",
            )
        ))
    if filters.department_id:
        query = query.filter(person.id.in_(
            select(DepartmentPerson.person_id).where(DepartmentPerson.department_id == filters.department_id)
        ))
    if filters.custom_field_id and filters.custom_field_value is not None:
        term = f"%{filters.custom_field_value}%"
        query = query.filter(person.id.in_(
            select(CustomFieldValue.entity_id).where(
                CustomFieldValue.entity_type == "person",
                CustomFieldValue.field_id == filters.custom_field_id,
                or_(
                    CustomFieldValue.value_text.ilike(term),
                    cast(CustomFieldValue.value_json, SqlString).ilike(term),
                ),
            )
        ))
    return apply_sort(query, filters)


def apply_sort(query, filters):
    person = models.Person
    columns = {
        "last_name": person.last_name,
        "first_name": person.first_name,
        "preferred_name": person.preferred_name,
        "date_of_birth": person.date_of_birth,
        "registered_date": person.registered_date,
        "id": person.id,
    }
    column = columns.get(filters.sort or "last_name", person.last_name)
    ordered = column.desc() if filters.direction == "desc" else column.asc()
    return query.order_by(ordered, person.id.asc())


def month_day_filter(column, start: datetime.date, days: int):
    clauses = []
    for offset in range(days + 1):
        day = start + timedelta(days=offset)
        clauses.append(and_(extract("month", column) == day.month, extract("day", column) == day.day))
    return or_(*clauses)


def exclude_closed_records(query):
    person = models.Person
    return query.filter(or_(
        person.lifecycle_status.is_(None),
        person.lifecycle_status.notin_(["archived", "deceased"]),
    ))
