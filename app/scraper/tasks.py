"""APScheduler 定时爬虫任务"""
import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import AsyncSessionLocal
from app.models.event import Event
from app.models.artist import Artist
from app.models.group import Group
from app.models.battle_report import BattleReport
from app.scraper.and8_client import And8Client

logger = logging.getLogger(__name__)


def _parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%d/%m/%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    return None


async def sync_all() -> None:
    """全量同步 and8.dance 数据"""
    logger.info("开始同步 and8.dance 数据...")
    client = And8Client()
    try:
        await _sync_events(client)
        await _sync_artists(client)
        await _sync_groups(client)
        await _sync_battle_reports(client)
    finally:
        await client.close()
    logger.info("同步完成")


async def _sync_events(client: And8Client) -> None:
    raw = await client.fetch_events()
    if not raw:
        return
    async with AsyncSessionLocal() as session:
        for item in raw:
            parsed_date = _parse_date(item.get("date_str")) or date.today()
            stmt = pg_insert(Event).values(
                source_id=item["source_id"],
                title=item["title"],
                date=parsed_date,
                poster_url=item.get("poster_url"),
                source_url=item.get("source_url"),
            ).on_conflict_do_update(
                index_elements=["source_id"],
                set_={
                    "title": item["title"],
                    "poster_url": item.get("poster_url"),
                    "source_url": item.get("source_url"),
                },
            )
            await session.execute(stmt)
        await session.commit()
    logger.info("同步赛事 %d 条", len(raw))


async def _sync_artists(client: And8Client) -> None:
    raw = await client.fetch_artists()
    if not raw:
        return
    async with AsyncSessionLocal() as session:
        for item in raw:
            stmt = pg_insert(Artist).values(
                source_id=item["source_id"],
                name=item["name"],
                avatar_url=item.get("avatar_url"),
            ).on_conflict_do_update(
                index_elements=["source_id"],
                set_={"name": item["name"], "avatar_url": item.get("avatar_url")},
            )
            await session.execute(stmt)
        await session.commit()
    logger.info("同步艺术家 %d 条", len(raw))


async def _sync_groups(client: And8Client) -> None:
    raw = await client.fetch_groups()
    if not raw:
        return
    async with AsyncSessionLocal() as session:
        for item in raw:
            stmt = pg_insert(Group).values(
                source_id=item["source_id"],
                name=item["name"],
                logo_url=item.get("logo_url"),
            ).on_conflict_do_update(
                index_elements=["source_id"],
                set_={"name": item["name"], "logo_url": item.get("logo_url")},
            )
            await session.execute(stmt)
        await session.commit()
    logger.info("同步团队 %d 条", len(raw))


async def _sync_battle_reports(client: And8Client) -> None:
    raw = await client.fetch_battle_reports()
    if not raw:
        return
    async with AsyncSessionLocal() as session:
        for item in raw:
            detail = await client.fetch_report_detail(item["source_id"])
            if not detail:
                continue
            stmt = pg_insert(BattleReport).values(
                source_id=item["source_id"],
                title=detail["title"],
                report_data=detail.get("report_data"),
            ).on_conflict_do_update(
                index_elements=["source_id"],
                set_={"title": detail["title"], "report_data": detail.get("report_data")},
            )
            await session.execute(stmt)
        await session.commit()
    logger.info("同步赛果报告 %d 条", len(raw))
