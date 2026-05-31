import uuid
from datetime import datetime
from urllib.parse import quote
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db import get_db
from app.deps import ensure_network_access, get_current_user, visible_networks
from app.models import Report, ReportRow, ReportStatus, User, UserRole
from app.services.excel_export import build_report_workbook
from app.services.repost_finder import find_reposts
from app.services.url_parser import InvalidVkPostUrl, parse_vk_post_url

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def export_content_disposition(filename: str) -> str:
    ascii_filename = filename.encode("ascii", "ignore").decode("ascii").replace('"', "")
    ascii_filename = ascii_filename or "report.xlsx"
    quoted_filename = quote(filename)
    return f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{quoted_filename}"


@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> HTMLResponse:
    stmt = (
        select(Report)
        .options(joinedload(Report.network))
        .order_by(desc(Report.created_at))
        .limit(20)
    )
    if user.role != UserRole.admin:
        stmt = stmt.where(Report.network_id == user.network_id)
    reports = list(db.scalars(stmt))
    return templates.TemplateResponse(
        request, "dashboard.html", {"user": user, "reports": reports}
    )


@router.get("/reports/new", response_class=HTMLResponse)
def new_report_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "reports/new.html",
        {"user": user, "networks": visible_networks(db, user)},
    )


@router.post("/reports")
def create_report(
    background_tasks: BackgroundTasks,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    source_url: Annotated[str, Form()],
    network_id: Annotated[str, Form()],
    infopovod_title: Annotated[str, Form()],
) -> Response:
    try:
        owner_id, post_id = parse_vk_post_url(source_url)
    except InvalidVkPostUrl as exc:
        networks = visible_networks(db, user)
        return templates.TemplateResponse(
            request,
            "reports/new.html",
            {
                "user": user,
                "networks": networks,
                "error": str(exc),
                "source_url": source_url,
                "infopovod_title": infopovod_title,
                "selected_network_id": network_id,
            },
            status_code=400,
        )

    if network_id == "all":
        if user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        networks = visible_networks(db, user)
    else:
        try:
            selected_network_id = uuid.UUID(network_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Некорректная сетка") from exc
        ensure_network_access(selected_network_id, user)
        networks = visible_networks(db, user)
        networks = [network for network in networks if network.id == selected_network_id]

    if not networks:
        raise HTTPException(status_code=404, detail="Сетка не найдена")

    reports = [
        Report(
            created_by=user.id,
            network_id=network.id,
            source_url=source_url.strip(),
            source_owner_id=owner_id,
            source_post_id=post_id,
            infopovod_title=infopovod_title.strip()[:512],
            status=ReportStatus.pending,
        )
        for network in networks
    ]
    db.add_all(reports)
    db.commit()
    for report in reports:
        background_tasks.add_task(find_reposts, report.id)

    if len(reports) > 1:
        return RedirectResponse("/", status_code=303)
    return RedirectResponse(f"/reports/{reports[0].id}", status_code=303)


@router.get("/reports/{report_id}", response_class=HTMLResponse)
def report_page(
    report_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> HTMLResponse:
    report = db.scalar(
        select(Report)
        .options(joinedload(Report.network), selectinload(Report.rows).joinedload(ReportRow.resource))
        .where(Report.id == report_id)
    )
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    ensure_network_access(report.network_id, user)
    return templates.TemplateResponse(
        request, "reports/detail.html", {"user": user, "report": report}
    )


@router.get("/reports/{report_id}/status")
def report_status(
    report_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    ensure_network_access(report.network_id, user)
    return JSONResponse({"status": report.status.value, "error": report.error_message})


@router.get("/reports/{report_id}/export.xlsx")
def export_report(
    report_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    report = db.scalar(
        select(Report)
        .options(joinedload(Report.network), selectinload(Report.rows).joinedload(ReportRow.resource))
        .where(Report.id == report_id)
    )
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    ensure_network_access(report.network_id, user)
    output = build_report_workbook(report)
    network_name = report.network.name.replace(" ", "_")
    created = (report.finished_at or datetime.now()).strftime("%Y%m%d_%H%M")
    filename = f"report_{network_name}_{created}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": export_content_disposition(filename)},
    )
