from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer

from src.app.database import Base
from src.app.database_types import portable_json
from src.app.users.models.database.models import User  # noqa: F401


def _naive_utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class DashboardLayout(Base):
    __tablename__ = "dashboard_layouts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    widgets = Column(portable_json(), nullable=False)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow, nullable=False)
    __table_args__ = (Index("ux_dashboard_layouts_user", "user_id", unique=True),)
