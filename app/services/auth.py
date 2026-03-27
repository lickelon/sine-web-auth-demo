from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User

password_hash = PasswordHash.recommended()


class DuplicateUsernameError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
    pass


class AuthService:
    def is_username_available(self, db: Session, username: str) -> bool:
        existing_user = db.scalar(select(User).where(User.username == username))
        return existing_user is None

    def register_user(
        self,
        db: Session,
        username: str,
        password: str,
        nickname: str,
    ) -> User:
        existing_user = db.scalar(select(User).where(User.username == username))
        if existing_user is not None:
            raise DuplicateUsernameError

        user = User(
            username=username,
            nickname=nickname,
            password_hash=password_hash.hash(password),
        )
        db.add(user)

        try:
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise DuplicateUsernameError from error

        db.refresh(user)
        return user

    def authenticate_user(self, db: Session, username: str, password: str) -> User:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            raise InvalidCredentialsError
        if not password_hash.verify(password, user.password_hash):
            raise InvalidCredentialsError
        return user

    def get_user_by_id(self, db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)
