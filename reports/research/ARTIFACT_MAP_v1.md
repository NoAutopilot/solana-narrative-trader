# Artifact Map v1 — Solana Narrative Trader

**Date:** 2026-03-13
**Purpose:** Single reference for every important file in the project.

---

## Active Collection

| File | Purpose | Status |
|------|---------|--------|
| `feature_tape_v2.py` | 15-min fire collector — writes feature_tape_v2 table | **FROZEN — do not modify** |
| `deploy/solana-feature-tape-v2.service` | systemd unit for collector | Active on VPS |
| `ops/feature_tape_v2_autopilot.sh` | Master orchestrator — waits for 96 fires + maturity, runs sweep | Pending launch |
| `ops/feature_tape_v2_wait_for_completion.sh` | Polls until 96 fires collected | Called by autopilot |
| `ops/feature_tape_v2_wait_for_label_maturity.sh` | Waits for all label horizons to mature | Called by autopilot |
| `ops/feature_tape_v2_freeze_dataset.sh` | Freezes dataset, writes manifest + CSV export | Called by autopilot |
| `ops/run_feature_tape_v2_final_sweeps.sh` | Runs all 5 horizon sweeps + holdout + benchmark | Called by autopilot |

---

## Analysis Scripts

| File | Purpose | When to Run |
|------|---------|-------------|
| `scripts/final_sweep_v2.py` | Full sweep across all 5 horizons (eligible-only primary) | After dataset freeze |
| `scripts/holdout_sweep_v2.py` | 75/25 temporal holdout, 8 promotion gates, 6 kill gates | After full sweep |
| `scripts/benchmark_comparator_v2.py` | Compare candidate vs v1 benchmark suite + no-go registry | After holdout |
| `scripts/red_team_validation_battery.py` | 7-module adversarial validation battery | After benchmark comparison |
| `scripts/generate_manifest.py` | Generate JSON provenance manifest for any run | Before any sweep |
| `scripts/generate_final_recommendation.py` | Produce final PROCEED/PIVOT/STOP recommendation memo | After all gates |
| `scripts/build_external_review_packet.py` | Generate external review packet (markdown/yaml/json) | On demand |
| `scripts/build_status_packet.py` | Generate compact current-state status packet | On demand |

---

## Large-Cap Swing Study (Deferred)

| File | Purpose | When to Run |
|------|---------|-------------|
| `scripts/dynamic_universe_builder.py` | Build point-in-time large-cap universe from frozen tape | After PIVOT verdict |
| `scripts/ohlcv_loader.py` | Fetch historical OHLCV candles (GeckoTerminal/Birdeye) | After universe built |
| `scripts/stageA_data_qc.py` | QA guardrails — survivorship bias, coverage, continuity | After OHLCV loaded |

---

## Contract Tests

| File | Purpose | When to Run |
|------|---------|-------------|
| `tests/feature_tape_v2_contract_test.py` | 10 schema/semantic contract tests | Before any sweep; after freeze |

---

## Research Docs

| File | Purpose |
|------|---------|
| `reports/research/CURRENT_STATE.md` | Authoritative current state snapshot |
| `reports/research/OPERATOR_RUNBOOK_v1.md` | Step-by-step operator procedures |
| `reports/research/DECISION_TREE_v1.md` | All possible outcomes and allowed next moves |
| `reports/research/ARTIFACT_MAP_v1.md` | This file |
| `reports/research/COMMAND_INDEX_v1.md` | Exact one-liner commands for all operations |
| `reports/research/feature_tape_v2_source_map.md` | Every v2 column: source type, null semantics, analysis scope |
| `reports/research/feature_tape_v2_analysis_views.md` | Primary (eligible-only) vs secondary (full-universe) view rules |
| `reports/research/feature_v2_holdout_pipeline.md` | Holdout design: 75/25 split, 8 promotion gates, 6 kill gates |
| `reports/research/benchmark_comparator_spec.md` | Benchmark comparator design |
| `reports/research/red_team_validation_battery_spec.md` | Red-team battery: 7 modules, PASS/FRAGILE/FAIL |
| `reports/research/red_team_validation_battery_template.md` | Expected output format for battery report |
| `reports/research/feature_tape_contract_spec.md` | Contract test spec: 10 tests |
| `reports/research/provenance_manifest_spec.md` | Manifest standard: git commit, SHA-256, DB path, etc. |
| `reports/research/external_review_packet_template.md` | External review packet template (markdown) |
| `reports/research/external_review_packet_template.yaml` | External review packet template (yaml) |
| `reports/parallel_sprint/largecap_swing/stageA_data_scaffold.md` | Large-cap swing data scaffold design |
| `reports/parallel_sprint/largecap_swing/stageA_design.md` | Stage A study design |
| `reports/parallel_sprint/largecap_swing/stageA_results.md` | Stage A results (from v1 data) |
| `reports/parallel_sprint/largecap_swing/stageA_summary.md` | Stage A summary |
| `reports/parallel_sprint/decision_matrix.md` | Three-workstream decision matrix |
| `reports/parallel_sprint/final_recommendation.md` | Sprint-level recommendation |

---

## Ops Docs

| File | Purpose |
|------|---------|
| `reports/ops/feature_tape_v2_deploy_instructions.md` | VPS deploy + service start instructions |
| `reports/ops/feature_tape_v2_semantic_rules.md` | 5 ratified semantic rules for v2 |
| `reports/ops/feature_tape_v2_source_map.md` | Earlier source map (superseded by research version) |
| `reports/ops/feature_tape_v2_unavailable_fields.md` | Fields removed from v2 due to unavailability |

---

## Synthesis / Closure Memos

| File | Purpose |
|------|---------|
| `reports/synthesis/feature_tape_v1_closure_memo.md` | v1 tape closure — lessons learned |
| `reports/synthesis/feature_acquisition_v2_design_note.md` | v2 feature acquisition design rationale |
| `reports/synthesis/feature_tape_v2_label_maturity.md` | Label maturity report (generated by autopilot) |
| `reports/synthesis/feature_tape_v2_final_manifest.json` | Final provenance manifest (generated by autopilot) |
| `reports/synthesis/feature_family_sweep_v2_final_recommendation.md` | **THE FINAL RECOMMENDATION** (generated by autopilot) |

---

## Benchmark / Registry

| File | Purpose |
|------|---------|
| `reports/synthesis/benchmark_suite_v1.md` | v1 momentum sweep results — baseline ceiling |
| `reports/synthesis/no_go_registry_v1.md` | 11 features proven to have no edge — never re-test |
| `reports/research/dataset_index.md` | All source tables, schemas, and update frequencies |

---

## Reconciliation

| File | Purpose |
|------|---------|
| `reports/reconciliation/pfm_1677a7da_reconciliation.md` | Failed observer post-mortem |
| `reports/reconciliation/pfm_1677a7da_reconciliation.csv` | Trade-level reconciliation data |

---

## Memory Layer

| File | Purpose |
|------|---------|
| `reports/research/LEARNINGS_LEDGER.md` | Cumulative lessons learned across all experiments |
| `reports/research/EXPERIMENT_INDEX.md` | Index of all experiments with status and outcome |
