# PixelOrchestrator â€” Phase Plan

> Master architectural roadmap.
> PROJECT_STATE.md contains the exact current checkpoint.
> This file contains the broader development sequence.

---

# Project Vision

PixelOrchestrator is evolving into a:

- Android Device Orchestrator
- Distributed Automation Platform
- Device Farm Controller
- Smart Repair Infrastructure

The architecture should remain:

    modular
    event-driven
    testable
    transport-agnostic
    extensible
    recoverable
    automation-ready

---

# PHASE STATUS

| Phase | Area | Status |
|---|---|---|
| 1â€“34 | Earlier architecture and foundation work | COMPLETE |
| 35 | Canonical Device Identity & Transport State | COMPLETE |
| 36 | Device Detection & Registry | COMPLETE |
| 37 | Device State / Lifecycle Hardening | COMPLETE |
| 38 | Unified Transport Layer Hardening | COMPLETE |
| 39 | Device Capability System | COMPLETE |
| 40 | Workflow / Task Execution Layer | IN PROGRESS |
| 41 | Persistent Event & Replay Infrastructure | PLANNED |
| 42 | Device Farm / Multi-Device Orchestration | PLANNED |
| 43 | Worker Pool & Distributed Execution | PLANNED |
| 44 | WebSocket / Remote Device Transport | PLANNED |
| 45 | Plugin Architecture | PLANNED |
| 46 | AI Diagnosis & Decision Engine | PLANNED |
| 47 | Self-Healing / Auto-Repair Workflows | PLANNED |
| 48 | GUI Device Operations & UX | PLANNED |
| 49 | Production Hardening / Security / Observability | PLANNED |
| 50 | Release / Packaging / Deployment | PLANNED |

---

# PHASE 35 â€” Canonical Device Identity & Transport State

Status:

    COMPLETE

Commit:

    3d30994

Objective:

Replace the legacy device model with the canonical Device contract.

Key results:

- Canonical `Device`
- Canonical `DeviceState`
- Canonical `ModuleType`
- Stable `device_id`
- Explicit transport
- Legacy `device_model.py` removed
- Legacy `device.mode` consumers removed
- Detector migration completed
- Transport resolver migration completed
- Tests updated

Verification:

    102 passed
    compileall PASS
    git diff --check PASS

---

# PHASE 36 â€” Device Detection & Registry

Status:

    NEXT

Objective:

Create a reliable registry around canonical devices.

Scope:

- Device registration
- Device lookup
- Device removal
- Device update
- Duplicate prevention
- Lifecycle integration
- ADB device registration
- Fastboot device registration
- Registry snapshots
- Registry tests

Architecture target:

    ADB Detector
          \
           \
    Fastboot Detector
            |
            v
    Canonical Device
            |
            v
      Device Registry
            |
            v
      Lifecycle Events

Rules:

- No duplicate Device model.
- Registry must consume canonical `Device`.
- Serial/device_id identity must be deterministic.
- Registry behavior must be testable independently.
- Do not mix unrelated GUI work into this phase.

---

# PHASE 37 â€” Device State / Lifecycle Hardening

Status:

    COMPLETE

Commit:

    31e8613

Objective:

Formalize device lifecycle transitions and integrate canonical state
synchronization into the lifecycle runtime.

Key results:

- Added `DeviceStateMachine`
- Added lifecycle transition validation
- Added invalid-transition protection
- Integrated `DeviceRegistry` into `LifecycleConsumer`
- Integrated canonical `Device` creation into lifecycle handling
- Integrated state transitions with lifecycle events
- Preserved task generation and BusRuntime execution behavior
- Added dedicated state-machine tests

Verification:

    118 passed
    targeted lifecycle/state tests: 12 passed
    bus runtime integration tests: 4 passed
    compileall PASS
    git diff --check PASS
    working tree clean

---

# PHASE 38 â€” Unified Transport Layer Hardening


Objective:

Make ADB/Fastboot and future transports conform to one stable transport abstraction.

Scope:

- Transport interface
- ADB transport
- Fastboot transport
- Transport resolver
- Transport factory
- Error normalization
- Command execution
- Timeouts
- Device availability checks

Future transports can later plug into the same architecture.

---

# PHASE 39 â€” Device Capability System

Objective:

Represent what each device/module can actually do.

Scope:

- Capability discovery
- Capability registry
- Module capabilities
- Device capabilities
- Capability validation
- Unsupported-operation handling

Examples:

- ADB shell
- reboot
- bootloader
- fastboot flash
- diagnostics
- recovery operations

---

# PHASE 40 â€” Workflow / Task Execution Layer

Objective:

Turn individual operations into reliable workflows.

Scope:

- Tasks
- Task queue
- Task executor
- Workflow definitions
- DAG dependencies
- Retry policies
- Cancellation
- Progress events
- Failure handling

---

# PHASE 41 â€” Persistent Event & Replay Infrastructure

Objective:

Provide reliable event persistence and recovery.

Scope:

- Event store
- Event bus
- Event broker
- Deduplication
- Replay engine
- Persistence policies
- Recovery
- Idempotency

Target:

    Event
      |
      +--> Bus
      +--> Store
      +--> Consumers
      +--> Replay

---

# PHASE 42 â€” Device Farm / Multi-Device Orchestration

Objective:

Operate many devices concurrently.

Scope:

- Device pools
- Device selection
- Device reservations
- Parallel execution
- Per-device queues
- Resource limits
- Device health

---

# PHASE 43 â€” Worker Pool & Distributed Execution

Objective:

Move execution from a single process toward scalable workers.

Scope:

- Worker registration
- Worker heartbeat
- Job assignment
- Retry
- Worker failure recovery
- Autoscaling foundation
- Queue isolation

---

# PHASE 44 â€” WebSocket / Remote Device Transport

Objective:

Support remote orchestration.

Scope:

- WebSocket transport
- Remote device agents
- Secure communication
- Heartbeats
- Remote lifecycle events
- Connection recovery

---

# PHASE 45 â€” Plugin Architecture

Objective:

Allow vendor/device modules to be added without destabilizing the core.

Potential modules:

- Pixel
- Qualcomm
- MediaTek
- Samsung/Odin
- Unisoc
- Generic Android

Rules:

- Plugin isolation
- Explicit contracts
- Capability declarations
- Versioning
- Failure isolation

---

# PHASE 46 â€” AI Diagnosis & Decision Engine

Objective:

Use AI for diagnosis and intelligent decision support.

Scope:

- Log analysis
- Error classification
- Root-cause analysis
- Suggested remediation
- Provider abstraction
- AI decision engine
- Confidence / safety boundaries

AI must not bypass deterministic safety checks.

---

# PHASE 47 â€” Self-Healing / Auto-Repair Workflows

Objective:

Allow the orchestrator to diagnose and recover devices automatically.

Pipeline:

    Error
      |
      v
    Diagnostics
      |
      v
    AI / Rule Engine
      |
      v
    Safe Repair Plan
      |
      v
    Approval / Policy
      |
      v
    Execution
      |
      v
    Verification
      |
      v
    Recovery / Escalation

---

# PHASE 48 â€” GUI Device Operations & UX

Objective:

Build the production-facing GUI around the stable backend.

GUI should expose:

- Device dashboard
- Connected devices
- Device state
- Device details
- Transport
- Capabilities
- Device Manager shortcut
- Drivers shortcut
- Logs
- Tasks
- Workflows
- AI assistant
- Diagnostics
- Repair operations
- Progress/status
- Error reporting

Important:

GUI should consume backend contracts instead of implementing device logic independently.

---

# PHASE 49 â€” Production Hardening

Objective:

Prepare the platform for reliable real-world use.

Scope:

- Security
- Authentication
- Authorization
- Logging
- Metrics
- Structured diagnostics
- Error reporting
- Configuration
- Secrets management
- Crash recovery
- Performance
- Concurrency testing

---

# PHASE 50 â€” Release / Packaging / Deployment

Objective:

Create a reproducible production release.

Scope:

- Windows packaging
- Dependency validation
- Platform-tools packaging strategy
- Driver installation guidance
- Configuration
- Installer
- Versioning
- Release checks
- Documentation
- Final test matrix

---

# Phase Completion Gate

Every phase must satisfy:

1. Implementation complete.
2. Tests added/updated.
3. `python -m compileall -q .\app .\tests` passes.
4. `python -m pytest -q` passes.
5. `git diff --check` passes.
6. Architecture reference audit passes.
7. No accidental unrelated changes.
8. `PROJECT_STATE.md` updated.
9. Git commit created.
10. Commit recorded in `PROJECT_STATE.md`.
11. Next exact phase identified.

---

# Important Rule

Do not advance phases merely because code exists.

Advance only when the phase's architectural objective is verified.

The repository is the source of truth.

---

# Phase 40-A â€” Task Contract

Status:

    COMPLETE

Commit:

    0a3522b

Objective:

Define a canonical execution unit for the Phase 40 workflow layer.

Implemented:

- Task contract
- TaskStatus lifecycle
- UUID task identity
- device/module/action targeting
- parameters
- ActionResult integration
- attempts
- lifecycle timestamps
- cancellation
- lifecycle validation
- defensive parameter copying

Verification:

    14 Task contract tests passed
    143 full regression tests passed
    compileall PASS
    git diff --check PASS

Next checkpoint:

    Phase 40-B â€” Task Queue

---


---

# Phase 40-B-A â€” Task Queue Checkpoint

Status:

    COMPLETE

Commit:

    0e12c95

Objective:

Implement the FIFO task queue required by the Phase 40 orchestration layer.

Implemented:

- FIFO TaskQueue using deque
- add_task()
- pop_task()
- peek_task()
- size()
- is_empty()
- clear()
- empty-queue behavior
- canonical Phase 40 Task compatibility
- legacy caller compatibility
- list-compatible snapshot via tasks property

Verification:

    7 Task Queue tests passed
    9 execution/lifecycle compatibility tests passed
    150 full regression tests passed
    compileall PASS
    git diff --check PASS

Decision:

    The Phase 40-B Task Queue contract is fully implemented.
    No additional B-B queue behavior is required at this checkpoint.
    TaskExecutor/ExecutionWorker migration to the canonical Task contract
    remains outside the completed queue scope.

Next checkpoint:

    Phase 40-C â€” Task Execution Layer

---

---

# Phase 40-C-B ? Canonical Execution Path Checkpoint

Status:

    COMPLETE

Commit:

    1bbc156

Objective:

    Migrate the execution path to the canonical Task contract while
    preserving existing execution compatibility.

Implemented:

- ExecutionWorker forwards canonical Task objects.
- TaskExecutor executes canonical Tasks through ModuleRegistry and
  DeviceRegistry.
- BusRuntime accepts canonical Tasks through the execution queue.
- ActionResult remains the execution result object.
- TASK_EXECUTED event payloads are serialized to JSON-safe dictionaries.
- Legacy task execution behavior remains compatible.

Verification:

    Targeted execution/lifecycle regression:
    13 passed in 0.95s

    Full regression:
    160 passed in 10.33s

    Compile:
    PASS

    Diff check:
    PASS

Decision:

    Canonical Task execution is now integrated through the queue,
    worker, executor, and BusRuntime event boundary.

Next:

    Continue Phase 40 workflow execution design, with the next
    checkpoint determined from the remaining workflow/DAG/retry/
    cancellation/progress requirements.

## Phase 40-D â€” Workflow Definition Contract

Status: COMPLETE

Implementation commit:
- `2e1a16f` â€” `Implement Phase 40-D workflow definition contract`

Objective:
- Introduce a canonical Workflow definition that groups canonical Tasks and declares task dependencies without owning execution behavior.

Implementation:
- Added `app/core/workflow.py`
- Added `tests/test_workflow.py`
- Workflow provides:
  - globally unique workflow ID
  - canonical `Task` collection
  - defensive task-list copy
  - task dependency mapping by Task ID
  - duplicate Task ID rejection
  - unknown dependency rejection
  - self-dependency rejection
  - Task type validation
  - dependency type validation
- Workflow intentionally does not own queueing, execution, retry policy, cancellation, progress reporting, or failure handling.

Verification:
- Workflow targeted tests: 9 passed
- Phase 40 targeted regression: 41 passed
- Full regression: 169 passed
- `compileall`: PASS
- `git diff --check`: PASS
- Final staged scope: only `app/core/workflow.py` and `tests/test_workflow.py`
- BOM audit: PASS

Architectural decision:
- `Task` remains the individual execution unit and owns execution lifecycle.
- `Workflow` groups Tasks and owns dependency structure only.
- Execution remains in TaskQueue / ExecutionWorker / TaskExecutor.
- Retry, cancellation, progress events, and failure handling remain separate Phase 40 boundaries.

Next checkpoint:
- Phase 40-E â€” Workflow DAG dependency validation/execution readiness.
- Before implementation, inspect the Workflow dependency contract for cycle detection and dependency readiness semantics.
- Preserve the 169-test baseline and do not stage unrelated working-tree changes.

## Phase 40-E â€” DAG Dependency Validation / Execution Readiness

Status: COMPLETE

Implementation commit:
- `23c7749` â€” `Implement Phase 40-E DAG readiness`

Objective:
- Validate Workflow dependency graphs as DAGs and determine which canonical Tasks are execution-ready without introducing workflow execution itself.

Implementation:
- Added cycle detection through dependency-graph traversal.
- Added `validate_dag()` to reject dependency cycles.
- Added `ready_tasks()` to identify pending Tasks whose dependencies are all COMPLETED.
- Dependency-free pending Tasks are immediately ready.
- Tasks with PENDING, RUNNING, FAILED, or CANCELLED dependencies are not ready.
- Ready Tasks preserve Workflow declaration order.
- No execution engine, retry policy, cancellation policy, progress reporting, or failure orchestration was added.

Verification:
- Phase 40-E Workflow tests: 16 passed
- Full regression: 176 passed
- `compileall`: PASS
- `git diff --check`: PASS
- Staged implementation scope: only `app/core/workflow.py` and `tests/test_workflow.py`

Architectural decision:
- `Workflow` owns dependency graph validation and execution-readiness calculation.
- `Task` continues to own individual execution lifecycle.
- `TaskQueue`, `ExecutionWorker`, and `TaskExecutor` continue to own execution mechanics.
- Workflow execution remains a future boundary.
- Retry, cancellation, progress events, and failure handling remain separate Phase 40 boundaries.

Next checkpoint:
- Phase 40-F-A — Retry Policy Contract.
- Before implementation, define how RetryPolicy integrates with TaskExecutor retry execution semantics.
- Preserve the 184-test baseline and do not stage unrelated working-tree changes.

## Phase 40-F-A — Retry Policy Contract

Status: COMPLETE

Implementation commit:
- `bf52f7f` — `Implement Phase 40-F-A retry policy contract`

Objective:
- Introduce an explicit RetryPolicy contract without changing TaskExecutor retry execution.

Implementation:
- Added `app/core/retry_policy.py`.
- Added `tests/test_retry_policy.py`.
- `RetryPolicy.max_attempts` represents total execution attempts, including the initial attempt.
- Failed `ActionResult` values may be retried while attempts remain.
- Successful results are never retried.
- Retry backoff, cancellation, progress events, and workflow execution remain outside this checkpoint.

Verification:
- RetryPolicy targeted tests: 8 passed
- Full regression: 184 passed
- `compileall`: PASS
- `git diff --check`: PASS
- BOM audit: PASS

Architectural decision:
- `RetryPolicy` owns retry-decision semantics.
- `Task.attempts` remains the authoritative cumulative attempt counter.
- Task lifecycle remains unchanged in 40-F-A.
- TaskExecutor retry execution semantics remain the next boundary.
- No `RETRYING` TaskStatus was introduced.
- No backoff or retry scheduling was introduced.

Next checkpoint:
- Phase 40-F-B — Retry Execution Semantics.
- Define and test TaskExecutor retry behavior while preserving canonical Task lifecycle correctness.
- Preserve the 184-test baseline and do not stage unrelated working-tree changes.

---

## Phase 40-F-B � Retry Execution Semantics

Status: COMPLETE

Implementation commit:

- `2278a16` � `Implement Phase 40-F-B retry execution semantics`

Objective:

- Integrate `RetryPolicy` into canonical `TaskExecutor` execution while
  preserving Task lifecycle correctness and cumulative attempt tracking.

Implemented:

- Added `Task.retry()` for `RUNNING -> PENDING` intermediate retry transitions.
- Integrated `RetryPolicy` into `TaskExecutor`.
- Retry attempts execute the canonical module action again while attempts remain.
- Successful execution completes the Task.
- Final failure marks the Task as `FAILED`.
- Execution exceptions become `EXECUTION_ERROR` results and are retryable.
- Module/action/device preflight failures remain terminal and non-retryable.
- Legacy dictionary-task execution remains unchanged.
- No `RETRYING` status, backoff, or retry scheduling was introduced.

Verification:

- Focused Phase 40 execution/retry tests: 41 passed
- Full regression: 189 passed in 8.15s
- `compileall`: PASS
- `git diff --check`: PASS

Architectural decision:

- `RetryPolicy` owns retry decisions.
- `Task.attempts` is the authoritative cumulative attempt counter.
- `Task` owns execution-attempt lifecycle state.
- `TaskExecutor` applies RetryPolicy around canonical module execution.
- Retry, cancellation, progress, and workflow execution remain separate concerns.

Next checkpoint:

- Inspect the remaining Phase 40 cancellation/progress/failure boundaries
  before selecting the next implementation boundary.

---

## Phase 40-F-C — Cancellation Execution Semantics

Status: COMPLETE

Commit:

    e66d62c

Phase 40-F-C establishes the canonical cancellation execution boundary.

ExecutionWorker now consumes cancelled canonical Tasks from the queue
without forwarding them to TaskExecutor. A Task cancelled before worker
execution remains CANCELLED and retains attempts == 0.

Verification:

- ExecutionWorker cancellation tests: 6 passed
- Focused Phase 40 integration: 63 passed
- Full regression: 191 passed in 7.34s
- compileall: PASS
- git diff --check: PASS

The legacy dictionary-task execution path remains unchanged. No forced
interruption of already-running synchronous module execution was introduced.
Retry semantics remain unchanged.

Next checkpoint:

- Inspect the remaining Phase 40 progress-event and failure-handling
  boundaries before selecting the next implementation checkpoint.

---

---

## Phase 40-G-A — Progress Event Contract

Status: COMPLETE

Implementation commit:

- `9fb360b` — `Implement Phase 40-G-A progress event contract`

Implemented:

- Added canonical `TASK_PROGRESS` event validation.
- Required non-empty `task_id`.
- Required integer `progress` from 0 through 100 inclusive.
- Boolean and invalid progress values are rejected.
- Optional `message` must be a string.
- Existing event types and `TASK_EXECUTED` remain unchanged.
- Progress events do not alter Task lifecycle/status.
- Progress is per execution attempt, not cumulative retry percentage.
- Task, TaskExecutor, Workflow, and RetryPolicy do not own progress publication.

Verification:

- G-A targeted tests: 7 passed
- Canonical task event regression: 3 passed
- Full regression: 198 passed in 11.72s
- `compileall`: PASS
- `git diff --check`: PASS
- BOM audit: PASS

Next checkpoint:

- Phase 40-G-B — Progress Event Publication Boundary.
- Inspect the canonical TaskExecutor/ExecutionWorker/BusRuntime boundary.
- Define the smallest safe mechanism for publishing `TASK_PROGRESS`.
- Preserve `TASK_EXECUTED`, retry, cancellation, and legacy dictionary-task behavior.
- Do not stage unrelated working-tree changes.

---

## Phase 40-G-B - Progress Event Publication Boundary

Status: COMPLETE

Implementation commit:

- `7ebf3c0` - `Implement Phase 40-G-B progress event publication boundary`

Implemented:

- Added an optional progress callback to the canonical TaskExecutor.
- TaskExecutor reports attempt-boundary progress.
- BusRuntime owns TASK_PROGRESS event construction and publication.
- TASK_EXECUTED, retry, cancellation, and legacy dictionary-task behavior remain unchanged.
- Progress remains per execution attempt.

Verification:

- G-B targeted tests: 2 passed
- Focused Phase 40 regression: 38 passed
- Full regression: 200 passed in 10.68s
- `compileall`: PASS
- `git diff --check`: PASS
- BOM audit after cleanup: PASS

Affected files:

    app/agents/orchestrator/task_executor.py
    app/core/bus_runtime.py
    tests/test_task_progress_publication.py

Next checkpoint:

- Phase 40-G-C - Workflow Progress Aggregation.

---

## Phase 40-G-C - Workflow Progress

Status: COMPLETE

Implementation commit:

- `4b7eae7` - `Implement Phase 40-G-C workflow progress`

Implemented:

- Added derived `Workflow.progress()` returning 0 through 100.
- Progress is based on completed tasks divided by total tasks.
- Empty workflows return 0.
- Failed and cancelled tasks are not counted as completed.
- Workflow does not own EventBus publication.

Verification:

- G-C targeted tests: 5 passed
- Targeted Phase 40 regression: 59 passed
- Full regression: 205 passed in 16.55s
- `compileall`: PASS
- `git diff --check`: PASS
- BOM audit after cleanup: PASS

Affected files:

    app/core/workflow.py
    tests/test_workflow_progress.py

Next checkpoint:

- Phase 40-G-D-A - Workflow Progress Publication Boundary.

---

## Phase 40-G-D-A - Workflow Progress Publication Boundary

Status: COMPLETE

Implementation commit:

- `481e70b` - `Implement Phase 40-G-D workflow progress publication`

Implemented:

- Added explicit BusRuntime workflow progress publication.
- BusRuntime publishes `WORKFLOW_PROGRESS`.
- Payload contains `workflow_id`, `progress`, and `message`.
- Workflow remains free of EventBus ownership.
- Task-level TASK_PROGRESS remains separate from workflow-level progress.
- TASK_EXECUTED, retry, and cancellation semantics remain unchanged.

Verification:

- G-D-A targeted tests: 3 passed in 0.88s
- Focused Phase 40 regression: 43 passed in 4.35s
- Full regression: 208 passed in 11.65s
- `compileall`: PASS
- `git diff --check`: PASS
- Architecture/reference audit: PASS
- BOM audit: PASS

Affected files:

    app/core/bus_runtime.py
    tests/test_workflow_progress_publication.py

G-D-A commit scope: only app/core/bus_runtime.py and
    tests/test_workflow_progress_publication.py

Known limitations:

- Workflow progress publication is currently an explicit BusRuntime boundary API.
- No automatic workflow orchestration loop was introduced.
- No UI workflow-progress consumer was introduced.
- No persistent workflow-progress state was introduced.

Next checkpoint:

- Inspect the remaining Phase 40 failure-handling boundaries before selecting the next implementation checkpoint.

---
## Phase 40-H-A - Workflow Outcome Contract

Status: COMPLETE

Commit:
    2c070ea Implement Phase 40-H-A workflow outcome contract

Implemented:

- Added derived Workflow.status() outcome semantics.
- FAILED takes precedence over CANCELLED.
- COMPLETED requires all tasks to be completed.
- RUNNING requires at least one running task with no terminal failure/cancellation.
- PENDING remains the outcome for otherwise non-terminal workflows, including blocked pending dependencies.
- No BLOCKED workflow status was introduced.
- Workflow remains free of EventBus ownership and publication.

Verification:

- RED: 7 expected failures.
- GREEN: 7 passed.
- Focused Phase 40 regression: 59 passed in 3.32s.
- Full regression: 215 passed in 10.58s.
- git diff --check: PASS.
- BOM audit: PASS.

Affected files:

    app/core/workflow.py
    tests/test_workflow_status.py

Known limitations:

- Status is derived and not persisted.
- No automatic workflow orchestration loop was added.
- No workflow terminal event publication was added.
- Empty-workflow status remains intentionally unspecified.

Next checkpoint:

- Define the next workflow failure-handling/publication boundary without
  moving orchestration responsibilities into Workflow.

---

## Phase 40-H-B - Workflow Failure Handling / Terminal State

Status: COMPLETE

Implementation commit:

- `21b993b` - `H-B Add workflow terminal state handling`

Implemented:

- Added derived `Workflow.is_terminal()`.
- completed, failed, and cancelled are terminal outcomes.
- pending and running are non-terminal.
- FAILED retains precedence over CANCELLED.
- Workflow remains free of EventBus ownership and execution orchestration.
- Failed dependencies remain unavailable to dependent tasks.

Verification:

- Workflow failure-handling tests: 4 passed.
- Workflow terminal tests: 6 passed.
- Focused Phase 40 regression: 99 passed in 5.80s.
- Full regression: 225 passed in 19.58s.
- `compileall`: PASS.
- `git diff --check`: PASS.
- BOM audit: PASS.

Affected files:

    app/core/workflow.py
    tests/test_workflow_failure_handling.py
    tests/test_workflow_terminal.py

Known limitations:

- Terminal state remains derived.
- No workflow terminal event publication was added.

Next checkpoint:

- Phase 40-H-C - Workflow Terminal Outcome Publication Boundary.

---

## Phase 40-H-C - Workflow Terminal Outcome Publication Boundary

Status: COMPLETE

Implementation commit:

- `db0bba5` - `Implement workflow terminal outcome publication`

Implemented:

- Added explicit `BusRuntime.publish_workflow_terminal_outcome(workflow)`.
- `WORKFLOW_COMPLETED`, `WORKFLOW_FAILED`, and `WORKFLOW_CANCELLED`
  are published for the corresponding terminal workflow outcomes.
- Non-terminal workflows publish no terminal outcome.
- Payload contains `workflow_id` and derived `status`.
- Workflow remains free of EventBus ownership.
- Existing task-level and workflow-progress semantics remain unchanged.

Verification:

- Valid RED: expected missing `BusRuntime.publish_workflow_terminal_outcome`.
- GREEN: 4 passed in 0.55s.
- Focused Phase 40 regression: 99 passed in 6.79s.
- Full regression: 229 passed in 11.32s.
- `compileall`: PASS.
- `git diff --check`: PASS.
- BOM audit: PASS.
- Exact staged scope: PASS.

Affected files:

    app/core/bus_runtime.py
    tests/test_workflow_terminal_publication.py

Known limitations:

- Terminal outcome publication is an explicit BusRuntime boundary API.
- No automatic workflow orchestration loop was introduced.
- No separate persisted workflow terminal state was introduced.

Next checkpoint:

- Audit the next Phase 40 workflow execution/integration boundary.

---
---

## Phase 40-I-A / I-B - Workflow Scheduling Boundary and BusRuntime Integration

Status: COMPLETE

Implementation commits:

- `d11241a` - `Implement Phase 40-I-A workflow scheduling boundary`
- `12d730d` - `Integrate workflow scheduling with BusRuntime`

Implemented:

- Added WorkflowExecutor as the canonical workflow scheduling boundary.
- Ready canonical Tasks are derived from `Workflow.ready_tasks()` and enqueued
  into the existing TaskQueue.
- WorkflowExecutor remains a scheduling boundary only; it does not execute
  tasks, own retry policy, publish events, or own workflow lifecycle state.
- BusRuntime now owns WorkflowExecutor and connects it to the existing
  TaskQueue.
- Added `BusRuntime.enqueue_workflow_ready_tasks(workflow)` as the explicit
  runtime scheduling integration boundary.
- Existing TaskExecutor, ExecutionWorker, Task lifecycle, retry, cancellation,
  progress, and workflow terminal publication semantics remain unchanged.

Verification:

- Targeted workflow scheduling/runtime integration tests: 5 passed in 0.44s.
- Full regression: 234 passed in 8.84s.
- `compileall`: PASS.
- `git diff --check`: PASS.
- BOM audit: PASS.
- Exact Phase 40-I implementation scope: clean.
- Unrelated working-tree changes remain unstaged.

Affected files:

    app/agents/orchestrator/workflow_executor.py
    app/core/bus_runtime.py
    tests/test_workflow_executor.py
    tests/test_workflow_runtime_integration.py

Known limitations:

- Workflow scheduling is currently an explicit boundary API.
- No automatic workflow execution/orchestration loop was introduced.
- Workflow remains a definition and derived-state model.
- WorkflowExecutor does not own execution, retry, event publication, or
  cancellation orchestration.

Next checkpoint:

- Audit the next Phase 40 workflow execution/orchestration boundary.

---
---

## Phase 40-I-C - Workflow Execution Orchestration

Status: COMPLETE

Implementation commit:

- `ed0e894` - `Implement Phase 40-I-C workflow execution orchestration`

Implemented:

- Extended `WorkflowExecutor` into the canonical workflow orchestration
  boundary.
- Tracked registered workflows for dependency-driven advancement.
- Added duplicate protection for canonical Tasks already present in the
  existing `TaskQueue`.
- Added `advance()` to re-evaluate tracked workflows and enqueue newly ready
  Tasks.
- Added `on_task_executed()` as the execution-to-workflow advancement hook.
- Integrated workflow advancement into `BusRuntime.execute_once()` after the
  existing `TASK_EXECUTED` event publication boundary.
- Reused the existing `BusRuntime.execution_loop` and `TaskQueue`.
- No second execution loop or second task queue was introduced.
- Existing TaskExecutor, Task lifecycle, retry, cancellation, progress, and
  workflow terminal-outcome semantics remain unchanged.
- Legacy dictionary-task execution remains unchanged.

Verification:

- Targeted Phase 40-I-C workflow orchestration tests: 8 passed in 0.77s.
- Full regression: 237 passed in 9.09s.
- `compileall`: PASS.
- `git diff --check`: PASS.
- BOM audit: PASS.
- Exact implementation scope committed as `ed0e894`.
- Unrelated working-tree changes remain unstaged.

Affected files:

    app/agents/orchestrator/workflow_executor.py
    app/core/bus_runtime.py
    tests/test_workflow_execution_orchestration.py

Architectural decisions:

- Workflow remains a definition and derived-state model.
- WorkflowExecutor owns scheduling/orchestration advancement.
- The existing TaskQueue remains the single canonical queue.
- The existing BusRuntime execution loop remains the single automatic
  execution loop.
- Workflow advancement is attached to the existing Task execution boundary.

Known limitations:

- Tracked workflows are currently retained for the lifetime of the executor.
- Workflow persistence is not part of this checkpoint.
- Workflow terminal publication remains governed by the existing H-C boundary.
- Cancellation/failure propagation remains a separate orchestration concern.

Next checkpoint:

- Audit the next Phase 40 workflow orchestration boundary.

---
