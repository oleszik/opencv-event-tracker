from opencv_event_tracker.config import EventsConfig, LineConfig, ZoneConfig
from opencv_event_tracker.events import EventEngine
from opencv_event_tracker.models import Track
from opencv_event_tracker.zones import crossing_direction, point_in_zone


def make_track(current: tuple[int, int], previous: tuple[int, int] | None) -> Track:
    return Track(1, (current[0], current[1], 10, 10), current, previous, 1, 1, history=[current])


def test_zone_membership_and_enter_exit() -> None:
    zone = ZoneConfig("test", 10, 10, 30, 30)
    assert point_in_zone((20, 20), zone)
    engine = EventEngine(EventsConfig(cooldown_seconds=0), [zone], [])
    assert not engine.process_track(make_track((5, 5), None), 1, 0, "test")
    assert (
        engine.process_track(make_track((20, 20), (5, 5)), 2, 1, "test")[0].event_type
        == "zone_enter"
    )
    assert (
        engine.process_track(make_track((40, 40), (20, 20)), 3, 2, "test")[0].event_type
        == "zone_exit"
    )


def test_line_crossing_direction_and_event() -> None:
    line = LineConfig("gate", (10, 0), (10, 20))
    assert crossing_direction((5, 10), (15, 10), line) == "positive_to_negative"
    engine = EventEngine(EventsConfig(cooldown_seconds=0), [], [line])
    events = engine.process_track(make_track((15, 10), (5, 10)), 2, 1, "test")
    assert events[0].event_type == "line_cross"
    assert events[0].direction == "positive_to_negative"


def test_cooldown_deduplicates() -> None:
    engine = EventEngine(EventsConfig(cooldown_seconds=2), [], [])
    track = make_track((1, 1), None)
    assert engine.object_event("object_detected", track, 1, 1.0, "test")
    assert engine.object_event("object_detected", track, 2, 2.0, "test") is None
    assert engine.object_event("object_detected", track, 3, 3.1, "test")
