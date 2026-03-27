from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import render_template
from app.services.auth import AuthService, DuplicateUsernameError, InvalidCredentialsError
from app.services.validation import (
    validate_login_form,
    validate_signup_form,
    validate_username,
)

router = APIRouter(include_in_schema=False)
auth_service = AuthService()


def _is_authenticated(request: Request) -> bool:
    return bool(request.session.get("user_id"))


def _redirect_to_profile() -> RedirectResponse:
    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)


def _is_htmx_request(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def _htmx_redirect(url: str) -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.headers["HX-Redirect"] = url
    return response


def _render_auth_response(
    request: Request,
    page_template: str,
    partial_template: str,
    context: dict,
    status_code: int = 200,
):
    is_htmx_request = _is_htmx_request(request)
    template_name = partial_template if is_htmx_request else page_template
    response_status_code = 200 if is_htmx_request and status_code >= 400 else status_code
    return render_template(request, template_name, context, status_code=response_status_code)


def _signup_context(
    username: str = "",
    nickname: str = "",
    errors: dict[str, str] | None = None,
    username_feedback: dict[str, str] | None = None,
):
    resolved_errors = errors or {}
    resolved_feedback = username_feedback or _default_username_feedback()
    if resolved_errors.get("username"):
        resolved_feedback = {
            "tone": "error",
            "message": resolved_errors["username"],
        }
    return {
        "page_title": "회원가입",
        "form": {
            "username": username,
            "nickname": nickname,
        },
        "errors": resolved_errors,
        "username_feedback": resolved_feedback,
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


def _default_username_feedback() -> dict[str, str]:
    return {
        "tone": "muted",
        "message": "영문, 숫자, 밑줄(_) 4자 이상으로 입력해 주세요.",
    }


@router.get("/signup")
def signup_page(request: Request):
    if _is_authenticated(request):
        return _redirect_to_profile()
    return render_template(request, "signup.html", _signup_context())


@router.get("/signup/username-check")
def signup_username_check(
    request: Request,
    username: str = "",
    db: Session = Depends(get_db),
):
    normalized_username = username.strip()
    feedback = _default_username_feedback()

    if normalized_username:
        username_error = validate_username(normalized_username)
        if username_error:
            feedback = {
                "tone": "error",
                "message": username_error,
            }
        elif auth_service.is_username_available(db=db, username=normalized_username):
            feedback = {
                "tone": "success",
                "message": "사용 가능한 아이디입니다.",
            }
        else:
            feedback = {
                "tone": "error",
                "message": "이미 사용 중인 아이디입니다.",
            }

    return render_template(
        request,
        "includes/username_feedback.html",
        {"username_feedback": feedback},
    )


@router.post("/signup")
def signup(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    nickname: str = Form(""),
    db: Session = Depends(get_db),
):
    if _is_authenticated(request):
        if _is_htmx_request(request):
            return _htmx_redirect("/profile")
        return _redirect_to_profile()

    normalized_username = username.strip()
    normalized_nickname = nickname.strip()
    errors = validate_signup_form(normalized_username, password, normalized_nickname)
    if errors:
        return _render_auth_response(
            request,
            "signup.html",
            "includes/signup_form.html",
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
        return _render_auth_response(
            request,
            "signup.html",
            "includes/signup_form.html",
            _signup_context(
                username=normalized_username,
                nickname=normalized_nickname,
                errors={"username": "이미 사용 중인 아이디입니다."},
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if _is_htmx_request(request):
        return _htmx_redirect("/login?registered=1")
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
        if _is_htmx_request(request):
            return _htmx_redirect("/profile")
        return _redirect_to_profile()

    normalized_username = username.strip()
    errors = validate_login_form(normalized_username, password)
    if errors:
        return _render_auth_response(
            request,
            "login.html",
            "includes/login_form.html",
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
        return _render_auth_response(
            request,
            "login.html",
            "includes/login_form.html",
            _login_context(
                username=normalized_username,
                errors={"form": "아이디 또는 비밀번호가 올바르지 않습니다."},
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    request.session["user_id"] = user.id
    if _is_htmx_request(request):
        return _htmx_redirect("/profile")
    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(
        url="/login?logged_out=1",
        status_code=status.HTTP_303_SEE_OTHER,
    )
