import datetime
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from starlette.responses import Response

from src.app.events.models.events import (
    CancelOccurrence,
    CancelRange,
    CreateEvent,
    DuplicateEvent,
    EventTypeInput,
    EventTypeUpdate,
    EventTypeView,
    OccurrenceView,
    PlanInput,
    PlanItemView,
    PlanView,
    SeriesView,
    SongUsageDetail,
    SongUsageView,
    TemplateInput,
    UpdateEventSeries,
    UpdateOccurrence,
)
from src.app.events.services.eventService import (
    EventService,
    EventTypeInUseException,
    InvalidEventException,
    NoEventTypeException,
    NoOccurrenceException,
    NoOrderOfServiceException,
    NoSeriesException,
)
from src.app.events.services.songUsageService import SongUsageService
from src.app.media.services.mediaService import MediaService
from src.app.users.models.user import User
from src.app.users.routers.login import get_current_user
from src.app.utils.fileUtils import FileUtils

router = APIRouter(tags=["Events"])


def _actor_id(current_user):
    return getattr(current_user, "id", None)


def _handle(callable_, *args, **kwargs):
    try:
        return callable_(*args, **kwargs)
    except (NoEventTypeException, NoSeriesException, NoOccurrenceException) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except EventTypeInUseException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except (InvalidEventException, NoOrderOfServiceException) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


def _store_image(file: UploadFile, media_service: MediaService, description: str):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload an image file")
    base = os.path.splitext(file.filename or "event")[0].strip() or "event"
    filename = f"{base}_{uuid.uuid4()}.{FileUtils.get_file_extension(file)}"
    return media_service.upload_image(file, filename, description)


# Event types


@router.get("/events/types", response_model=List[EventTypeView])
def list_event_types(include_inactive: bool = False, service: EventService = Depends(EventService),
                     current_user: User = Depends(get_current_user)):
    return service.list_types(include_inactive)


@router.post("/events/types", status_code=status.HTTP_201_CREATED, response_model=EventTypeView)
def create_event_type(payload: EventTypeInput, service: EventService = Depends(EventService),
                      current_user: User = Depends(get_current_user)):
    return _handle(service.create_type, payload)


@router.put("/events/types/{type_id}", response_model=EventTypeView)
def update_event_type(type_id: int, payload: EventTypeUpdate, service: EventService = Depends(EventService),
                      current_user: User = Depends(get_current_user)):
    return _handle(service.update_type, type_id, payload)


@router.delete("/events/types/{type_id}")
def delete_event_type(type_id: int, service: EventService = Depends(EventService),
                      current_user: User = Depends(get_current_user)):
    """Deactivates a type that events still use; deletes it otherwise."""
    result = _handle(service.delete_type, type_id)
    return result if result is not None else {"deleted": True}


# Calendar


@router.get("/events", response_model=List[OccurrenceView])
def list_events(
    start: datetime.date,
    end: datetime.date,
    type_id: Optional[List[int]] = Query(None),
    group_id: Optional[int] = None,
    include_cancelled: bool = True,
    services_only: bool = False,
    service: EventService = Depends(EventService),
    current_user: User = Depends(get_current_user),
):
    """Every occurrence from start to end inclusive (at most 400 days)."""
    return _handle(service.list_occurrences, start, end, type_id, group_id, include_cancelled, services_only)


@router.post("/events", status_code=status.HTTP_201_CREATED, response_model=SeriesView)
def create_event(payload: CreateEvent, service: EventService = Depends(EventService),
                 current_user: User = Depends(get_current_user)):
    """Creates a once-off event, or a recurring series when `recurrence` is set."""
    return _handle(service.create, payload, _actor_id(current_user))


@router.get("/services/upcoming", response_model=List[OccurrenceView])
def upcoming_services(days: int = Query(28, ge=1, le=180), service: EventService = Depends(EventService),
                      current_user: User = Depends(get_current_user)):
    """Upcoming events whose type has an order of service, with their planning state."""
    today = datetime.date.today()
    return _handle(service.list_occurrences, today, today + datetime.timedelta(days=days),
                   None, None, True, True)


# Series


@router.get("/events/series", response_model=List[SeriesView])
def list_series(type_id: Optional[int] = None, group_id: Optional[int] = None, include_archived: bool = False,
                service: EventService = Depends(EventService), current_user: User = Depends(get_current_user)):
    return service.list_series(type_id, group_id, include_archived)


@router.get("/events/series/{series_id}", response_model=SeriesView)
def get_series(series_id: int, service: EventService = Depends(EventService),
               current_user: User = Depends(get_current_user)):
    return _handle(service.get_series, series_id)


@router.put("/events/series/{series_id}", response_model=SeriesView)
def update_series(series_id: int, payload: UpdateEventSeries, service: EventService = Depends(EventService),
                  current_user: User = Depends(get_current_user)):
    """Changes every occurrence. Matching per-occurrence overrides are cleared."""
    return _handle(service.update_series, series_id, payload)


@router.delete("/events/series/{series_id}", response_model=SeriesView)
def archive_series(series_id: int, service: EventService = Depends(EventService),
                   current_user: User = Depends(get_current_user)):
    """Archives the event. Saved orders of service are kept."""
    return _handle(service.archive_series, series_id)


@router.post("/events/series/{series_id}/restore", response_model=SeriesView)
def restore_series(series_id: int, service: EventService = Depends(EventService),
                   current_user: User = Depends(get_current_user)):
    return _handle(service.restore_series, series_id)


@router.post("/events/series/{series_id}/image", response_model=SeriesView)
def upload_series_image(series_id: int, file: UploadFile, service: EventService = Depends(EventService),
                        media_service: MediaService = Depends(MediaService),
                        current_user: User = Depends(get_current_user)):
    _handle(service.get_series, series_id)
    image = _store_image(file, media_service, f"Image for event {series_id}")
    return _handle(service.set_series_image, series_id, image.id)


@router.delete("/events/series/{series_id}/image", response_model=SeriesView)
def remove_series_image(series_id: int, service: EventService = Depends(EventService),
                        current_user: User = Depends(get_current_user)):
    return _handle(service.set_series_image, series_id, None)


@router.post("/events/series/{series_id}/duplicate", status_code=status.HTTP_201_CREATED, response_model=SeriesView)
def duplicate_series(series_id: int, payload: DuplicateEvent, service: EventService = Depends(EventService),
                     current_user: User = Depends(get_current_user)):
    """Copies the whole series, schedule and order-of-service template included, to start on `date`."""
    return _handle(service.duplicate_series, series_id, payload, _actor_id(current_user))


@router.post("/events/series/{series_id}/cancel-range", response_model=List[OccurrenceView])
def cancel_range(series_id: int, payload: CancelRange, service: EventService = Depends(EventService),
                 current_user: User = Depends(get_current_user)):
    return _handle(service.cancel_range, series_id, payload)


@router.get("/events/series/{series_id}/template", response_model=List[PlanItemView])
def get_template(series_id: int, service: EventService = Depends(EventService),
                 current_user: User = Depends(get_current_user)):
    return _handle(service.get_template, series_id)


@router.put("/events/series/{series_id}/template", response_model=List[PlanItemView])
def replace_template(series_id: int, payload: TemplateInput, service: EventService = Depends(EventService),
                     current_user: User = Depends(get_current_user)):
    """The order of service that new occurrences start from."""
    return _handle(service.replace_template, series_id, payload)


# Occurrences


@router.get("/events/occurrences/{series_id}/{original_date}", response_model=OccurrenceView)
def get_occurrence(series_id: int, original_date: datetime.date, service: EventService = Depends(EventService),
                   current_user: User = Depends(get_current_user)):
    return _handle(service.get_occurrence, series_id, original_date)


@router.patch("/events/occurrences/{series_id}/{original_date}", response_model=OccurrenceView)
def update_occurrence(series_id: int, original_date: datetime.date, payload: UpdateOccurrence,
                      service: EventService = Depends(EventService), current_user: User = Depends(get_current_user)):
    """`scope` is 'this', 'following' (splits the series from this date) or 'all'."""
    return _handle(service.update_occurrence, series_id, original_date, payload)


@router.post("/events/occurrences/{series_id}/{original_date}/cancel", response_model=OccurrenceView)
def cancel_occurrence(series_id: int, original_date: datetime.date, payload: CancelOccurrence | None = None,
                      service: EventService = Depends(EventService), current_user: User = Depends(get_current_user)):
    return _handle(service.cancel_occurrence, series_id, original_date, payload.reason if payload else None)


@router.post("/events/occurrences/{series_id}/{original_date}/restore", response_model=OccurrenceView)
def restore_occurrence(series_id: int, original_date: datetime.date, service: EventService = Depends(EventService),
                       current_user: User = Depends(get_current_user)):
    return _handle(service.restore_occurrence, series_id, original_date)


@router.post("/events/occurrences/{series_id}/{original_date}/image", response_model=OccurrenceView)
def upload_occurrence_image(series_id: int, original_date: datetime.date, file: UploadFile,
                            service: EventService = Depends(EventService),
                            media_service: MediaService = Depends(MediaService),
                            current_user: User = Depends(get_current_user)):
    _handle(service.get_occurrence, series_id, original_date)
    image = _store_image(file, media_service, f"Image for event {series_id} on {original_date.isoformat()}")
    return _handle(service.set_occurrence_image, series_id, original_date, image.id)


@router.delete("/events/occurrences/{series_id}/{original_date}/image", response_model=OccurrenceView)
def remove_occurrence_image(series_id: int, original_date: datetime.date, service: EventService = Depends(EventService),
                            current_user: User = Depends(get_current_user)):
    """Falls back to the series image."""
    return _handle(service.set_occurrence_image, series_id, original_date, None)


@router.post("/events/occurrences/{series_id}/{original_date}/duplicate", status_code=status.HTTP_201_CREATED,
             response_model=OccurrenceView)
def duplicate_occurrence(series_id: int, original_date: datetime.date, payload: DuplicateEvent,
                         service: EventService = Depends(EventService), current_user: User = Depends(get_current_user)):
    """Copies this date into a new once-off event, for example next year's Good Friday."""
    return _handle(service.duplicate_occurrence, series_id, original_date, payload, _actor_id(current_user))


@router.get("/events/occurrences/{series_id}/{original_date}/plan", response_model=PlanView)
def get_plan(series_id: int, original_date: datetime.date, service: EventService = Depends(EventService),
             current_user: User = Depends(get_current_user)):
    """The order of service. Until it is saved, this is a preview of the series template."""
    return _handle(service.get_plan, series_id, original_date)


@router.put("/events/occurrences/{series_id}/{original_date}/plan", response_model=PlanView)
def save_plan(series_id: int, original_date: datetime.date, payload: PlanInput,
              service: EventService = Depends(EventService), current_user: User = Depends(get_current_user)):
    return _handle(service.save_plan, series_id, original_date, payload)


@router.delete("/events/occurrences/{series_id}/{original_date}/plan", response_model=PlanView)
def reset_plan(series_id: int, original_date: datetime.date, service: EventService = Depends(EventService),
               current_user: User = Depends(get_current_user)):
    """Discards this date's order of service so it starts from the template again."""
    return _handle(service.reset_plan, series_id, original_date)


# Song usage


@router.get("/songs/usage", response_model=List[SongUsageView])
def song_usage(start: datetime.date, end: datetime.date, limit: Optional[int] = Query(None, ge=1, le=500),
               usage_service: SongUsageService = Depends(SongUsageService),
               current_user: User = Depends(get_current_user)):
    return usage_service.usage(start, end, limit)


@router.get("/songs/ccli-report")
def ccli_report(start: datetime.date, end: datetime.date, usage_service: SongUsageService = Depends(SongUsageService),
                current_user: User = Depends(get_current_user)):
    """CSV of songs used from start to end with CCLI numbers, for CCLI reporting."""
    body = usage_service.ccli_csv(start, end)
    filename = f"ccli-report-{start.isoformat()}-to-{end.isoformat()}.csv"
    return Response(content=body, media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/song/{song_id}/usage", response_model=SongUsageDetail)
def song_usage_detail(song_id: int, usage_service: SongUsageService = Depends(SongUsageService),
                      current_user: User = Depends(get_current_user)):
    return usage_service.detail(song_id)
