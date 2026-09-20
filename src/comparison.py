"""Paired comparisons: average seeds first, give each instance one vote."""
from collections import defaultdict
from statistics import mean

from .models import InputError


def paired_comparisons(rows, references=("B0", "B2", "B3"), tolerance=1e-9):
    grouped = defaultdict(list)
    for row in rows:
        if not row["feasible"]:
            raise InputError("Cannot compare infeasible benchmark results")
        grouped[row["instance"], row["method"]].append(row["objective"])
    averages = {key: mean(values) for key, values in grouped.items()}
    methods = sorted({method for _, method in averages})
    output = []
    for reference in references:
        for method in methods:
            if method == reference:
                continue
            pairs = []
            for instance in sorted({name for name, _ in averages}):
                if (instance, reference) not in averages or (instance, method) not in averages:
                    continue
                baseline = averages[instance, reference]
                value = averages[instance, method]
                delta = value - baseline
                pairs.append({"instance": instance, "difference": delta,
                              "improvement_pct": 100 * (baseline - value) / baseline if baseline else None,
                              "outcome": "tie" if abs(delta) <= tolerance else "win" if delta < 0 else "loss"})
            if pairs:
                improvements = [p["improvement_pct"] for p in pairs if p["improvement_pct"] is not None]
                output.append({"method": method, "reference": reference, "instances": len(pairs),
                               **{key: sum(p["outcome"] == key for p in pairs) for key in ("win", "tie", "loss")},
                               "mean_improvement_pct": mean(improvements) if improvements else None,
                               "percentage_instances": len(improvements), "pairs": pairs})
    return output
