"""Build full-capacity seed timetables by bipartite edge coloring.

An event is (section_id, timeslot, room_id). A chromosome contains five days.
Every selected section has a fixed pair of nonadjacent meeting days. GA can
change its slots and rooms, but preserves those day pairs and professor mapping.
"""
import random


def meeting_days(instance, seed):
    rng = random.Random(seed)
    patterns = {}
    full = len(instance.room_sizes) == 32
    for p in range(60):
        section_ids = list(range(8 * p + 1, 8 * p + 9))
        rng.shuffle(section_ids)
        if not full:
            pairs = [(0, 2), (0, 4), (2, 4), (1, 3), (1, 3)]
        else:
            # Across 60 professors, each day has exactly 192 sessions.
            triangle = [(0, 2), (0, 4), (2, 4)]
            if p < 48:
                counts, tuth = [2, 2, 2], 3
                counts[p % 3] = 1
            else:
                counts, tuth = [1, 1, 1], 4
                counts[p % 3] = 2
            pairs = [pair for pair, n in zip(triangle, counts) for _ in range(n)]
            pairs += [(1, 3)] * tuth
        rng.shuffle(pairs)
        patterns.update(zip(section_ids, pairs))
    return patterns


def color_day(instance, ids, rng):
    """Assign rooms, then edge-color professor-room multigraph with six slots.

Pad both sides to 60 vertices and fill degree deficits with dummy edges. A
6-regular bipartite multigraph has a perfect matching; removing one leaves a
5-regular graph. Repeat six times. Real edges become conflict-free sessions.
"""
    n = 60
    edges = [[[] for _ in range(n)] for _ in range(n)]
    room_load = [0] * len(instance.room_sizes)
    shuffled = list(ids)
    rng.shuffle(shuffled)
    shuffled.sort(key=lambda sid: -instance.sections[sid - 1].size)
    for sid in shuffled:
        section = instance.sections[sid - 1]
        options = [r for r, size in enumerate(instance.room_sizes)
                   if size >= section.size and room_load[r] < 6]
        if not options:
            raise ValueError("Room-size capacity is insufficient for this day; change input data.")
        # Tightest room first; balance load inside a room-size category.
        rng.shuffle(options)
        room = min(options, key=lambda r: (instance.room_sizes[r], room_load[r]))
        room_load[room] += 1
        edges[section.professor - 1][room].append(sid)
    left = [6 - sum(map(len, row)) for row in edges]
    right = [6 - sum(len(edges[p][r]) for p in range(n)) for r in range(n)]
    if min(left + right) < 0:
        raise ValueError("A professor or room needs more than six slots on one day.")
    for p in range(n):
        for r in range(n):
            take = min(left[p], right[r])
            edges[p][r].extend([None] * take)
            left[p] -= take
            right[r] -= take
    events = []
    for slot in range(1, 7):
        adj = [[r for r in range(n) if edges[p][r]] for p in range(n)]
        for row in adj:
            rng.shuffle(row)
        match = [-1] * n

        def augment(p, seen):
            for r in adj[p]:
                if r in seen:
                    continue
                seen.add(r)
                if match[r] == -1 or augment(match[r], seen):
                    match[r] = p
                    return True
            return False

        order = list(range(n))
        rng.shuffle(order)
        for p in order:
            if not augment(p, set()):
                raise RuntimeError("Regular graph unexpectedly has no perfect matching.")
        for r, p in enumerate(match):
            sid = edges[p][r].pop()
            if sid is not None:
                events.append((sid, slot, r + 1))
    return tuple(sorted(events))


def construct(instance, patterns, seed):
    rng = random.Random(seed)
    return tuple(color_day(instance, [sid for sid, pair in patterns.items() if day in pair], rng)
                 for day in range(5))
