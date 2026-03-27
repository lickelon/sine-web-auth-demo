from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.api import (
    LoginRequest,
    MessageResponse,
    ProfileResponse,
    SignupRequest,
    UserResponse,
)
from app.services.auth import AuthService, DuplicateUsernameError, InvalidCredentialsError
from app.services.validation import validate_login_form, validate_signup_form

router = APIRouter(prefix="/api")
auth_service = AuthService()


def _resolve_current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
        )

    user = auth_service.get_user_by_id(db=db, user_id=user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효한 세션이 아닙니다.",
        )
    return user


@router.post(
    "/signup",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    normalized_username = payload.username.strip()
    normalized_nickname = payload.nickname.strip()
    errors = validate_signup_form(
        normalized_username,
        payload.password,
        normalized_nickname,
    )
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors,
        )

    try:
        auth_service.register_user(
            db=db,
            username=normalized_username,
            password=payload.password,
            nickname=normalized_nickname,
        )
    except DuplicateUsernameError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 아이디입니다.",
        ) from None

    return MessageResponse(message="회원가입이 완료되었습니다.")


@router.post("/login", response_model=ProfileResponse, tags=["auth"])
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    normalized_username = payload.username.strip()
    errors = validate_login_form(normalized_username, payload.password)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors,
        )

    try:
        user = auth_service.authenticate_user(
            db=db,
            username=normalized_username,
            password=payload.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다.",
        ) from None

    request.session["user_id"] = user.id
    return ProfileResponse(
        message="로그인되었습니다.",
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse, tags=["auth"])
def logout(request: Request):
    request.session.clear()
    return MessageResponse(message="로그아웃되었습니다.")


@router.get("/profile", response_model=ProfileResponse, tags=["profile"])
def profile(request: Request, db: Session = Depends(get_db)):
    user = _resolve_current_user(request, db)
    return ProfileResponse(
        message="프로필 조회 성공",
        user=UserResponse.model_validate(user),
    )
