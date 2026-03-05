from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.battle_report import BattleReport

router = APIRouter(prefix="/stats")
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def stats_list(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BattleReport).order_by(BattleReport.created_at.desc()))
    reports = result.scalars().all()

    return templates.TemplateResponse("stats/list.html", {
        "request": request,
        "reports": reports,
        "active_page": "stats",
    })


@router.get("/{report_id}", response_class=HTMLResponse)
async def stats_detail(report_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BattleReport).where(BattleReport.source_id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="报告未找到")

    return templates.TemplateResponse("stats/detail.html", {
        "request": request,
        "report": report,
        "active_page": "stats",
    })


@router.get("/{report_id}/{round_id}/review", response_class=HTMLResponse)
async def battle_review(
    report_id: str,
    round_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BattleReport).where(BattleReport.source_id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="报告未找到")

    # 从 report_data 中提取指定轮次的对战数据
    round_data = []
    if report.report_data:
        rounds = report.report_data.get("rounds", {})
        round_battles = rounds.get(round_id, [])
        round_data = round_battles

    return templates.TemplateResponse("stats/review.html", {
        "request": request,
        "report": report,
        "round_id": round_id,
        "round_data": round_data,
        "active_page": "stats",
    })
