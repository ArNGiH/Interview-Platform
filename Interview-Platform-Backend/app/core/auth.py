from datetime import datetime

from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.user import User


def _is_opaque_google_subject(value: str | None):
    if not value:
        return True

    stripped_value = value.strip()

    return (
        not stripped_value
        or stripped_value.isdigit()
        or stripped_value.startswith("accounts.google.com:")
    )


def _display_name_from_email(email: str):
    username = email.split("@")[0]
    normalized = username.replace(".", " ").replace("_", " ").strip()

    return normalized.title() if normalized else email


def _resolve_display_name(
    email: str,
    *candidates: str | None
):
    for candidate in candidates:
        if not candidate:
            continue

        display_name = candidate.strip()

        if (
            display_name
            and display_name.lower() != email.lower()
            and not _is_opaque_google_subject(display_name)
        ):
            return display_name

    return _display_name_from_email(email)


class CurrentUser:

    def __init__(
        self,
        id,
        email: str,
        name: str | None = None,
        picture_url: str | None = None,
    ):

        self.id = id
        self.email = email
        self.name = name
        self.picture_url = picture_url


def get_current_user(
    db: Session = Depends(get_db),
    x_forwarded_email: str | None = Header(
        default=None,
        include_in_schema=False
    ),

    x_forwarded_user: str | None = Header(
        default=None,
        include_in_schema=False
    ),

    x_forwarded_name: str | None = Header(
        default=None,
        include_in_schema=False
    ),

    x_forwarded_preferred_username: str | None = Header(
        default=None,
        include_in_schema=False
    ),

    x_forwarded_picture: str | None = Header(
        default=None,
        include_in_schema=False
    ),

    x_auth_request_picture: str | None = Header(
        default=None,
        include_in_schema=False
    )
):

    if not x_forwarded_email:

        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    email = x_forwarded_email.strip().lower()
    name = _resolve_display_name(
        email,
        x_forwarded_name,
        x_forwarded_preferred_username,
        x_forwarded_user
    )
    picture_url = (
        x_forwarded_picture
        or x_auth_request_picture
    )

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user:
        user.name = name or user.name
        user.picture_url = picture_url or user.picture_url
        user.updated_at = datetime.utcnow()
    else:
        user = User(
            email=email,
            name=name,
            picture_url=picture_url,
            updated_at=datetime.utcnow()
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    return CurrentUser(
        id=user.id,
        email=user.email,
        name=user.name,
        picture_url=user.picture_url
    )
