import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.group import Group

router = APIRouter(prefix="/groups")
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def groups_list(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Group).order_by(Group.name))
    groups = result.scalars().all()

    return templates.TemplateResponse("groups/list.html", {
        "request": request,
        "groups": groups,
        "active_page": "groups",
    })


@router.get("/{group_id}", response_class=HTMLResponse)
async def group_detail(group_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Group).where(Group.id == uuid.UUID(group_id)))
    group = result.scalar_one_or_none()
    if not group:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="团队未找到")

    return templates.TemplateResponse("groups/detail.html", {
        "request": request,
        "group": group,
        "active_page": "groups",
    })
