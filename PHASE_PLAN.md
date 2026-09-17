# PixelOrchestrator — Phase Plan

> Reconciled master roadmap.
> `PROJECT_STATE.md` contains the exact active checkpoint.
> This file distinguishes historical roadmap labels from the actual implementation path.

## PHASE STATUS

| Phase | Status | Area |
|---|---|---|
| 1–34 | COMPLETE / HISTORICAL | Foundation / early architecture |
| 35 | COMPLETE | Canonical Device Identity & Transport State |
| 36 | COMPLETE | Device Detection & Registry |
| 37 | COMPLETE | Device State / Lifecycle Hardening |
| 38 | COMPLETE | Unified Transport Layer Hardening |
| 39 | COMPLETE | Device Capability System |
| 40 | COMPLETE | Workflow / Task Execution Layer |
| 41 | SUBSTANTIALLY IMPLEMENTED / CONTRACT-VERIFIED | Persistent Event & Replay Infrastructure |
| 42 | COMPLETE | Device Farm / Multi-Device Orchestration |
| 43 | DEFERRED / NOT IMPLEMENTED | Worker Pool & Distributed Execution (original label) |
| 44 | COMPLETE | WebSocket / Remote Device Transport |
| 45 | COMPLETE | Agent Registry / Remote Device Ownership (actual implementation) |
| 46 | COMPLETE THROUGH 46-H | Agent Persistence / Identity / Security / Recovery (actual implementation) |
| 47 | PLANNED | Self-Healing / Auto-Repair Workflows |
| 48 | PLANNED | GUI Device Operations & UX |
| 49 | PLANNED | Production Hardening / Security / Observability |
| 50 | PLANNED | Release / Packaging / Deployment |

## 1–34 — FOUNDATION

Historical foundation and early architecture work. The current repository documentation does not preserve reliable individual checkpoints for every phase, so missing commit/test details are intentionally not invented.

## 35 — CANONICAL DEVICE IDENTITY & TRANSPORT STATE

Status: COMPLETE
Commit: `3d30994`
Validation: 102 passed.

Established canonical Device identity, DeviceState, ModuleType, stable device_id and explicit transport. Legacy device-model consumers were migrated.

## 36 — DEVICE DETECTION & REGISTRY

Status: COMPLETE

Established the canonical DeviceRegistry boundary for device discovery, registration, lookup, lifecycle integration and device existence.

## 37 — DEVICE STATE / LIFECYCLE HARDENING

Status: COMPLETE
Commit: `31e8613`
Validation: 118 passed; targeted lifecycle/state 12; BusRuntime integration 4; compileall PASS; diff check PASS.

Added DeviceStateMachine and integrated canonical DeviceRegistry lifecycle handling.

## 38 — UNIFIED TRANSPORT LAYER HARDENING

Status: COMPLETE
Validation: 118 passed at the established checkpoint.

Unified ADB/Fastboot transport abstraction, resolver/factory, error normalization, command execution, timeouts and availability checks.

## 39 — DEVICE CAPABILITY SYSTEM

Status: COMPLETE
Validation: 129 passed.

Established stable capability IDs, CapabilityRegistry, ModuleRegistry capability ownership, capability validation and structured unknown-action failure.

## 40 — WORKFLOW / TASK EXECUTION LAYER

Status: COMPLETE.

Major checkpoints:

- 40-A Task Contract — `0a3522b` — 14 Task tests; 143 full.
- 40-B Task Queue — `0e12c95` — 150 full.
- 40-C Canonical Execution — `1bbc156` — 160 full.
- 40-D Workflow Definition — `2e1a16f` — 169 full.
- 40-E DAG Readiness — `23c7749` — 176 full.
- 40-F-A Retry Policy — `bf52f7f` — 184 full.
- 40-F-B Retry Execution — `2278a16` — 189 full.
- 40-F-C Cancellation — `e66d62c` — 191 full.
- 40-G Progress — `9fb360b`, `7ebf3c0`, `4b7eae7`, `481e70b` — 31 targeted / 241 full at final orchestration checkpoint.
- 40-H Workflow Outcomes — `2c070ea`, `21b993b`, `db0bba5`.
- 40-I Workflow Orchestration — `d11241a`, `12d730d`, `ed0e894`, followed by terminal publication/tracking audits.

Canonical chain:

`Workflow → ready_tasks → WorkflowExecutor → TaskQueue → ExecutionWorker → TaskExecutor → ActionResult → BusRuntime → terminal publication`

## 41 — PERSISTENT EVENT & REPLAY INFRASTRUCTURE

Status: SUBSTANTIALLY IMPLEMENTED / CONTRACT-VERIFIED.

Verified areas include consumer offsets, replay batching, event fidelity, reconstruction, recovery dispatch, replay/live-log isolation, concurrent append behavior, bounded replay and recovery retry boundaries.

Known limitations: automatic startup recovery, workflow persistence, schema migration and event versioning were not established as universal guarantees.

## 42 — DEVICE FARM / MULTI-DEVICE ORCHESTRATION

Status: COMPLETE
Closure: 2026-09-06
Final audit: `02a64ca`
Validation: 247 full; compileall PASS.

Verified shared DeviceRegistry, identity/isolation, multi-device and concurrent execution, failure isolation and disconnect/reconnect.

Deferred: allocation/selection, reservation/lease, per-device queues, device health, availability and health monitoring.

## 43 — WORKER POOL & DISTRIBUTED EXECUTION

Original roadmap status: DEFERRED / NOT IMPLEMENTED.

The old roadmap defined worker registration, heartbeat, job assignment, retry, worker failure recovery, autoscaling foundation and queue isolation. Actual development did not complete this as a separate implementation phase; the project moved into WebSocket/remote-agent architecture instead.

Do not mark this complete without a new explicit contract and implementation evidence.

## 44 — WEBSOCKET / REMOTE DEVICE TRANSPORT

Status: COMPLETE.
Official closure: 44-I-AN-V.
Final known validation: 291 full.

Verified remote agent registration, connection loss/reconnect, identity lifecycle, malformed transport contracts and WebSocket boundary hardening.

## 45 — AGENT REGISTRY / REMOTE DEVICE OWNERSHIP

Status: COMPLETE.

45-C: `34b7f61` — remote agent device ownership; 13 targeted passed.

45-H: `522cb5c` — DeviceRegistry ownership boundary; 23 targeted / 323 full.

Verified ownership, registered-device existence, authentication, authorization and reconnect lifecycle.

Historical note: the original roadmap called Phase 45 “Plugin Architecture”. That label was superseded by actual implementation.

## 46 — AGENT PERSISTENCE / IDENTITY / SECURITY / RECOVERY

Status: COMPLETE THROUGH 46-H.

There is NO Phase 46-I.

- 46-A Persistent Agent Registry.
- 46-B Persistent Agent Identity — `b10f593`.
- 46-C Agent Device Ownership — `a8382e4`.
- 46-D Presence / Last Seen — `352285b`.
- 46-E Global Connection Policy — `591dba3`.
- 46-F Authentication Boundary — `570d8bb`.
- 46-G Authorization / Reconnect Lifecycle — `fdc16fd`.
- 46-H Crash / Restart Recovery — `c260314`.

46-H validation:
- `tests/test_agent_registry.py`: 25 passed.
- Full regression: 351 passed in 12.35s.

Persistent state: identity, device ownership, last_seen and registry knowledge.
Ephemeral state: active WebSocket connection, connection_id and live connection state.

Historical note: the original roadmap called Phase 46 “AI Diagnosis & Decision Engine”. That label was superseded by actual implementation.

## 47 — SELF-HEALING / AUTO-REPAIR WORKFLOWS

Status: PLANNED.

This remains a future roadmap area. It must not begin until deterministic safety boundaries, recovery contracts and observability requirements are explicitly defined.

## 48 — GUI DEVICE OPERATIONS & UX

Status: PLANNED.

Production-facing GUI around the stable backend, including device operations, diagnostics, reporting, configuration and user-facing error handling.

## 49 — PRODUCTION HARDENING / SECURITY / OBSERVABILITY

Status: PLANNED.

Production error handling, secrets/configuration, crash recovery, performance, concurrency, security and observability.

## 50 — RELEASE / PACKAGING / DEPLOYMENT

Status: PLANNED.

Reproducible packaging, deployment, release validation and production distribution.

## NEXT IMPLEMENTATION DECISION

After this documentation reconciliation, do not automatically jump to Phase 47.

The next implementation checkpoint must be explicitly selected from the current architecture gaps. Candidate areas are:

1. Device allocation / selection deferred by Phase 42.
2. Worker pool / distributed execution deferred by original Phase 43.
3. Reconciliation and real-hardware reliability.
4. Observability / production hardening.
5. AI diagnosis / self-healing after deterministic safety contracts.

The chosen checkpoint must be RED-first, narrowly scoped, regression-preserving and committed independently of unrelated working-tree changes.
