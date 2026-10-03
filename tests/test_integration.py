import json
from pathlib import Path

from opencv_event_tracker.app import run
from opencv_event_tracker.config import load_config
from opencv_event_tracker.demo import generate_demo_video


def test_deterministic_demo(tmp_path: Path) -> None:
    video = generate_demo_video(tmp_path / "demo.mp4")
    output = tmp_path / "output"
    summary = run(load_config(Path("examples/demo.yaml")), input_path=video, output_override=output)
    assert summary.frames_processed == 180
    assert summary.objects_tracked >= 2
    assert summary.event_counts.get("zone_enter", 0) >= 1
    assert summary.event_counts.get("line_cross", 0) >= 1
    events = [json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()]
    assert events
    assert list((output / "screenshots").glob("*.jpg"))
    assert (output / "annotated.mp4").stat().st_size > 1000
