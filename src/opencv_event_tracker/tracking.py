"""Small deterministic centroid tracker."""

from __future__ import annotations

from math import hypot

from .models import Detection, Track


class CentroidTracker:
    def __init__(self, max_distance: float, max_missing_frames: int, history_length: int = 30):
        self.max_distance = max_distance
        self.max_missing_frames = max_missing_frames
        self.history_length = history_length
        self.tracks: dict[int, Track] = {}
        self.next_id = 1
        self.total_created = 0

    def update(
        self, detections: list[Detection], frame_number: int
    ) -> tuple[list[Track], list[Track], list[Track]]:
        unmatched_tracks = set(self.tracks)
        unmatched_detections = set(range(len(detections)))
        candidates = sorted(
            (
                hypot(
                    self.tracks[track_id].centroid[0] - detection.centroid[0],
                    self.tracks[track_id].centroid[1] - detection.centroid[1],
                ),
                track_id,
                index,
            )
            for track_id in self.tracks
            for index, detection in enumerate(detections)
        )
        for distance, track_id, index in candidates:
            if distance > self.max_distance:
                break
            if track_id not in unmatched_tracks or index not in unmatched_detections:
                continue
            track = self.tracks[track_id]
            track.previous_centroid = track.centroid
            track.centroid = detections[index].centroid
            track.bbox = detections[index].bbox
            track.last_seen_frame = frame_number
            track.missing_frames = 0
            track.history.append(track.centroid)
            track.history = track.history[-self.history_length :]
            unmatched_tracks.remove(track_id)
            unmatched_detections.remove(index)

        lost: list[Track] = []
        for track_id in list(unmatched_tracks):
            track = self.tracks[track_id]
            track.missing_frames += 1
            if track.missing_frames > self.max_missing_frames:
                lost.append(self.tracks.pop(track_id))

        created: list[Track] = []
        for index in sorted(unmatched_detections):
            detection = detections[index]
            track = Track(
                self.next_id,
                detection.bbox,
                detection.centroid,
                None,
                frame_number,
                frame_number,
                history=[detection.centroid],
            )
            self.tracks[self.next_id] = track
            self.next_id += 1
            self.total_created += 1
            created.append(track)
        visible = [track for track in self.tracks.values() if track.missing_frames == 0]
        return visible, created, lost
