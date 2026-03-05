import uuid

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.artist import Artist

router = APIRouter(prefix="/artists")
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def artists_list(
    request: Request,
    q: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Artist).order_by(Artist.name)
    if q:
        stmt = stmt.where(
            Artist.name.ilike(f"%{q}%") | Artist.nickname.ilike(f"%{q}%")
        )
    result = await db.execute(stmt)
    artists = result.scalars().all()

    return templates.TemplateResponse("artists/list.html", {
        "request": request,
        "artists": artists,
        "query": q,
        "active_page": "artists",
    })


@router.get("/{artist_id}", response_class=HTMLResponse)
async def artist_detail(artist_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Artist).where(Artist.id == uuid.UUID(artist_id)))
    artist = result.scalar_one_or_none()
    if not artist:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="艺术家未找到")

    return templates.TemplateResponse("artists/detail.html", {
        "request": request,
        "artist": artist,
        "active_page": "artists",
    })
