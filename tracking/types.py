"""
tracking/types.py

Pure data types for tracking — no torch dependency.
Imported by metrics/ modules to avoid pulling in detection/detector.py → torch.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Track:
    """A persistent player track across frames."""
    track_id: int
    bbox: np.ndarray             # current [x1, y1, x2, y2]
    pitch_pos: Optional[np.ndarray] = None   # (x, y) in pitch metres
    team: Optional[str] = None
    jersey_number: Optional[int] = None
    reid_embedding: Optional[np.ndarray] = None

    # History
    bbox_history: list[np.ndarray] = field(default_factory=list)
    pitch_history: list[np.ndarray] = field(default_factory=list)
    frame_history: list[int] = field(default_factory=list)

    # Best player crop seen so far (updated when a larger bbox is matched).
    # Used by jersey OCR after tracking completes.
    best_crop: Optional[np.ndarray] = None

    # State
    frames_since_seen: int = 0
    age: int = 0                 # total frames this track has been active
    is_confirmed: bool = False   # True once track has lived long enough

    @property
    def center(self) -> np.ndarray:
        x1, y1, x2, y2 = self.bbox
        return np.array([(x1 + x2) / 2, (y1 + y2) / 2])

    @property
    def velocity(self) -> Optional[np.ndarray]:
        """Pixel velocity from last two positions."""
        if len(self.bbox_history) < 2:
            return None
        prev = self._center_of(self.bbox_history[-2])
        curr = self._center_of(self.bbox_history[-1])
        return curr - prev

    @staticmethod
    def _center_of(bbox: np.ndarray) -> np.ndarray:
        return np.array([(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2])


@dataclass
class TrackedFrame:
    """All active tracks for a single frame."""
    frame_id: int
    tracks: list[Track]

    @property
    def confirmed_tracks(self) -> list[Track]:
        return [t for t in self.tracks if t.is_confirmed]
