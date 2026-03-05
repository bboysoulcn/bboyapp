"""and8.dance 数据爬取客户端"""
import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://and8.dance"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BBoyApp-Scraper/1.0)",
    "Accept-Language": "en-US,en;q=0.9",
}


class And8Client:
    def __init__(self):
        self.client = httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True)

    async def close(self):
        await self.client.aclose()

    async def _get(self, path: str) -> BeautifulSoup | None:
        try:
            resp = await self.client.get(f"{BASE_URL}{path}")
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            logger.warning("爬取失败 %s: %s", path, e)
            return None

    async def fetch_events(self) -> list[dict[str, Any]]:
        """爬取赛事列表"""
        soup = await self._get("/en/events")
        if not soup:
            return []
        events = []
        for item in soup.select("article, .event-item, [data-event-id]"):
            source_id = item.get("data-event-id") or item.get("id", "")
            title_el = item.select_one("h2, h3, .event-title, .title")
            date_el = item.select_one("time, .date, [datetime]")
            link_el = item.select_one("a[href]")
            img_el = item.select_one("img")
            if not source_id or not title_el:
                continue
            events.append({
                "source_id": str(source_id),
                "title": title_el.get_text(strip=True),
                "date_str": date_el.get("datetime") or date_el.get_text(strip=True) if date_el else None,
                "poster_url": img_el.get("src") or img_el.get("data-src") if img_el else None,
                "source_url": BASE_URL + link_el["href"] if link_el else None,
            })
        return events

    async def fetch_artists(self) -> list[dict[str, Any]]:
        """爬取艺术家列表"""
        soup = await self._get("/en/artists/")
        if not soup:
            return []
        artists = []
        for item in soup.select("[data-artist-id], .artist-card, article"):
            source_id = item.get("data-artist-id") or item.get("id", "")
            name_el = item.select_one("h2, h3, .name, .artist-name")
            img_el = item.select_one("img")
            if not source_id or not name_el:
                continue
            artists.append({
                "source_id": str(source_id),
                "name": name_el.get_text(strip=True),
                "avatar_url": img_el.get("src") if img_el else None,
            })
        return artists

    async def fetch_groups(self) -> list[dict[str, Any]]:
        """爬取团队列表"""
        soup = await self._get("/en/groups")
        if not soup:
            return []
        groups = []
        for item in soup.select("[data-group-id], .group-card, article"):
            source_id = item.get("data-group-id") or item.get("id", "")
            name_el = item.select_one("h2, h3, .name")
            img_el = item.select_one("img")
            if not source_id or not name_el:
                continue
            groups.append({
                "source_id": str(source_id),
                "name": name_el.get_text(strip=True),
                "logo_url": img_el.get("src") if img_el else None,
            })
        return groups

    async def fetch_battle_reports(self) -> list[dict[str, Any]]:
        """爬取赛果报告列表"""
        soup = await self._get("/en/stats")
        if not soup:
            return []
        reports = []
        for link in soup.select("a[href*='/stats/reports/']"):
            href = link.get("href", "")
            parts = href.strip("/").split("/")
            if "reports" in parts:
                idx = parts.index("reports")
                if idx + 1 < len(parts):
                    source_id = parts[idx + 1]
                    reports.append({
                        "source_id": source_id,
                        "title": link.get_text(strip=True),
                        "source_url": BASE_URL + href,
                    })
        # 去重
        seen = set()
        unique = []
        for r in reports:
            if r["source_id"] not in seen:
                seen.add(r["source_id"])
                unique.append(r)
        return unique

    async def fetch_report_detail(self, report_id: str) -> dict[str, Any] | None:
        """爬取单个报告详情"""
        soup = await self._get(f"/en/stats/reports/{report_id}")
        if not soup:
            return None
        title_el = soup.select_one("h1, h2, .report-title")
        return {
            "source_id": report_id,
            "title": title_el.get_text(strip=True) if title_el else f"Report {report_id}",
            "report_data": {"raw_html": soup.find("main").decode_contents() if soup.find("main") else ""},
        }
