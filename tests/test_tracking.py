from opencv_event_tracker.models import Detection
from opencv_event_tracker.tracking import CentroidTracker


def test_centroid() -> None:
    assert Detection((10, 20, 30, 40)).centroid == (25, 40)


def test_tracker_preserves_id_and_loses_track() -> None:
    tracker = CentroidTracker(max_distance=30, max_missing_frames=1)
    tracks, created, _ = tracker.update([Detection((0, 0, 10, 10))], 1)
    assert tracks[0].object_id == created[0].object_id == 1
    tracks, created, lost = tracker.update([Detection((5, 0, 10, 10))], 2)
    assert tracks[0].object_id == 1 and not created and not lost
    tracker.update([], 3)
    _, _, lost = tracker.update([], 4)
    assert lost[0].object_id == 1
