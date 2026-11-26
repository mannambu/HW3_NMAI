"""Run reproducible HW3 experiments. No third-party dependency is needed."""
import argparse
from dataclasses import asdict
from pathlib import Path
import statistics
import time
from hw3.evaluate import fitness, soft_metrics
from hw3.export import export_run, write_csv, write_json
from hw3.ga import Config, run_ga
from hw3.model import make_instance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rooms", nargs="+", type=int, choices=(20, 32), default=[20, 32])
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--data-seed", type=int, default=2026)
    parser.add_argument("--population", type=int, default=60)
    parser.add_argument("--generations", type=int, default=400)
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    comparison = []
    for rooms in args.rooms:
        instance = make_instance(rooms, args.data_seed)
        runs = []
        all_history = []
        winner = None
        for seed in args.seeds:
            config = Config(population=args.population, generations=args.generations, seed=seed)
            start = time.perf_counter()
            print(f"Running {rooms} rooms, seed {seed}", flush=True)
            best, initial, history, validation = run_ga(instance, config)
            elapsed = time.perf_counter() - start
            final_metrics = soft_metrics(instance, best)
            initial_metrics = soft_metrics(instance, initial)
            summary = {"rooms": rooms, "config": asdict(config), "data_seed": args.data_seed,
                       "elapsed_seconds": round(elapsed, 4), "validation": validation,
                       "initial_metrics": initial_metrics, "final_metrics": final_metrics,
                       "fitness": fitness(final_metrics["soft_cost"], validation["missing_sessions"], validation["operational_violations"]),
                       "soft_improvement_percent": round(100 * (initial_metrics["soft_cost"] - final_metrics["soft_cost"]) / initial_metrics["soft_cost"], 4)}
            runs.append(summary)
            all_history.extend({"seed": seed, **row} for row in history)
            export_run(args.output / f"rooms{rooms}" / f"seed{seed}", instance, best, initial, history, summary)
            if winner is None or final_metrics["soft_cost"] < winner[0]:
                winner = (
                    final_metrics["soft_cost"],
                    best,
                    initial,
                    history,
                    summary
                )

            print(
                f"  final={final_metrics['soft_cost']}; "
                f"improvement={summary['soft_improvement_percent']:.2f}%; "
                f"elapsed={elapsed:.2f}s",
                flush=True
            )

        if winner is None:
            raise RuntimeError(f"No successful runs for {rooms} rooms.")

        _, best, initial, history, summary = winner
        folder = args.output / f"rooms{rooms}"
        export_run(folder, instance, best, initial, history, summary)
        write_csv(folder / "all_fitness.csv", all_history)
        costs = [r["final_metrics"]["soft_cost"] for r in runs]
        stats = {"rooms": rooms, "runs": len(runs), "best_seed": summary["config"]["seed"],
                 "best_soft_cost": min(costs), "mean_soft_cost": statistics.mean(costs),
                 "stdev_soft_cost": statistics.stdev(costs) if len(costs) > 1 else 0.0,
                 "validation": summary["validation"], "run_summaries": runs}
        write_json(folder / "experiments.json", stats)
        comparison.append(stats)
    write_json(args.output / "comparison.json", comparison)
    print(f"Done. Open {args.output / 'rooms32' / 'schedule.html'} (if 32 rooms were requested).")


if __name__ == "__main__":
    main()
