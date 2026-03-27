from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import render_template
from app.services.auth import AuthService, DuplicateUsernameError, InvalidCredentialsError
from app.services.validation import validate_login_form, validate_signup_form

router = APIRouter(include_in_schema=False)
auth_service = AuthService()


def _is_authenticated(request: Request) -> bool:
    return bool(request.session.get("user_id"))


def _redirect_to_profile() -> RedirectResponse:
    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)


def _signup_context(
    username: str = "",
    nickname: str = "",
    errors: dict[str, str] | None = None,
):
    return {
        "page_title": "회원가입",
        "form": {
            "username": username,
            "nickname": nickname,
        },
        "errors": errors or {},
    }


def _login_context(
    username: str = "",
    errors: dict[str, str] | None = None,
    message: str | None = None,
):
    return {
        "page_title": "로그인",
        "form": {
            "username": username,
        },
        "errors": errors or {},
        "message": message,
    }


@router.get("/signup")
def signup_page(request: Request):
    if _is_authenticated(request):
        return _redirect_to_profile()
    return render_template(request, "signup.html", _signup_context())


@router.post("/signup")
def signup(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    nickname: str = Form(""),
    db: Session = Depends(get_db),
):
    if _is_authenticated(request):
        return _redirect_to_profile()

    normalized_username = username.strip()
    normalized_nickname = nickname.strip()
    errors = validate_signup_form(normalized_username, password, normalized_nickname)
    if errors:
        return render_template(
            request,
            "signup.html",
            _signup_context(
                username=normalized_username,
                nickname=normalized_nickname,
                errors=errors,
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        auth_service.register_user(
            db=db,
            username=normalized_username,
            password=password,
            nickname=normalized_nickname,
        )
    except DuplicateUsernameError:
        return render_template(
            request,
            "signup.html",
            _signup_context(
                username=normalized_username,
                nickname=normalized_nickname,
                errors={"username": "이미 사용 중인 아이디입니다."},
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(url="/login?registered=1", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
def login_page(request: Request):
    if _is_authenticated(request):
        return _redirect_to_profile()

    message = None
    if request.query_params.get("registered") == "1":
        message = "회원가입이 완료되었습니다. 로그인해 주세요."
    if request.query_params.get("logged_out") == "1":
        message = "로그아웃되었습니다."
    return render_template(request, "login.html", _login_context(message=message))


@router.post("/login")
def login(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    db: Session = Depends(get_db),
):
    if _is_authenticated(request):
        return _redirect_to_profile()

    normalized_username = username.strip()
    errors = validate_login_form(normalized_username, password)
    if errors:
        return render_template(
            request,
            "login.html",
            _login_context(username=normalized_username, errors=errors),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = auth_service.authenticate_user(
            db=db,
            username=normalized_username,
            password=password,
        )
    except InvalidCredentialsError:
        return render_template(
            request,
            "login.html",
            _login_context(
                username=normalized_username,
                errors={"form": "아이디 또는 비밀번호가 올바르지 않습니다."},
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    request.session["user_id"] = user.id
    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(
        url="/login?logged_out=1",
        status_code=status.HTTP_303_SEE_OTHER,
    )
