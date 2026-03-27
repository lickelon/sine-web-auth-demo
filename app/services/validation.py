import re

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def validate_username(username: str) -> str | None:
    if len(username) < 4:
        return "아이디는 4자 이상이어야 합니다."
    if not USERNAME_PATTERN.fullmatch(username):
        return "아이디는 영문, 숫자, 밑줄(_)만 사용할 수 있습니다."
    return None


def validate_signup_form(username: str, password: str, nickname: str) -> dict[str, str]:
    errors: dict[str, str] = {}
    username_error = validate_username(username)
    if username_error:
        errors["username"] = username_error
    if len(password) < 8:
        errors["password"] = "비밀번호는 8자 이상이어야 합니다."
    if len(nickname) < 2:
        errors["nickname"] = "닉네임은 2자 이상이어야 합니다."
    return errors


def validate_login_form(username: str, password: str) -> dict[str, str]:
    errors: dict[str, str] = {}
    username_error = validate_username(username)
    if username_error:
        errors["username"] = username_error
    if not password:
        errors["password"] = "비밀번호를 입력해 주세요."
    return errors
