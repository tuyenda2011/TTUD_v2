# Unified benchmark and evaluation

Goal: one experiment command produces independently audited evidence, CSV tables,
report/presentation figures, and a portable evaluation.json consumed by Streamlit.

- [x] Shared portable evaluation schema, raw-solution validation and per-instance aggregation.
- [x] Unified quick/report experiment config, CLI dry-run/resume and report-only re-export.
- [x] Five figure families sharing calculations and styles across exports and demo.
- [x] Demo current-run evaluation and standalone benchmark JSON upload/viewer.
- [x] Update documentation and run integrity, CLI, report and UI checks; inspect actual images.

## Integration contract

`src.evaluation` owns the standard-library data API:

- `make_evaluation(groups, preset="custom", provenance=None)` returns a JSON-ready envelope.
- Envelope: `schema_version: 1`, `kind: "warehouse_benchmark_evaluation"`,
  `preset`, `created_at_utc`, `provenance`, `groups`.
- Each group: `name`, `config` (resolved low-level benchmark config),
  `instance_fingerprints` (input inventory), `instances` (list of complete instance dictionaries),
  `results` (list of complete solver results).
- `validate_evaluation(payload)` raises InputError on invalid/incomplete evidence and returns payload.
- `load_evaluation(path_or_bytes)` parses JSON, validates, returns payload.
- `load_benchmark_group(path, name)` audits an existing low-level benchmark directory and builds a group.
- `snapshot_evaluation(snapshot)` creates a validated one-instance group named `current_run`.
- `evaluation_tables(payload, reference="B2")` returns dictionaries `summary`, `per_instance`, `raw_metrics`, each a list of flat rows.
- Rows always include `group`, `method`; instance rows also have `instance`, `n`, `instance_seed`, `distance_unit`, `time_unit`, `runs`.
- Per-instance statistics use `{metric}_mean`, `{metric}_std`, `{metric}_median`, `{metric}_best`, and `{metric}_improvement_pct` versus the selected reference. Metrics: objective/distance/makespan/tardiness/late_orders/on_time_rate/total_seconds.
- Summary rows: group/method/reference/instances/runs/win/tie/loss/percentage_instances/mean_improvement_pct plus per-metric mean improvement percentages, averaged over paired instance means. No physical-unit pooling across groups.

`src.evaluation_figures` owns reusable `figure_specs(payload, reference="B2", group=None, style="report")`.
Return list of dicts: `id`, `title`, `caption`, `figure` (Matplotlib figure or None), `reason` (why unavailable).
`figure_bytes(figure, format="png")` returns bytes. Styles report/presentation; no PowerPoint generation.

`src.evaluation_report.export_evaluation(payload, output, presentation=False, charts=True)`
validates evidence before writing a new output directory and produces tables, evaluation.json,
REPORT.md, figure availability metadata, report figures and optionally presentation figures.

`src.experiment` and CLI consume this API. Experiment groups live under datasets/<name>;
report output is experiment/report. Existing low-level benchmark formats remain readable.

Dataset families are separate. Search seeds are averaged within instances; repeated demand
seeds across sizes are correlated. Spread over seed runs is not a confidence interval.
Quick output is marked pipeline/demo evidence only. No benchmark is rerun during plotting.

## Completed verification

- Full suite: 286 tests passed, including existing solver checks and new integrity,
  archive recovery, export and Streamlit regression tests.
- Actual quick experiment: 10 instances, 80 independently audited solver runs across
  maps/scalability/Kris; 39 report image files and 90 presentation image files.
  Every presentation PNG/PDF/SVG preserves 16:9; multi-panel figures are split into
  individual images with 20-point labels.
- Completed resume: all 250 archived files remained byte-identical.
- Report-only re-export: portable evidence and all three CSV tables are reproduced
  byte-for-byte without calling a solver.
- Full report protocol dry-run: 45 instances and 1,440 solver runs; the long experiment
  has not been run to produce academic results.
- Real Edge browser: portable upload before simulation, shared-statistics CSV filtering,
  PDF download, presentation chart selection with exact 16:9 PNG download, and
  rejection of an invalid replacement;
  desktop/mobile screenshots saved alongside the acceptance results.
- Actual figures rendered and visually inspected; Ruff and whitespace checks passed.

Final quick evidence: `results/benchmark_unified_final_20261002/report/`.
Browser acceptance: `results/evaluation_browser_final_20261002/checks.json`.
