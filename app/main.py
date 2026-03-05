"""BBoyApp FastAPI 主入口"""
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import home, events, artists, groups, guestboard, stats
from app.scraper.tasks import sync_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化调度器
    scheduler.add_job(
        sync_all,
        "interval",
        hours=settings.scraper_interval_hours,
        id="sync_and8",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("爬虫调度器已启动，间隔 %d 小时", settings.scraper_interval_hours)
    yield
    scheduler.shutdown()
    logger.info("调度器已关闭")


app = FastAPI(
    title=settings.app_name,
    description="街舞社区网站",
    version="1.0.0",
    lifespan=lifespan,
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 注册路由
app.include_router(home.router)
app.include_router(events.router)
app.include_router(artists.router)
app.include_router(groups.router)
app.include_router(guestboard.router)
app.include_router(stats.router)
