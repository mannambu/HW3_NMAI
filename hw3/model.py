"""Reproducible input data; indices in exported data are one-based."""
from dataclasses import dataclass
import random

DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")


@dataclass(frozen=True)
class Section:
    id: int
    course: int
    professor: int
    size: int


@dataclass(frozen=True)
class Instance:
    sections: tuple
    room_sizes: tuple
    favorites: tuple
    seed: int

    @property
    def capacity(self):
        return len(self.room_sizes) * 30

    def to_dict(self):
        return {
            "seed": self.seed, "num_courses": 60, "num_professors": 60,
            "num_days": 5, "slots_per_day": 6, "sessions_per_section": 2,
            "max_sections_per_professor": 10,
            "sections": [vars(s) for s in self.sections],
            "rooms": [{"id": i + 1, "size": size} for i, size in enumerate(self.room_sizes)],
            "professors": [{"id": i + 1, "favorites": list(f), "allowed_courses": list(f)}
                           for i, f in enumerate(self.favorites)],
            "availability": "All rooms are available at all 30 weekly slots.",
        }


def make_instance(rooms=32, seed=2026):
    if rooms not in (20, 32):
        raise ValueError("The documented experiments support 20 or 32 rooms.")
    rng = random.Random(seed)
    sections = tuple(Section(i + 1, i // 8 + 1, i // 8 + 1, rng.randrange(3))
                     for i in range(480))
    favorites = tuple(tuple([p] + rng.sample([c for c in range(1, 61) if c != p], 2))
                      for p in range(1, 61))
    # The two experiments share exactly the same sections, preferences and first 20 rooms.
    sizes = [0] * 4 + [1] * 6 + [2] * 10
    rng.shuffle(sizes)
    if rooms == 32:
        extra = [0] * 2 + [1] * 4 + [2] * 6
        rng.shuffle(extra)
        sizes += extra
    return Instance(sections, tuple(sizes), favorites, seed)
