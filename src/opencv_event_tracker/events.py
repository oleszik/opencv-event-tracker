"""Stateful event generation and cooldown."""

from __future__ import annotations

from .config import EventsConfig, LineConfig, ZoneConfig
from .models import Event, Track
from .zones import crossing_direction, point_in_zone


class EventEngine:
    def __init__(self, config: EventsConfig, zones: list[ZoneConfig], lines: list[LineConfig]):
        self.config = config
        self.zones = zones
        self.lines = lines
        self.zone_state: dict[tuple[int, str], bool] = {}
        self.last_emitted: dict[tuple[int, str, str], float] = {}

    def _emit(self, event: Event, clock_seconds: float, context: str = "") -> Event | None:
        key = (event.object_id, event.event_type, context)
        last = self.last_emitted.get(key)
        if last is not None and clock_seconds - last < self.config.cooldown_seconds:
            return None
        self.last_emitted[key] = clock_seconds
        return event

    def process_track(
        self, track: Track, frame_number: int, clock_seconds: float, source: str
    ) -> list[Event]:
        events: list[Event] = []
        common = {"bbox": track.bbox, "centroid": track.centroid}
        for zone in self.zones:
            key = (track.object_id, zone.name)
            inside = point_in_zone(track.centroid, zone)
            was_inside = self.zone_state.get(key, False)
            self.zone_state[key] = inside
            event_type = (
                "zone_enter"
                if inside and not was_inside
                else "zone_exit"
                if was_inside and not inside
                else None
            )
            if event_type:
                event = Event.create(
                    event_type, frame_number, track.object_id, source, zone=zone.name, **common
                )
                emitted = self._emit(event, clock_seconds, zone.name)
                if emitted:
                    events.append(emitted)
        if track.previous_centroid is not None:
            for line in self.lines:
                direction = crossing_direction(track.previous_centroid, track.centroid, line)
                if direction:
                    event = Event.create(
                        "line_cross",
                        frame_number,
                        track.object_id,
                        source,
                        line=line.name,
                        direction=direction,
                        **common,
                    )
                    emitted = self._emit(event, clock_seconds, line.name)
                    if emitted:
                        events.append(emitted)
        return events

    def object_event(
        self, event_type: str, track: Track, frame_number: int, clock_seconds: float, source: str
    ) -> Event | None:
        event = Event.create(
            event_type,
            frame_number,
            track.object_id,
            source,
            bbox=track.bbox,
            centroid=track.centroid,
        )
        return self._emit(event, clock_seconds)
