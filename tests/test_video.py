from pathlib import Path

import pytest

from opencv_event_tracker.video import VideoError, open_capture


def test_missing_video_error() -> None:
    with pytest.raises(VideoError, match="does not exist"):
        open_capture(Path("no-such-video.mp4"), None)
