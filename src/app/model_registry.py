"""Import every SQLAlchemy model so Base.metadata is complete before create_all."""


def import_all_models() -> None:
    from src.app.audit.models.database import models as audit_models  # noqa: F401
    from src.app.church.models.database import models as church_models  # noqa: F401
    from src.app.customfields.models.database import models as custom_field_models  # noqa: F401
    from src.app.dashboard.models.database import models as dashboard_models  # noqa: F401
    from src.app.departments.models.database import models as department_models  # noqa: F401
    from src.app.events.models.database import models as event_models  # noqa: F401
    from src.app.groups.models.database import models as group_models  # noqa: F401
    from src.app.imports.models.database import models as import_models  # noqa: F401
    from src.app.media.models.database import models as media_models  # noqa: F401
    from src.app.people.models.database import models as people_models  # noqa: F401
    from src.app.users.models.database import models as user_models  # noqa: F401
    from src.app.worship.models.database import models as worship_models  # noqa: F401
