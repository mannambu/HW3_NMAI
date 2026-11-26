"""Validate exported CSV against exported input data, independently of GA."""
import argparse
import csv
import json
from pathlib import Path
from hw3.evaluate import validate
from hw3.model import DAYS, Instance, Section


def verify_folder(folder):
    folder = Path(folder)
    data = json.loads((folder / "instance.json").read_text(encoding="utf-8"))
    instance = Instance(tuple(Section(**s) for s in data["sections"]),
                        tuple(r["size"] for r in data["rooms"]),
                        tuple(tuple(p["allowed_courses"]) for p in data["professors"]), data["seed"])
    schedule = [[] for _ in range(5)]
    with (folder / "schedule.csv").open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            sid, day, slot, room = (int(row[k]) for k in ("section", "day", "timeslot", "room"))
            if not (1 <= sid <= len(instance.sections) and 1 <= day <= 5
                    and 1 <= slot <= 6 and 1 <= room <= len(instance.room_sizes)):
                raise ValueError(f"CSV contains an out-of-range event: {row}")
            sec = instance.sections[sid - 1]
            if any(int(row[k]) != v for k, v in (("course", sec.course), ("professor", sec.professor),
                                                  ("section_size", sec.size), ("room_size", instance.room_sizes[room - 1]),
                                                  ("section_in_course", (sid - 1) % 8 + 1))):
                raise ValueError(f"CSV metadata disagrees with instance: {row}")
            if row["day_name"] != DAYS[day - 1] or row["period"] != ("AM" if slot <= 3 else "PM"):
                raise ValueError(f"CSV has an incorrect day/period label: {row}")
            schedule[day - 1].append((sid, slot, room))
    return validate(instance, schedule)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    try:
        result = verify_folder(args.folder)
    except (ValueError, KeyError, IndexError, OSError) as error:
        parser.exit(1, f"Validation failed: {error}\n")
    print(json.dumps(result, indent=2))
    if result["operational_violations"] or (result["missing_sessions"] and not args.allow_partial):
        parser.exit(1, "The schedule does not satisfy all required constraints.\n")


if __name__ == "__main__":
    main()
