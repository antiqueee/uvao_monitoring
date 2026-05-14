import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Network, User, UserRole


def get_current_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    user = db.get(User, uuid.UUID(user_id))
    if not user:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return user


def visible_networks(db: Session, user: User) -> list[Network]:
    stmt = select(Network).order_by(Network.name)
    if user.role != UserRole.admin:
        stmt = stmt.where(Network.id == user.network_id)
    return list(db.scalars(stmt))


def ensure_network_access(network_id: uuid.UUID, user: User) -> None:
    if user.role == UserRole.admin:
        return
    if user.network_id != network_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой сетке")
