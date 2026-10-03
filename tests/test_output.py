import json
from pathlib import Path

from opencv_event_tracker.config import OutputConfig
from opencv_event_tracker.models import Event
from opencv_event_tracker.output import EventWriter


def test_jsonl_output(tmp_path: Path) -> None:
    event = Event.create("object_detected", 1, 2, "demo", centroid=(10, 20))
    with EventWriter(tmp_path / "run", OutputConfig(save_video=False)) as writer:
        writer.write(event)
    rows = (tmp_path / "run/events.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(rows[0])["object_id"] == 2
