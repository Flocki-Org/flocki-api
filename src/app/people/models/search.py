import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PeopleSearchFilters(BaseModel):
    first_name: Optional[str] = None
    preferred_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    date_of_birth: Optional[datetime.date] = None
    birthday_month: Optional[int] = None
    membership_status: Optional[str] = None
    category_ids: List[int] = Field(default_factory=list)
    household_id: Optional[int] = None
    group_id: Optional[int] = None
    department_id: Optional[int] = None
    lifecycle_status: Optional[str] = None
    archived: Optional[bool] = None
    custom_field_id: Optional[int] = None
    custom_field_value: Optional[str] = None
    sort: Optional[str] = None
    direction: str = "asc"

    def is_empty(self) -> bool:
        return not any(
            [
                self.first_name,
                self.preferred_name,
                self.last_name,
                self.full_name,
                self.email,
                self.phone,
                self.gender,
                self.marital_status,
                self.age_min is not None,
                self.age_max is not None,
                self.date_of_birth,
                self.birthday_month,
                self.membership_status,
                self.category_ids,
                self.household_id,
                self.group_id,
                self.department_id,
                self.lifecycle_status,
                self.archived is not None,
                self.custom_field_id,
                self.custom_field_value,
                self.sort,
            ]
        )
