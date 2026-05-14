import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import ensure_network_access, get_current_user, visible_networks
from app.models import Network, Resource, ResourceType, User, UserRole
from app.security import hash_password
from app.services.vk_client import VkApiError, VkClient

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


@router.get("/networks", response_class=HTMLResponse)
def networks_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "admin/networks.html",
        {"user": user, "networks": visible_networks(db, user)},
    )


@router.get("/networks/{network_id}", response_class=HTMLResponse)
def network_detail(
    network_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> HTMLResponse:
    ensure_network_access(network_id, user)
    network = db.scalar(
        select(Network).options(selectinload(Network.resources)).where(Network.id == network_id)
    )
    if not network:
        raise HTTPException(status_code=404, detail="Сетка не найдена")
    return templates.TemplateResponse(
        request,
        "admin/network_detail.html",
        {
            "user": user,
            "network": network,
            "resource_types": list(ResourceType),
        },
    )


@router.post("/networks/{network_id}/resources")
async def add_resource(
    network_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    screen_name: Annotated[str, Form()],
    display_name: Annotated[str, Form()] = "",
    resource_type: Annotated[ResourceType, Form()] = ResourceType.district_community,
    category_label: Annotated[str, Form()] = "",
    is_active: Annotated[str | None, Form()] = None,
) -> Response:
    ensure_network_access(network_id, user)
    clean_screen_name = screen_name.strip().removeprefix("https://vk.com/").removeprefix("vk.com/")
    try:
        resolved = await VkClient().resolve_screen_name(clean_screen_name)
        object_id = int(resolved["object_id"])
        vk_owner_id = -object_id if resolved["type"] in {"group", "page"} else object_id
    except (VkApiError, KeyError, ValueError) as exc:
        return await _network_form_with_error(request, db, user, network_id, f"Не удалось проверить ВК: {exc}")

    resource = Resource(
        network_id=network_id,
        vk_owner_id=vk_owner_id,
        vk_screen_name=clean_screen_name,
        display_name=display_name.strip() or clean_screen_name,
        resource_type=resource_type,
        category_label=category_label.strip() or None,
        is_active=is_active == "on",
    )
    db.add(resource)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return await _network_form_with_error(request, db, user, network_id, "Этот ресурс уже есть в сетке")
    return RedirectResponse(f"/admin/networks/{network_id}", status_code=303)


@router.post("/resources/{resource_id}/delete")
def delete_resource(
    resource_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> RedirectResponse:
    resource = db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Ресурс не найден")
    ensure_network_access(resource.network_id, user)
    network_id = resource.network_id
    db.delete(resource)
    db.commit()
    return RedirectResponse(f"/admin/networks/{network_id}", status_code=303)


@router.get("/users", response_class=HTMLResponse)
def users_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> HTMLResponse:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    users = list(db.scalars(select(User).options(selectinload(User.network)).order_by(User.login)))
    networks = list(db.scalars(select(Network).order_by(Network.name)))
    return templates.TemplateResponse(
        request, "admin/users.html", {"user": user, "users": users, "networks": networks}
    )


@router.post("/users")
def create_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    login: Annotated[str, Form()],
    password: Annotated[str, Form()],
    display_name: Annotated[str, Form()],
    role: Annotated[UserRole, Form()],
    network_id: Annotated[uuid.UUID | None, Form()] = None,
) -> Response:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    new_user = User(
        login=login.strip(),
        password_hash=hash_password(password),
        display_name=display_name.strip(),
        role=role,
        network_id=network_id if role == UserRole.user else None,
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        users = list(db.scalars(select(User).options(selectinload(User.network)).order_by(User.login)))
        networks = list(db.scalars(select(Network).order_by(Network.name)))
        return templates.TemplateResponse(
            request,
            "admin/users.html",
            {
                "user": user,
                "users": users,
                "networks": networks,
                "error": "Пользователь с таким логином уже существует",
            },
            status_code=400,
        )
    return RedirectResponse("/admin/users", status_code=303)


async def _network_form_with_error(
    request: Request, db: Session, user: User, network_id: uuid.UUID, error: str
) -> HTMLResponse:
    network = db.scalar(
        select(Network).options(selectinload(Network.resources)).where(Network.id == network_id)
    )
    return templates.TemplateResponse(
        request,
        "admin/network_detail.html",
        {
            "user": user,
            "network": network,
            "resource_types": list(ResourceType),
            "error": error,
        },
        status_code=400,
    )
