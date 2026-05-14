import asyncio
import uuid
from datetime import timedelta

from sqlalchemy import delete, select

from app.db import SessionLocal
from app.models import Report, ReportRow, ReportStatus, Resource
from app.services.vk_client import VkApiError, VkClient, vk_ts_to_dt


async def find_reposts(report_id: uuid.UUID) -> None:
    client = VkClient()
    with SessionLocal() as db:
        report = db.get(Report, report_id)
        if not report:
            return
        report.status = ReportStatus.running
        report.error_message = None
        db.execute(delete(ReportRow).where(ReportRow.report_id == report.id))
        db.commit()

        try:
            source = await client.wall_get_by_id(report.source_owner_id, report.source_post_id)
            report.source_date = vk_ts_to_dt(source["date"])
            window_end = report.source_date + timedelta(days=8)
            resources = list(
                db.scalars(
                    select(Resource)
                    .where(Resource.network_id == report.network_id, Resource.is_active.is_(True))
                    .order_by(Resource.created_at)
                )
            )
            row_number = 1
            for resource in resources:
                try:
                    posts = await client.wall_get(resource.vk_owner_id)
                except VkApiError as exc:
                    if exc.code in {15, 30}:
                        continue
                    raise

                for post in posts:
                    post_date = vk_ts_to_dt(post["date"])
                    if post_date < report.source_date:
                        break
                    if post_date > window_end:
                        continue
                    copy_history = post.get("copy_history") or []
                    if not any(
                        item.get("owner_id") == report.source_owner_id
                        and item.get("id") == report.source_post_id
                        for item in copy_history
                    ):
                        continue

                    followers_count = await fetch_followers(client, resource)
                    db.add(
                        ReportRow(
                            report_id=report.id,
                            resource_id=resource.id,
                            repost_owner_id=post.get("owner_id", resource.vk_owner_id),
                            repost_post_id=post["id"],
                            repost_url=f"https://vk.com/wall{post.get('owner_id', resource.vk_owner_id)}_{post['id']}",
                            repost_date=post_date,
                            followers_count=followers_count,
                            views_count=(post.get("views") or {}).get("count"),
                            row_number=row_number,
                        )
                    )
                    row_number += 1
                    break

                await asyncio.sleep(0.34)

            report.status = ReportStatus.done
        except VkApiError as exc:
            report.status = ReportStatus.failed
            if exc.code == 14:
                report.error_message = "ВК запросил капчу, обратитесь к администратору"
            elif exc.code == 5:
                report.error_message = "VK-токен невалиден или не задан"
            else:
                report.error_message = str(exc)
        except Exception as exc:
            report.status = ReportStatus.failed
            report.error_message = str(exc)
        finally:
            from datetime import datetime, timezone

            report.finished_at = datetime.now(timezone.utc)
            db.commit()


async def fetch_followers(client: VkClient, resource: Resource) -> int:
    if resource.vk_owner_id < 0:
        info = await client.group_info(resource.vk_owner_id)
        if info.get("name"):
            resource.display_name = info["name"]
        return int(info.get("members_count") or 0)
    info = await client.user_info(resource.vk_owner_id)
    full_name = " ".join(part for part in [info.get("first_name"), info.get("last_name")] if part)
    if full_name:
        resource.display_name = full_name
    return int(info.get("followers_count") or 0)
