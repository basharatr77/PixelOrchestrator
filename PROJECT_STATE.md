# PixelOrchestrator — Project State

> Authoritative continuation checkpoint for active development.
> The repository is the source of truth.

---

## CURRENT CHECKPOINT

### Phase

Phase 36-B — Canonical Device Registry

### Status

COMPLETE

### Commit

79ae185 — Phase 36-B: establish canonical device registry

### Test Baseline

110 passed

Command:

    python -m pytest -q

Result:

    110 passed

### Compile Check

PASS

Command:

    python -m compileall -q .\app .\tests

### Diff Check

PASS

Command:

    git diff --check

### Working Tree

Clean after Phase 36-B commit.

---

# Phase 36-B — Canonical Device Registry

## Objective

Establish a clean canonical device registry around the existing
`app.core.module_contract.Device` contract without introducing another
Device model or mixing registry ownership with unrelated database code.

## Completed Changes

### Canonical Device Registry

Added:

    app/core/device_registry.py

`DeviceRegistry` stores canonical `Device` objects keyed by stable
`device_id`.

Supported operations:

- register
- get
- contains
- update
- remove
- snapshot
- clear

Duplicate registration is rejected.

Unknown-device updates are rejected.

Registry snapshots do not expose the internal registry mapping.

### Registry Persistence Boundary

The legacy registry implementation was removed from:

    app/db/database.py

`app/core/registry.py` remains the event/lifecycle persistence adapter used
by `BusRuntime`.

The in-memory `DeviceRegistry` is intentionally independent from SQLite,
event-bus implementation details, and vendor-specific logic.

### Tests

Added:

    tests/test_device_registry.py

Registry behavior is covered for:

- registration
- lookup
- duplicate prevention
- update
- removal
- missing-device removal
- snapshots
- snapshot isolation
- clear

## Verification

Test suite:

    110 passed

Compile:

    PASS

Diff check:

    PASS

Git working tree:

    CLEAN

## Architecture Baseline

The canonical device contract remains:

    app/core/module_contract.py

Device flow:

    Detector
        |
        v
    Canonical Device
        |
        v
    Device Registry
        |
        v
    Lifecycle Events
        |
        v
    Orchestrator

No duplicate Device model was introduced.

Legacy:

    app/agents/device_agent/device_model.py

remains removed.

Legacy:

    device.mode

remains prohibited.

---

# Known Limitations

1. ADB and Fastboot remain the primary detection transports.
2. The new DeviceRegistry is currently an in-memory canonical registry.
3. Lifecycle integration with DeviceRegistry is not yet complete.
4. Registry persistence and event synchronization remain separate concerns.
5. Additional lifecycle states and transition hardening remain future work.
6. GUI device-management integration remains future work.
7. AI provider integration remains incomplete.

---

# NEXT PHASE

## Phase 37 — Device State / Lifecycle Hardening

Status:

    NEXT

Objective:

Formalize device lifecycle transitions and ensure lifecycle events,
state synchronization, and invalid-transition handling are deterministic.

### Exact First Action

Before modifying code:

1. Inspect `DeviceState` in `app/core/module_contract.py`.
2. Inspect current lifecycle detection in
   `app/agents/device_agent/detector.py`.
3. Inspect lifecycle event consumers.
4. Search all `DeviceState` and lifecycle event references.
5. Map currently supported and unsupported transitions.
6. Add tests before changing implementation.

Do not mix GUI work into Phase 37.

---

# Resume Procedure

When continuing in a new chat:

1. Read `PROJECT_STATE.md`.
2. Read the relevant section of `PHASE_PLAN.md`.
3. Read `PROJECT_INSTRUCTIONS.md`.
4. Run:

    git status --short

5. Run:

    git log -1 --oneline

6. Verify the recorded test baseline if needed.
7. Continue from `NEXT PHASE`.
8. Do not repeat completed phases without repository evidence of regression.

---

# Historical Checkpoints

## Phase 35

Status:

    COMPLETE

Commit:

    3d30994

Description:

    Canonicalize device identity and transport state

Verification:

    102 passed
    compileall PASS
    git diff --check PASS

## Phase 36-B

Status:

    COMPLETE

Commit:

    79ae185

Description:

    Establish canonical device registry

Verification:

    110 passed
    compileall PASS
    git diff --check PASS
    working tree clean
