from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse

router = APIRouter(include_in_schema=False)


@router.get("/")
def index(request: Request):
    destination = "/profile" if request.session.get("user_id") else "/login"
    return RedirectResponse(url=destination, status_code=status.HTTP_303_SEE_OTHER)
