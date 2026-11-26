"""Fitness and a separate, exhaustive hard-constraint validator."""
from collections import Counter, defaultdict

WEIGHTS = {"idle_slots": 2, "idle_weekdays": 2, "extra_teaching_days": 1,
           "mixed_professor_days": 5, "course_minority_sessions": 3,
           "room_mismatches": 1}
HARD_WEIGHT = 100_000


def soft_metrics(instance, schedule):
    daily = [[[] for _ in range(5)] for _ in range(60)]
    periods = [[0, 0] for _ in range(60)]
    mismatch = 0
    for day, events in enumerate(schedule):
        for sid, slot, room in events:
            sec = instance.sections[sid - 1]
            daily[sec.professor - 1][day].append(slot)
            periods[sec.course - 1][int(slot > 3)] += 1
            mismatch += instance.room_sizes[room - 1] != sec.size
    gaps = week_gaps = extra_days = mixed = 0
    for days in daily:
        active = [d for d, slots in enumerate(days) if slots]
        if active:
            week_gaps += active[-1] - active[0] + 1 - len(active)
            extra_days += len(active) - 1
        for slots in days:
            if slots:
                gaps += max(slots) - min(slots) + 1 - len(slots)
                mixed += min(slots) <= 3 < max(slots)
    metrics = {"idle_slots": gaps, "idle_weekdays": week_gaps,
               "extra_teaching_days": extra_days, "mixed_professor_days": mixed,
               "course_minority_sessions": sum(min(x) for x in periods),
               "room_mismatches": mismatch}
    metrics["soft_cost"] = sum(WEIGHTS[k] * value for k, value in metrics.items())
    return metrics


def validate(instance, schedule):
    """Do not trust the constructor or GA: inspect every exported event.

    Missing required sessions are reported separately AND included in total
    hard violations; a maximum-coverage partial schedule is not fully feasible.
    """
    errors = []
    by_section = defaultdict(list)
    room_slots = Counter()
    professor_slots = Counter()
    section_slots = Counter()
    taught = defaultdict(set)
    favorite_taught = defaultdict(set)
    if len(schedule) != 5:
        errors.append("Schedule must have exactly five days.")
    for day, events in enumerate(schedule):
        for sid, slot, room in events:
            if not (1 <= sid <= len(instance.sections) and 1 <= slot <= 6
                    and 1 <= room <= len(instance.room_sizes) and 0 <= day < 5):
                errors.append(f"Out-of-range event: {(day, sid, slot, room)}")
                continue
            sec = instance.sections[sid - 1]
            by_section[sid].append((day, slot, room))
            room_slots[day, slot, room] += 1
            professor_slots[day, slot, sec.professor] += 1
            section_slots[day, slot, sid] += 1
            taught[sec.professor].add(sid)
            if instance.room_sizes[room - 1] < sec.size:
                errors.append(f"Room too small for section {sid}.")
            if sec.course not in instance.favorites[sec.professor - 1]:
                errors.append(f"Professor {sec.professor} cannot teach course {sec.course}.")
            else:
                favorite_taught[sec.professor].add(sec.course)
    for label, counts in (("room", room_slots), ("professor", professor_slots),
                          ("section", section_slots)):
        for key, count in counts.items():
            if count > 1:
                errors.extend([f"Simultaneous {label} conflict at {key}."] * (count - 1))
    missing = 0
    complete = 0
    for sec in instance.sections:
        events = by_section[sec.id]
        missing += max(0, 2 - len(events))
        if len(events) > 2:
            errors.extend([f"Section {sec.id} has extra sessions."] * (len(events) - 2))
        if len(events) == 2:
            if abs(events[0][0] - events[1][0]) < 2:
                errors.append(f"Section {sec.id} meets on same/adjacent days.")
            else:
                complete += 1
    for professor, sections in taught.items():
        if len(sections) > 10:
            errors.append(f"Professor {professor} exceeds ten sections.")
    return {"scheduled_sessions": sum(map(len, schedule)), "complete_sections": complete,
            "missing_sessions": missing, "missing_sections": sum(not by_section[s.id] for s in instance.sections),
            "operational_violations": len(errors), "total_hard_violations": len(errors) + missing,
            "fully_feasible": not errors and missing == 0,
            "capacity_lower_bound_missing_sessions": max(0, 2 * len(instance.sections) - instance.capacity),
            "professors_with_favorite": len(favorite_taught),
            "max_sections_per_professor": max(map(len, taught.values()), default=0),
            "errors": errors}


def fitness(soft_cost, missing_sessions, violations=0):
    return 1.0 / (1 + HARD_WEIGHT * (missing_sessions + violations) + soft_cost)
