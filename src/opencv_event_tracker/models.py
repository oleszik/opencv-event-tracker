"""Shared domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

BBox = tuple[int, int, int, int]
Point = tuple[int, int]


@dataclass(slots=True)
class Detection:
    bbox: BBox

    @property
    def centroid(self) -> Point:
        x, y, width, height = self.bbox
        return (x + width // 2, y + height // 2)


@dataclass(slots=True)
class Track:
    object_id: int
    bbox: BBox
    centroid: Point
    previous_centroid: Point | None
    first_seen_frame: int
    last_seen_frame: int
    missing_frames: int = 0
    history: list[Point] = field(default_factory=list)


@dataclass(slots=True)
class Event:
    event_type: str
    frame_number: int
    object_id: int
    source: str
    timestamp: str
    bbox: BBox | None = None
    centroid: Point | None = None
    zone: str | None = None
    line: str | None = None
    direction: str | None = None
    event_id: str = field(default_factory=lambda: str(uuid4()))

    @classmethod
    def create(
        cls,
        event_type: str,
        frame_number: int,
        object_id: int,
        source: str,
        **kwargs: object,
    ) -> Event:
        timestamp = datetime.now(UTC).isoformat()
        return cls(event_type, frame_number, object_id, source, timestamp, **kwargs)

    def to_dict(self) -> dict[str, object]:
        return {key: value for key, value in asdict(self).items() if value is not None}
