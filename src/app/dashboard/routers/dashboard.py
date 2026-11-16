from fastapi import APIRouter, Depends, HTTPException, status

from src.app.dashboard.services.dashboardService import (
    DashboardLayoutInput,
    DashboardLayoutView,
    DashboardService,
    DashboardSummary,
)
from src.app.users.models.user import User
from src.app.users.routers.login import get_current_user

router = APIRouter(tags=["Dashboard"])


def _user_id(service, current_user):
    user_id = service.user_id_for(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sign in to use the dashboard")
    return user_id


@router.get("/dashboard/layout", response_model=DashboardLayoutView)
def get_layout(service: DashboardService = Depends(DashboardService), current_user: User = Depends(get_current_user)):
    """The signed-in staff member's widget order and visibility, or the default layout."""
    return service.layout(_user_id(service, current_user))


@router.put("/dashboard/layout", response_model=DashboardLayoutView)
def save_layout(payload: DashboardLayoutInput, service: DashboardService = Depends(DashboardService),
                current_user: User = Depends(get_current_user)):
    return service.save_layout(_user_id(service, current_user), payload)


@router.delete("/dashboard/layout", response_model=DashboardLayoutView)
def reset_layout(service: DashboardService = Depends(DashboardService), current_user: User = Depends(get_current_user)):
    return service.reset_layout(_user_id(service, current_user))


@router.get("/dashboard/summary", response_model=DashboardSummary)
def summary(service: DashboardService = Depends(DashboardService), current_user: User = Depends(get_current_user)):
    return service.summary()
