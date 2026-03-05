from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event
from app.models.artist import Artist

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    from datetime import date
    events_result = await db.execute(
        select(Event).where(Event.date >= date.today()).order_by(Event.date).limit(6)
    )
    events = events_result.scalars().all()

    artists_result = await db.execute(select(Artist).limit(12))
    artists = artists_result.scalars().all()

    return templates.TemplateResponse("home.html", {
        "request": request,
        "events": events,
        "artists": artists,
        "active_page": "home",
    })
