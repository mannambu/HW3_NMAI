"""Constraint corruption tests and genetic-operator invariants."""
import csv
from dataclasses import replace
from pathlib import Path
import random
import tempfile
import unittest

from hw3.construct import construct, meeting_days
from hw3.evaluate import fitness, soft_metrics, validate
from hw3.export import export_run
from hw3.ga import Config, crossover, mutate, run_ga
from hw3.model import make_instance
from verify import verify_folder


class TimetableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instance = make_instance(32)
        cls.patterns = meeting_days(cls.instance, 42)
        cls.schedule = construct(cls.instance, cls.patterns, 42)

    def copy_schedule(self):
        return [list(day) for day in self.schedule]

    def test_capacity_and_all_hard_constraints(self):
        for rooms, sessions, complete, missing in ((20, 600, 300, 360), (32, 960, 480, 0)):
            instance = make_instance(rooms)
            schedule = construct(instance, meeting_days(instance, 42), 42)
            result = validate(instance, schedule)
            self.assertEqual(result["scheduled_sessions"], sessions)
            self.assertEqual(result["complete_sections"], complete)
            self.assertEqual(result["missing_sessions"], missing)
            self.assertEqual(result["total_hard_violations"], missing)
            self.assertEqual(result["operational_violations"], 0)
            self.assertEqual(result["professors_with_favorite"], 60)
            self.assertEqual(result["fully_feasible"], rooms == 32)

    def test_shared_data_across_scenarios(self):
        a, b = make_instance(20), make_instance(32)
        self.assertEqual(a.sections, b.sections)
        self.assertEqual(a.favorites, b.favorites)
        self.assertEqual(a.room_sizes, b.room_sizes[:20])

    def test_room_collision_detected(self):
        schedule = self.copy_schedule()
        a = schedule[0][0]
        i = next(i for i, event in enumerate(schedule[0]) if event[1] == a[1] and event != a)
        sid, slot, _ = schedule[0][i]
        schedule[0][i] = (sid, slot, a[2])
        self.assertTrue(any("room conflict" in error for error in validate(self.instance, schedule)["errors"]))

    def test_professor_collision_detected(self):
        schedule = self.copy_schedule()
        sid, slot, room = schedule[0][0]
        professor = self.instance.sections[sid - 1].professor
        i = next(i for i, (other, _, _) in enumerate(schedule[0])
                 if other != sid and self.instance.sections[other - 1].professor == professor)
        other, _, other_room = schedule[0][i]
        schedule[0][i] = (other, slot, other_room)
        self.assertTrue(any("professor conflict" in error for error in validate(self.instance, schedule)["errors"]))

    def test_section_collision_and_extra_session_detected(self):
        schedule = self.copy_schedule()
        schedule[0].append(schedule[0][0])
        errors = validate(self.instance, schedule)["errors"]
        self.assertTrue(any("section conflict" in error for error in errors))
        self.assertTrue(any("extra sessions" in error for error in errors))

    def test_adjacent_and_same_day_detected(self):
        sid = next(sid for sid, pair in self.patterns.items() if pair == (0, 2))
        for destination in (0, 1):
            schedule = self.copy_schedule()
            event = next(e for e in schedule[2] if e[0] == sid)
            schedule[2].remove(event)
            schedule[destination].append(event)
            self.assertTrue(any("same/adjacent" in error for error in validate(self.instance, schedule)["errors"]))

    def test_room_size_detected(self):
        schedule = self.copy_schedule()
        i = next(i for i, event in enumerate(schedule[0]) if self.instance.sections[event[0] - 1].size == 2)
        sid, slot, _ = schedule[0][i]
        small = self.instance.room_sizes.index(0) + 1
        schedule[0][i] = (sid, slot, small)
        self.assertTrue(any("too small" in error for error in validate(self.instance, schedule)["errors"]))

    def test_missing_session_is_a_hard_violation(self):
        schedule = self.copy_schedule()
        schedule[0].pop()
        result = validate(self.instance, schedule)
        self.assertFalse(result["fully_feasible"])
        self.assertEqual(result["missing_sessions"], 1)
        self.assertEqual(result["total_hard_violations"], 1)

    def test_invalid_room_slot_day_and_section_detected(self):
        for event in ((1, 7, 1), (1, 1, 33), (481, 1, 1)):
            schedule = self.copy_schedule()
            schedule[0][0] = event
            self.assertTrue(any("Out-of-range" in error for error in validate(self.instance, schedule)["errors"]))
        schedule = self.copy_schedule() + [[(1, 1, 1)]]
        self.assertGreater(validate(self.instance, schedule)["operational_violations"], 0)

    def test_professor_load_limit_detected(self):
        sections = tuple(replace(s, professor=1) if s.professor == 2 else s for s in self.instance.sections)
        instance = replace(self.instance, sections=sections)
        errors = validate(instance, self.schedule)["errors"]
        self.assertTrue(any("exceeds ten" in error for error in errors))

    def test_course_restriction_detected(self):
        favorites = list(self.instance.favorites)
        favorites[0] = (2, 3, 4)
        instance = replace(self.instance, favorites=tuple(favorites))
        self.assertTrue(any("cannot teach" in error for error in validate(instance, self.schedule)["errors"]))

    def test_operators_preserve_all_constraints(self):
        rng = random.Random(813)
        for rooms in (20, 32):
            instance = make_instance(rooms)
            patterns = meeting_days(instance, 42)
            a = construct(instance, patterns, 1)
            b = construct(instance, patterns, 2)
            expected_missing = 960 - rooms * 30
            for _ in range(150):
                a = mutate(instance, crossover(a, b, rng), rng)
                result = validate(instance, a)
                self.assertEqual(result["operational_violations"], 0, result["errors"])
                self.assertEqual(result["missing_sessions"], expected_missing)
                b = mutate(instance, b, rng)

    def test_ga_reproducibility_elitism_and_improvement(self):
        config = Config(population=10, generations=15, elite=2, seed=37)
        a = run_ga(self.instance, config)
        b = run_ga(self.instance, config)
        self.assertEqual(a, b)
        costs = [row["best_soft_cost"] for row in a[2]]
        self.assertTrue(all(y <= x for x, y in zip(costs, costs[1:])))
        self.assertLess(costs[-1], costs[0])

    def test_soft_metrics_hand_calculation(self):
        # One professor/course, two Monday lectures at slots 1 and 6.
        # This intentionally invalid example tests ONLY the soft-cost arithmetic.
        room = self.instance.room_sizes.index(2) + 1
        schedule = [((1, 1, room), (1, 6, room)), (), (), (), ()]
        result = soft_metrics(self.instance, schedule)
        mismatch = 0 if self.instance.sections[0].size == 2 else 2
        self.assertEqual(result["idle_slots"], 4)
        self.assertEqual(result["mixed_professor_days"], 1)
        self.assertEqual(result["course_minority_sessions"], 1)
        self.assertEqual(result["soft_cost"], 8 + 5 + 3 + mismatch)
        self.assertGreater(fitness(100, 0), fitness(0, 1))

    def test_export_round_trip_and_metadata_tamper(self):
        with tempfile.TemporaryDirectory() as folder:
            validation = validate(self.instance, self.schedule)
            soft = soft_metrics(self.instance, self.schedule)["soft_cost"]
            history = [{"generation": 0, "best_soft_cost": soft, "mean_soft_cost": soft,
                        "conditional_fitness": 1 / (1 + soft), "best_fitness": fitness(soft, 0)}]
            export_run(folder, self.instance, self.schedule, self.schedule, history, {"validation": validation})
            self.assertEqual(verify_folder(folder), validation)
            path = Path(folder) / "schedule.csv"
            with path.open(encoding="utf-8-sig", newline="") as file:
                rows = list(csv.DictReader(file))
            rows[0]["professor"] = "999"
            with path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaises(ValueError):
                verify_folder(folder)

    def test_invalid_configuration_rejected(self):
        for config in (Config(population=1), Config(generations=-1), Config(mutation_rate=1.1)):
            with self.assertRaises(ValueError):
                config.check()
        with self.assertRaises(ValueError):
            make_instance(21)


if __name__ == "__main__":
    unittest.main()
