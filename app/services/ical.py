"""iCal 导出服务"""
from datetime import datetime, timezone

from icalendar import Calendar, Event as CalEvent

from app.models.event import Event


def generate_ical(events: list[Event]) -> bytes:
    cal = Calendar()
    cal.add("prodid", "-//BBoyApp//bboyapp.com//ZH")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "BBoyApp 街舞赛事")
    cal.add("x-wr-timezone", "UTC")

    for event in events:
        ev = CalEvent()
        ev.add("summary", event.title)
        ev.add("dtstart", event.date)
        ev.add("dtend", event.end_date or event.date)
        if event.location:
            ev.add("location", event.location)
        if event.source_url:
            ev.add("url", event.source_url)
        ev.add("uid", f"{event.source_id}@bboyapp.com")
        cal.add_component(ev)

    return cal.to_ical()
