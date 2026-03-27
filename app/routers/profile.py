from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.time import format_datetime_for_seoul
from app.core.templates import render_template
from app.services.auth import AuthService

router = APIRouter(include_in_schema=False)
auth_service = AuthService()


@router.get("/profile")
def profile_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    user = auth_service.get_user_by_id(db=db, user_id=user_id)
    if user is None:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    return render_template(
        request,
        "profile.html",
        {
            "page_title": "프로필",
            "user": user,
            "created_at_display": format_datetime_for_seoul(user.created_at),
        },
    )
