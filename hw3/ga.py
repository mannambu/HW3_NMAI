"""Elitist genetic algorithm with day crossover and Kempe-chain mutations."""
from dataclasses import dataclass
import random
from .construct import construct, meeting_days
from .evaluate import fitness, soft_metrics, validate


@dataclass(frozen=True)
class Config:
    population: int = 40
    generations: int = 200
    elite: int = 4
    tournament: int = 3
    crossover_rate: float = 0.9
    mutation_rate: float = 0.9
    seed: int = 42

    def check(self):
        if self.population < 2 or not 1 <= self.elite < self.population:
            raise ValueError("Require population >= 2 and 1 <= elite < population.")
        if self.generations < 0 or not 1 <= self.tournament <= self.population:
            raise ValueError("Invalid generation count or tournament size.")
        if not (0 <= self.crossover_rate <= 1 and 0 <= self.mutation_rate <= 1):
            raise ValueError("Probabilities must lie in [0, 1].")


def crossover(a, b, rng):
    # All individuals share section/day membership. Each day is independently
    # conflict-free; copying complete days cannot introduce a hard conflict.
    return tuple(x if rng.random() < 0.5 else y for x, y in zip(a, b))


def mutate(instance, chromosome, rng):
    day = rng.randrange(5)
    events = list(chromosome[day])
    operation = rng.random()
    if operation < 0.70:
        # Swap two colors on a connected component of the professor-room graph.
        # Each vertex has <= 1 edge of each color, so conflicts stay impossible.
        s1, s2 = rng.sample(range(1, 7), 2)
        indices = [i for i, (_, slot, _) in enumerate(events) if slot in (s1, s2)]
        if indices:
            incident = {}
            for i in indices:
                sid, _, room = events[i]
                for vertex in (("p", instance.sections[sid - 1].professor), ("r", room)):
                    incident.setdefault(vertex, []).append(i)
            component = {rng.choice(indices)}
            queue = list(component)
            while queue:
                i = queue.pop()
                sid, _, room = events[i]
                for vertex in (("p", instance.sections[sid - 1].professor), ("r", room)):
                    for j in incident[vertex]:
                        if j not in component:
                            component.add(j)
                            queue.append(j)
            for i in component:
                sid, slot, room = events[i]
                events[i] = (sid, s2 if slot == s1 else s1, room)
    elif operation < 0.85:
        a, b = rng.sample(range(1, 7), 2)
        events = [(sid, b if slot == a else a if slot == b else slot, room)
                  for sid, slot, room in events]
    else:
        # Room swap inside a slot preserves occupancy and professor availability.
        slot = rng.randrange(1, 7)
        indices = [i for i, event in enumerate(events) if event[1] == slot]
        for _ in range(12):
            if len(indices) < 2:
                break
            a, b = rng.sample(indices, 2)
            sid_a, _, room_a = events[a]
            sid_b, _, room_b = events[b]
            if (instance.sections[sid_a - 1].size <= instance.room_sizes[room_b - 1]
                    and instance.sections[sid_b - 1].size <= instance.room_sizes[room_a - 1]):
                events[a] = (sid_a, slot, room_b)
                events[b] = (sid_b, slot, room_a)
                break
    result = list(chromosome)
    result[day] = tuple(events)
    return tuple(result)


def run_ga(instance, config=Config()):
    config.check()
    rng = random.Random(config.seed)
    patterns = meeting_days(instance, config.seed)
    base = construct(instance, patterns, config.seed)
    check = validate(instance, base)
    if check["operational_violations"] or check["missing_sessions"] != check["capacity_lower_bound_missing_sessions"]:
        raise RuntimeError(f"Constructor failed validation: {check}")
    # Diverse random feasible seeds, with the same selected sections/day pairs.
    population = [base]
    for _ in range(config.population - 1):
        population.append(construct(instance, patterns, rng.randrange(2**32)))
    scores = [soft_metrics(instance, x)["soft_cost"] for x in population]
    missing = check["missing_sessions"]
    initial_best = population[min(range(len(scores)), key=scores.__getitem__)]
    history = []

    def record(generation):
        best = min(scores)
        history.append({"generation": generation, "best_soft_cost": best,
                        "mean_soft_cost": sum(scores) / len(scores),
                        "worst_soft_cost": max(scores),
                        "best_fitness": fitness(best, missing),
                        "conditional_fitness": 1 / (1 + best),
                        "unique_individuals": len(set(population))})

    record(0)
    for generation in range(1, config.generations + 1):
        ranked = sorted(range(len(scores)), key=scores.__getitem__)
        next_pop = [population[i] for i in ranked[:config.elite]]
        next_scores = [scores[i] for i in ranked[:config.elite]]

        def select():
            sample = rng.sample(range(len(population)), config.tournament)
            return population[min(sample, key=scores.__getitem__)]

        while len(next_pop) < config.population:
            a, b = select(), select()
            child = crossover(a, b, rng) if rng.random() < config.crossover_rate else a
            if rng.random() < config.mutation_rate:
                for _ in range(rng.randint(1, 3)):
                    child = mutate(instance, child, rng)
            next_pop.append(child)
            next_scores.append(soft_metrics(instance, child)["soft_cost"])
        population, scores = next_pop, next_scores
        record(generation)
        if generation % 50 == 0:
            print(f"  generation {generation:4d}: best soft cost = {min(scores)}", flush=True)
    best = population[min(range(len(scores)), key=scores.__getitem__)]
    check = validate(instance, best)
    if check["operational_violations"] or check["missing_sessions"] != missing:
        raise RuntimeError(f"GA broke a hard constraint: {check}")
    return best, initial_best, history, check
