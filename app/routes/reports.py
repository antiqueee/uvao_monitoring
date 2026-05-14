import uuid
from datetime import datetime
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
        "dashboard.html", {"request": request, "user": user, "reports": reports}
    )


@router.get("/reports/new", response_class=HTMLResponse)
def new_report_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> HTMLResponse:
    return templates.TemplateResponse(
        "reports/new.html",
        {"request": request, "user": user, "networks": visible_networks(db, user)},
    )


@router.post("/reports")
def create_report(
    background_tasks: BackgroundTasks,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    source_url: Annotated[str, Form()],
    network_id: Annotated[uuid.UUID, Form()],
    infopovod_title: Annotated[str, Form()],
) -> Response:
    ensure_network_access(network_id, user)
    try:
        owner_id, post_id = parse_vk_post_url(source_url)
    except InvalidVkPostUrl as exc:
        networks = visible_networks(db, user)
        return templates.TemplateResponse(
            "reports/new.html",
            {
                "request": request,
                "user": user,
                "networks": networks,
                "error": str(exc),
                "source_url": source_url,
                "infopovod_title": infopovod_title,
            },
            status_code=400,
        )

    report = Report(
        created_by=user.id,
        network_id=network_id,
        source_url=source_url.strip(),
        source_owner_id=owner_id,
        source_post_id=post_id,
        infopovod_title=infopovod_title.strip()[:512],
        status=ReportStatus.pending,
    )
    db.add(report)
    db.commit()
    background_tasks.add_task(find_reposts, report.id)
    return RedirectResponse(f"/reports/{report.id}", status_code=303)


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
        "reports/detail.html", {"request": request, "user": user, "report": report}
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
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
