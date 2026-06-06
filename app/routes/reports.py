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
from app.deps import ensure_network_access, get_current_user, require_admin, visible_networks
from app.models import Report, ReportRow, ReportStatus, User, UserRole
from app.services.excel_export import build_batch_workbook, build_report_workbook
from app.services.repost_finder import find_reposts
from app.services.url_parser import InvalidVkPostUrl, parse_vk_post_url

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def parse_source_posts(source_url: str, source_urls: str, fallback_title: str) -> list[dict[str, str]]:
    raw_lines = [line.strip() for line in source_urls.splitlines() if line.strip()]
    if not raw_lines and source_url.strip():
        raw_lines = [source_url.strip()]
    posts: list[dict[str, str]] = []
    for line in raw_lines:
        url, _, title = line.partition("|")
        posts.append({"url": url.strip(), "title": (title.strip() or fallback_title.strip())[:512]})
    if not posts:
        raise InvalidVkPostUrl("укажите ссылку на пост ВК")
    return posts


def export_content_disposition(filename: str) -> str:
    ascii_filename = filename.encode("ascii", "ignore").decode("ascii").replace('"', "")
    ascii_filename = ascii_filename or "report.xlsx"
    quoted_filename = quote(filename)
    return f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{quoted_filename}"


def batch_status(reports: list[Report]) -> ReportStatus:
    if any(report.status in {ReportStatus.pending, ReportStatus.running} for report in reports):
        return ReportStatus.running
    if any(report.status == ReportStatus.failed for report in reports):
        return ReportStatus.failed
    return ReportStatus.done


def _load_batch_reports(db: Session, batch_id: uuid.UUID) -> list[Report]:
    return list(
        db.scalars(
            select(Report)
            .options(
                joinedload(Report.network),
                selectinload(Report.rows).joinedload(ReportRow.resource),
            )
            .where(Report.batch_id == batch_id)
            .order_by(Report.created_at)
        )
    )


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
    )
    if user.role != UserRole.admin:
        stmt = stmt.where(Report.network_id == user.network_id).limit(20)
    reports = list(db.scalars(stmt))
    dashboard_items: list[dict[str, object]] = []
    seen_batch_ids: set[uuid.UUID] = set()
    for report in reports:
        if user.role == UserRole.admin and report.batch_id:
            if report.batch_id in seen_batch_ids:
                continue
            seen_batch_ids.add(report.batch_id)
            batch_reports = [item for item in reports if item.batch_id == report.batch_id]
            dashboard_items.append(
                {
                    "url": f"/report-batches/{report.batch_id}",
                    "created_at": report.created_at,
                    "title": report.infopovod_title,
                    "network_name": "Все районы",
                    "status": batch_status(batch_reports),
                }
            )
        else:
            dashboard_items.append(
                {
                    "url": f"/reports/{report.id}",
                    "created_at": report.created_at,
                    "title": report.infopovod_title,
                    "network_name": report.network.name,
                    "status": report.status,
                }
            )
        if len(dashboard_items) == 20:
            break
    return templates.TemplateResponse(
        request, "dashboard.html", {"user": user, "items": dashboard_items}
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
    source_urls: Annotated[str, Form()] = "",
) -> Response:
    if source_urls.strip() and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    try:
        source_posts = parse_source_posts(source_url, source_urls, infopovod_title)
        for post in source_posts:
            owner_id, post_id = parse_vk_post_url(post["url"])
            post["owner_id"] = str(owner_id)
            post["post_id"] = str(post_id)
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
                "source_urls": source_urls,
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

    reports: list[Report] = []
    batch_ids: list[uuid.UUID] = []
    for source_post in source_posts:
        batch_id = uuid.uuid4() if len(networks) > 1 else None
        if batch_id:
            batch_ids.append(batch_id)
        reports.extend(
            Report(
                created_by=user.id,
                network_id=network.id,
                batch_id=batch_id,
                source_url=source_post["url"],
                source_owner_id=int(source_post["owner_id"]),
                source_post_id=int(source_post["post_id"]),
                infopovod_title=source_post["title"],
                status=ReportStatus.pending,
            )
            for network in networks
        )
    db.add_all(reports)
    db.commit()
    for report in reports:
        background_tasks.add_task(find_reposts, report.id)

    if len(batch_ids) == 1:
        return RedirectResponse(f"/report-batches/{batch_ids[0]}", status_code=303)
    if len(batch_ids) > 1:
        return RedirectResponse("/", status_code=303)
    return RedirectResponse(f"/reports/{reports[0].id}", status_code=303)


@router.get("/report-batches/{batch_id}", response_class=HTMLResponse)
def batch_report_page(
    batch_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_admin)],
) -> HTMLResponse:
    reports = _load_batch_reports(db, batch_id)
    if not reports:
        raise HTTPException(status_code=404, detail="Сводный отчёт не найден")
    return templates.TemplateResponse(
        request,
        "reports/batch_detail.html",
        {"user": user, "reports": reports, "batch_id": batch_id, "status": batch_status(reports)},
    )


@router.get("/report-batches/{batch_id}/status")
def batch_report_status(
    batch_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_admin)],
) -> JSONResponse:
    reports = _load_batch_reports(db, batch_id)
    if not reports:
        raise HTTPException(status_code=404, detail="Сводный отчёт не найден")
    return JSONResponse({"status": batch_status(reports).value})


@router.get("/report-batches/{batch_id}/export.xlsx")
def export_batch_report(
    batch_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_admin)],
) -> StreamingResponse:
    reports = _load_batch_reports(db, batch_id)
    if not reports:
        raise HTTPException(status_code=404, detail="Сводный отчёт не найден")
    if batch_status(reports) == ReportStatus.running:
        raise HTTPException(status_code=409, detail="Сводный отчёт ещё формируется")
    output = build_batch_workbook(reports)
    created = max(report.finished_at or datetime.now() for report in reports).strftime("%Y%m%d_%H%M")
    filename = f"report_all_districts_{created}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": export_content_disposition(filename)},
    )


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
