from datetime import UTC, datetime
from zoneinfo import ZoneInfo

SEOUL_TZ = ZoneInfo("Asia/Seoul")


def format_datetime_for_seoul(value: datetime | None) -> str:
    if value is None:
        return "-"

    normalized = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return normalized.astimezone(SEOUL_TZ).strftime("%Y-%m-%d %H:%M")
