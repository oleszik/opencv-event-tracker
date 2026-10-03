"""Zone membership and line-crossing geometry."""

from .config import LineConfig, ZoneConfig
from .models import Point


def point_in_zone(point: Point, zone: ZoneConfig) -> bool:
    return zone.x1 <= point[0] <= zone.x2 and zone.y1 <= point[1] <= zone.y2


def line_side(point: Point, line: LineConfig) -> int:
    ax, ay = line.start
    bx, by = line.end
    value = (bx - ax) * (point[1] - ay) - (by - ay) * (point[0] - ax)
    return (value > 0) - (value < 0)


def crossing_direction(previous: Point, current: Point, line: LineConfig) -> str | None:
    before, after = line_side(previous, line), line_side(current, line)
    if before == 0 or after == 0 or before == after:
        return None
    return "negative_to_positive" if before < after else "positive_to_negative"
