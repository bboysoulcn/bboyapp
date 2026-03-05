import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event
from app.services.ical import generate_ical

router = APIRouter(prefix="/events")
templates = Jinja2Templates(directory="app/templates")


@router.get("/calendar.ics")
async def export_ical(
    event_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if event_id:
        result = await db.execute(select(Event).where(Event.id == uuid.UUID(event_id)))
        events = result.scalars().all()
    else:
        result = await db.execute(select(Event).order_by(Event.date))
        events = result.scalars().all()

    ical_bytes = generate_ical(events)
    return Response(
        content=ical_bytes,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=bboyapp-events.ics"},
    )


@router.get("/", response_class=HTMLResponse)
async def events_list(
    request: Request,
    region: str | None = Query(None),
    level: str | None = Query(None),
    style: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Event).order_by(Event.date)
    if region:
        stmt = stmt.where(Event.region.ilike(f"%{region}%"))
    if level:
        stmt = stmt.where(Event.level == level)
    if style:
        stmt = stmt.where(Event.dance_styles.any(style))

    result = await db.execute(stmt)
    events = result.scalars().all()

    # 按年月分组
    events_by_month: dict[str, list[Event]] = defaultdict(list)
    for event in events:
        key = event.date.strftime("%Y年%m月")
        events_by_month[key].append(event)

    return templates.TemplateResponse("events/list.html", {
        "request": request,
        "events_by_month": dict(events_by_month),
        "filters": {"region": region, "level": level, "style": style},
        "active_page": "events",
    })


@router.get("/{event_id}", response_class=HTMLResponse)
async def event_detail(event_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event).where(Event.id == uuid.UUID(event_id)))
    event = result.scalar_one_or_none()
    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="赛事未找到")

    return templates.TemplateResponse("events/detail.html", {
        "request": request,
        "event": event,
        "active_page": "events",
    })
