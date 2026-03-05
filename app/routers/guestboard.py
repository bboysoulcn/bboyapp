import random
import string
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.guestbook import GuestbookMessage
from app.services.email import send_pin_email

router = APIRouter(prefix="/guestboard")
templates = Jinja2Templates(directory="app/templates")


def _gen_pin() -> str:
    return "".join(random.choices(string.digits, k=6))


@router.get("/", response_class=HTMLResponse)
async def guestboard(
    request: Request,
    pending: str | None = Query(None),
    success: bool = Query(False),
    error: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    msgs_result = await db.execute(
        select(GuestbookMessage)
        .where(GuestbookMessage.is_visible == True)  # noqa: E712
        .order_by(GuestbookMessage.created_at.desc())
    )
    messages = msgs_result.scalars().all()

    count_result = await db.execute(
        select(func.count()).where(GuestbookMessage.is_visible == True)  # noqa: E712
    )
    total = count_result.scalar_one()

    return templates.TemplateResponse("guestboard.html", {
        "request": request,
        "messages": messages,
        "total": total,
        "pending_id": pending,
        "success": success,
        "error": error,
        "active_page": "guestboard",
    })


@router.post("/submit")
async def submit_message(
    nickname: str = Form(...),
    email: str = Form(...),
    content: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    pin = _gen_pin()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    msg = GuestbookMessage(
        nickname=nickname.strip(),
        email=email.strip().lower(),
        content=content.strip(),
        pin_code=pin,
        pin_expires_at=expires_at,
        email_verified=False,
        is_visible=False,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    try:
        send_pin_email(email, nickname, pin)
    except Exception:
        pass  # 邮件发送失败不阻塞流程，用户可重新提交

    return RedirectResponse(f"/guestboard/?pending={msg.id}", status_code=303)


@router.post("/verify")
async def verify_pin(
    message_id: str = Form(...),
    pin: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GuestbookMessage).where(GuestbookMessage.id == uuid.UUID(message_id))
    )
    msg = result.scalar_one_or_none()

    if not msg:
        return RedirectResponse("/guestboard/?error=留言不存在", status_code=303)

    now = datetime.now(timezone.utc)
    if msg.pin_expires_at and now > msg.pin_expires_at:
        return RedirectResponse("/guestboard/?error=验证码已过期，请重新提交留言", status_code=303)

    if msg.pin_code != pin.strip():
        return RedirectResponse(f"/guestboard/?pending={message_id}&error=验证码错误", status_code=303)

    msg.email_verified = True
    msg.is_visible = True
    msg.pin_code = None
    await db.commit()

    return RedirectResponse("/guestboard/?success=true", status_code=303)
