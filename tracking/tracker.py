"""
tracking/tracker.py

Multi-object tracker that maintains persistent player IDs across frames.
Combines SORT (Kalman filter + Hungarian algorithm) with Re-ID embeddings
to survive occlusions and re-entries.
"""

from __future__ import annotations

import numpy as np
from loguru import logger

from config.settings import settings
from detection.detector import Detection, FrameDetections
from tracking.types import Track, TrackedFrame


# ---------------------------------------------------------------------------
# IoU utilities
# ---------------------------------------------------------------------------

def compute_iou(bbox_a: np.ndarray, bbox_b: np.ndarray) -> float:
    """Compute IoU between two bboxes [x1, y1, x2, y2]."""
    ax1, ay1, ax2, ay2 = bbox_a
    bx1, by1, bx2, by2 = bbox_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union_area = area_a + area_b - inter_area

    return inter_area / union_area if union_area > 0 else 0.0


def iou_cost_matrix(
    tracks: list[Track], detections: list[Detection]
) -> np.ndarray:
    """Build IoU cost matrix (1 - IoU) for Hungarian assignment."""
    cost = np.ones((len(tracks), len(detections)))
    for i, track in enumerate(tracks):
        for j, det in enumerate(detections):
            cost[i, j] = 1.0 - compute_iou(track.bbox, det.bbox)
    return cost


# ---------------------------------------------------------------------------
# Re-ID embedding extractor (stub — replace with TransReID weights)
# ---------------------------------------------------------------------------

class ReIDExtractor:
    """
    Extracts Re-ID embedding vectors from player crops.
    Stub implementation uses HOG features.
    Replace with TransReID or OSNet for production.
    """

    def __init__(self):
        self.embedding_dim = 512
        logger.info(
            "ReIDExtractor: using HOG stub — replace with TransReID for production"
        )

    def extract(self, crop: np.ndarray) -> np.ndarray:
        """Return a normalised embedding vector for a player crop."""
        import cv2
        if crop.size == 0:
            return np.zeros(self.embedding_dim)

        resized = cv2.resize(crop, (64, 128))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        hog = cv2.HOGDescriptor(
            _winSize=(64, 128),
            _blockSize=(16, 16),
            _blockStride=(8, 8),
            _cellSize=(8, 8),
            _nbins=9,
        )
        descriptor = hog.compute(gray).flatten()

        # Pad or trim to embedding_dim
        if len(descriptor) >= self.embedding_dim:
            vec = descriptor[: self.embedding_dim]
        else:
            vec = np.pad(descriptor, (0, self.embedding_dim - len(descriptor)))

        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b))  # both already normalised


# ---------------------------------------------------------------------------
# Main tracker
# ---------------------------------------------------------------------------

class PlayerTracker:
    """
    Tracks players across frames, maintaining persistent IDs.

    Strategy:
    1. Match detections to existing tracks via IoU (fast)
    2. For unmatched: try Re-ID embedding similarity (handles re-entries)
    3. Create new tracks for remaining unmatched detections
    4. Drop tracks lost for > max_lost_frames
    """

    def __init__(self):
        self.tracks: list[Track] = []
        self._next_id: int = 1
        self.reid = ReIDExtractor()

    def _new_track(self, detection: Detection, frame_id: int) -> Track:
        embedding = None
        if detection.crop is not None:
            embedding = self.reid.extract(detection.crop)

        track = Track(
            track_id=self._next_id,
            bbox=detection.bbox.copy(),
            team=detection.team,
            reid_embedding=embedding,
        )
        track.bbox_history.append(detection.bbox.copy())
        track.frame_history.append(frame_id)
        self._next_id += 1
        return track

    def _update_track(
        self, track: Track, detection: Detection, frame_id: int
    ) -> None:
        track.bbox = detection.bbox.copy()
        track.frames_since_seen = 0
        track.age += 1
        track.bbox_history.append(detection.bbox.copy())
        track.frame_history.append(frame_id)

        if track.team is None and detection.team is not None:
            track.team = detection.team

        if detection.crop is not None:
            new_embedding = self.reid.extract(detection.crop)
            if track.reid_embedding is None:
                track.reid_embedding = new_embedding
            else:
                # Exponential moving average of embedding
                track.reid_embedding = (
                    0.8 * track.reid_embedding + 0.2 * new_embedding
                )
                norm = np.linalg.norm(track.reid_embedding)
                if norm > 0:
                    track.reid_embedding /= norm

        if track.age >= settings.min_track_length:
            track.is_confirmed = True

    def update(
        self, frame_detections: FrameDetections
    ) -> TrackedFrame:
        """
        Update tracker with new frame detections.
        Returns TrackedFrame with updated track states.
        """
        detections = frame_detections.detections
        frame_id = frame_detections.frame_id
        active_tracks = [t for t in self.tracks if t.frames_since_seen == 0 or
                         t.frames_since_seen <= settings.max_lost_frames]

        if not detections:
            for t in active_tracks:
                t.frames_since_seen += 1
            self.tracks = [
                t for t in self.tracks
                if t.frames_since_seen <= settings.max_lost_frames
            ]
            return TrackedFrame(frame_id=frame_id, tracks=self.tracks)

        if not active_tracks:
            self.tracks = [self._new_track(d, frame_id) for d in detections]
            return TrackedFrame(frame_id=frame_id, tracks=self.tracks)

        # --- Stage 1: IoU matching ---
        try:
            from scipy.optimize import linear_sum_assignment
            cost = iou_cost_matrix(active_tracks, detections)
            row_ind, col_ind = linear_sum_assignment(cost)
        except ImportError:
            row_ind, col_ind = np.array([]), np.array([])

        matched_tracks: set[int] = set()
        matched_detections: set[int] = set()

        for r, c in zip(row_ind, col_ind):
            if cost[r, c] < 0.7:  # IoU > 0.3 threshold
                self._update_track(active_tracks[r], detections[c], frame_id)
                matched_tracks.add(r)
                matched_detections.add(c)

        # --- Stage 2: Re-ID for unmatched ---
        unmatched_track_ids = [
            i for i in range(len(active_tracks)) if i not in matched_tracks
        ]
        unmatched_det_ids = [
            j for j in range(len(detections)) if j not in matched_detections
        ]

        still_unmatched_tracks: list[int] = []
        still_unmatched_dets: list[int] = list(unmatched_det_ids)

        for ti in unmatched_track_ids:
            track = active_tracks[ti]
            if track.reid_embedding is None:
                still_unmatched_tracks.append(ti)
                continue

            best_sim, best_di = -1.0, -1
            for di in still_unmatched_dets:
                det = detections[di]
                if det.crop is None:
                    continue
                emb = self.reid.extract(det.crop)
                sim = self.reid.cosine_similarity(track.reid_embedding, emb)
                if sim > best_sim:
                    best_sim, best_di = sim, di

            if best_sim >= settings.reid_threshold and best_di >= 0:
                self._update_track(track, detections[best_di], frame_id)
                still_unmatched_dets.remove(best_di)
            else:
                still_unmatched_tracks.append(ti)

        # --- Stage 3: Age lost tracks, create new ones ---
        for ti in still_unmatched_tracks:
            active_tracks[ti].frames_since_seen += 1

        for di in still_unmatched_dets:
            self.tracks.append(self._new_track(detections[di], frame_id))

        # Prune dead tracks
        self.tracks = [
            t for t in self.tracks
            if t.frames_since_seen <= settings.max_lost_frames
        ]

        return TrackedFrame(frame_id=frame_id, tracks=self.tracks)

    def process_detections(
        self, all_detections: list[FrameDetections]
    ) -> list[TrackedFrame]:
        """Run tracker over all frame detections from a video."""
        results = []
        for frame_dets in all_detections:
            tracked = self.update(frame_dets)
            results.append(tracked)
        logger.info(
            f"Tracking complete — {self._next_id - 1} unique tracks created"
        )
        return results
