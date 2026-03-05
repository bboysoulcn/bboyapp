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
        """爬取赛事列表（来自 /en/events/overview 的 tr.d_list 行）"""
        soup = await self._get("/en/events/overview")
        if not soup:
            return []
        events = []
        for row in soup.select("tr.d_list"):
            link_el = row.select_one("td:nth-child(2) a[href]")
            if not link_el:
                continue
            href = link_el.get("href", "")
            # href 格式：en/e/5360
            parts = href.strip("/").split("/")
            source_id = parts[-1] if parts else None
            if not source_id:
                continue
            date_td = row.select_one("td.dateRange")
            venue_td = row.select_one("td:nth-child(3)")
            flag_img = venue_td.select_one("img[alt]") if venue_td else None
            country = flag_img.get("alt") if flag_img else None
            venue_text = venue_td.get_text(strip=True) if venue_td else None
            events.append({
                "source_id": source_id,
                "title": link_el.get_text(strip=True),
                "date_str": date_td.get_text(strip=True).split("\n")[0] if date_td else None,
                "location": venue_text,
                "country": country,
                "source_url": BASE_URL + "/" + href,
            })
        return events

    async def fetch_artists(self) -> list[dict[str, Any]]:
        """爬取艺术家列表（按字母分页：en/artists/A .. Z）"""
        import re
        artists = []
        seen_ids: set[str] = set()
        pages = ["Nr"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        for letter in pages:
            soup = await self._get(f"/en/artists/{letter}")
            if not soup:
                continue
            for a in soup.find_all("a", href=True):
                m = re.search(r"/artist/(\d+)/", a["href"])
                if not m:
                    continue
                source_id = m.group(1)
                if source_id in seen_ids:
                    continue
                seen_ids.add(source_id)
                name = a.get_text(strip=True)
                if not name:
                    continue
                # 尝试获取头像（同行 img）
                parent = a.find_parent()
                img_el = parent.find("img") if parent else None
                artists.append({
                    "source_id": source_id,
                    "name": name,
                    "avatar_url": img_el.get("src") if img_el else None,
                })
        return artists

    async def fetch_groups(self) -> list[dict[str, Any]]:
        """爬取团队列表（按字母分页：en/groups/A .. Z）"""
        import re
        groups = []
        seen_ids: set[str] = set()
        pages = ["Nr"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        for letter in pages:
            soup = await self._get(f"/en/groups/{letter}")
            if not soup:
                continue
            for a in soup.find_all("a", href=True):
                m = re.search(r"/group/(\d+)/", a["href"])
                if not m:
                    continue
                source_id = m.group(1)
                if source_id in seen_ids:
                    continue
                seen_ids.add(source_id)
                name = a.get_text(strip=True)
                if not name:
                    continue
                parent = a.find_parent()
                img_el = parent.find("img") if parent else None
                groups.append({
                    "source_id": source_id,
                    "name": name,
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
