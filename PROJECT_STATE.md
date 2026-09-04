# PixelOrchestrator Ã¢â‚¬â€ Project State

> Authoritative continuation checkpoint for active development.
> The repository is the source of truth.

---

## CURRENT CHECKPOINT

### Phase

Phase 40-C-B ? Canonical Execution Path

### Status

COMPLETE

### Commit

1bbc156 ? Implement Phase 40-C-B canonical execution path

### Test Baseline

160 passed

Command:

    python -m pytest -q

Result:

    160 passed in 10.33s

### Targeted Regression

13 passed

Command:

    python -m pytest .\tests\test_execution_worker.py .\tests\test_bus_runtime_execution.py .\tests\test_bus_runtime_task_event.py .\tests\test_bus_runtime_auto_execution.py .\tests\test_lifecycle_consumer.py -q

Result:

    13 passed in 0.95s

### Compile Check

PASS

### Diff Check

PASS

### Architecture Result

Canonical Task execution is now forwarded through ExecutionWorker
and BusRuntime.

ActionResult is preserved as the execution result object while
TASK_EXECUTED event payloads are serialized to a JSON-safe dictionary
at the event boundary.

Legacy execution compatibility remains intact.

### Working Tree

Unrelated pre-existing working tree changes remain intentionally
unstaged and excluded from the Phase 40-C-B commit.

### Next Phase

Phase 40 ? Workflow / Task Execution Layer
Next checkpoint: determine the next execution/workflow boundary
after canonical Task migration.


Phase 40 ??? Workflow / Task Execution Layer
# Phase 37 Ã¢â‚¬â€ Device State / Lifecycle Hardening

## Objective

Formalize canonical device lifecycle transitions and integrate
state synchronization into the lifecycle runtime.

## Completed Changes

### Device State Machine

Added:

    app/core/device_state.py

`DeviceStateMachine` validates and applies canonical `DeviceState`
transitions.

Covered lifecycle states include:

- UNKNOWN
- DISCONNECTED
- ADB
- RECOVERY
- SIDELOAD
- FASTBOOT
- FASTBOOTD
- EDL

Invalid transitions are rejected with `ValueError`.

Failed transitions preserve the existing device state.

### Lifecycle Consumer Integration

Updated:

    app/agents/orchestrator/lifecycle_consumer.py

The lifecycle consumer now:

- accepts the canonical `DeviceRegistry`
- creates canonical `Device` objects
- derives `DeviceState` from lifecycle mode
- registers devices in the canonical registry
- applies `DeviceStateMachine` transitions
- handles disconnect state transitions
- preserves existing lifecycle task generation

### Bus Runtime Integration

Updated:

    app/core/bus_runtime.py

`BusRuntime` now owns a canonical `DeviceRegistry` and passes it
to `LifecycleConsumer`.

### Regression Coverage

Added:

    tests/test_device_state.py

Validated:

- UNKNOWN Ã¢â€ â€™ ADB
- DISCONNECTED Ã¢â€ â€™ ADB
- ADB Ã¢â€ â€™ FASTBOOT
- FASTBOOT Ã¢â€ â€™ FASTBOOTD
- RECOVERY Ã¢â€ â€™ SIDELOAD
- ADB Ã¢â€ â€™ DISCONNECTED
- invalid transition rejection
- failed-transition state preservation

## Verification

Targeted lifecycle/state tests:

    12 passed

Bus runtime integration tests:

    4 passed

Full regression:

    118 passed in 6.32s

Working tree:

    CLEAN

## Architecture Result

Lifecycle flow is now:

    Detector
        |
        v
    Lifecycle Event
        |
        v
    LifecycleConsumer
        |
        +--> DeviceRegistry
        |
        +--> DeviceStateMachine
        |
        v
    TaskQueue
        |
        v
    BusRuntime / TaskExecutor

The canonical `Device` contract remains:

    app/core/module_contract.py

No second Device model was introduced.

---

# Known Limitations

1. ADB and Fastboot remain the primary detection transports.
2. DeviceRegistry remains an in-memory canonical registry.
3. Registry persistence remains a separate concern.
4. Transport abstraction hardening remains future work.
5. Device capability modeling remains future work.
6. GUI device-management integration remains future work.
7. AI provider integration remains incomplete.

---

# NEXT PHASE

## Phase 38 - Unified Transport Layer Hardening

Status:

    COMPLETE

Objective:

Make ADB/Fastboot and future transports conform to one stable
transport abstraction.

Completed validation:

- Transport abstract contract verified.
- ADB transport verified.
- Fastboot transport verified.
- Transport factory verified.
- Transport resolver verified.
- Unsupported transport rejection verified.
- Invalid serial rejection verified.
- Unsupported device state rejection verified.
- Full test suite passed.

Test Baseline:

    118 passed in 7.63s

Validation:

    python -m pytest -q

Result:

    118 passed in 7.63s

Working Tree:

    clean before checkpoint update

---


---

# Phase 39 ??? Device Capability System

## Objective

Represent what each device/module can actually do.

## Completed Changes

### Capability Contract

Implemented canonical capability representation through:

    app/core/module_contract.py

Capabilities are represented with stable capability IDs and are
validated as part of module contracts.

### Capability Registry

Added:

    app/core/capability_registry.py

The registry provides:

- capability registration
- capability lookup
- presence checks
- enumeration
- unregister
- clear
- length tracking
- duplicate protection
- invalid capability rejection

### Module Capability Ownership

Updated:

    app/core/module_registry.py

Modules now expose capabilities through their contracts.

Capability ownership is tracked so that:

- multiple modules may share one capability
- removing one owner preserves a shared capability
- removing the final owner removes the capability
- absent-module unregister returns False
- failed registration rolls back newly registered capabilities
- failed registration removes partial ownership state

### Built-in Module Capabilities

Built-in modules expose their supported capabilities through the
canonical module contract.

### Capability / Action Integrity

Validated that actions requiring capabilities are correctly tied to
their declared capability requirements.

Unsupported actions return the structured UNKNOWN_ACTION result
instead of silently succeeding.

### Device Capability Enforcement

Validated required-capability enforcement at device/action level,
while preserving actions that are explicitly optional.

### Regression Coverage

Phase 39 checkpoint validation covered:

- capability registration and lookup
- capability presence and enumeration
- capability unregister and cleanup
- shared capability ownership
- final-owner cleanup
- exception-safe registration rollback
- action-to-capability integrity
- device capability requirement enforcement
- optional capability actions
- unknown action handling
- capability/action enabled state
- final Phase 39 integration

Final regression baseline:

    129 passed

Compile check:

    PASS

Diff check:

    PASS

Architecture/reference audit:

    PASS

## Key Decisions

- Capability IDs are stable identifiers.
- Action IDs remain module-local rather than globally unique.
- Shared capabilities use ownership tracking inside ModuleRegistry.
- Capability registration is exception-safe and rolls back partial state.
- Unsupported operations use structured failure results.
- Capability modeling is part of the canonical module/device contract.

## Closure

Phase 39 implementation and integration validation are complete.

Next phase:

    Phase 40 ??? Workflow / Task Execution Layer

Objective:

    Turn individual operations into reliable workflows.

---

# Phase 40-A â€” Task Contract

Status:

    COMPLETE

Implementation:

    app/core/task.py

Tests:

    tests/test_task.py

Task contract provides:

- globally unique UUID task IDs
- device_id
- module_id
- action_id
- action parameters
- TaskStatus lifecycle
- execution attempt tracking
- ActionResult integration
- creation/start/completion timestamps
- defensive parameter copying
- lifecycle transition validation
- cancellation support

Task lifecycle:

    PENDING
        |
        v
    RUNNING ---> COMPLETED
        |
        +-------> FAILED
        |
        +-------> CANCELLED

Key decisions:

- Task is an execution unit, not an Action.
- Action IDs remain module-local.
- Task identity therefore includes module_id + action_id.
- Capability validation remains outside the Task contract.
- Queueing, execution, retry policy, workflow/DAG handling,
  and event publishing remain outside the Task contract.
- Retry-specific state is deferred to Phase 40-F.

Verification:

    Targeted Task tests: 14 passed

    Full regression:
    143 passed in 10.27s

    Compile:
    PASS

    Diff check:
    PASS

Commit:

    0a3522b

Commit message:

    Implement Phase 40-A task contract

Next:

    Phase 40-B â€” Task Queue


---

# Phase 40-B-A â€” Task Queue Checkpoint

Status:

    COMPLETE

Commit:

    0e12c95

Verification:

    7 Task Queue tests passed
    9 execution/lifecycle compatibility tests passed
    150 full regression tests passed
    compileall PASS
    git diff --check PASS

Decision:

    TaskQueue now provides the complete Phase 40-B queue contract.
    Existing legacy queue consumers remain compatible.
    No artificial B-B implementation is required.
    Canonical Task execution migration is deferred to Phase 40-C.

Next:

    Phase 40-C â€” Task Execution Layer

---
# Phase 40-D â€” Workflow Definition Contract

Status: COMPLETE

Commit: `2e1a16f`

Current architecture:
`Canonical Task -> TaskQueue -> ExecutionWorker -> TaskExecutor -> ModuleRegistry / DeviceRegistry -> ActionResult`

Workflow layer:
`Workflow -> Tasks + dependency declarations`

A Workflow groups canonical Tasks and describes their dependency relationships. It does not execute tasks.

Implemented:
- Workflow ID
- canonical Task collection
- defensive task-list copy
- dependency mapping
- duplicate Task ID validation
- unknown dependency validation
- self-dependency validation
- Task/dependency type validation

Verification:
- Workflow: 9 passed
- Phase 40 targeted regression: 41 passed
- Full regression baseline: 169 passed
- compileall: PASS
- git diff --check: PASS

Decision:
- Task owns execution lifecycle.
- Workflow owns grouping and dependency structure only.
- Queue, executor, retry, cancellation, progress, and failure handling remain outside Workflow.

Next checkpoint:
Phase 40-E â€” DAG dependency validation/execution readiness.

Continuity rule:
Resume from this checkpoint and preserve unrelated working-tree changes as unstaged.

---

# Phase 40-E â€” DAG Dependency Validation / Execution Readiness

Status: COMPLETE

Commit:

    23c7749

Current architecture:

    Canonical Task -> TaskQueue -> ExecutionWorker -> TaskExecutor
    -> ModuleRegistry / DeviceRegistry -> ActionResult

Workflow layer:

    Workflow -> Tasks + dependency declarations
             -> DAG validation
             -> execution readiness

Implemented:

- Workflow dependency cycle detection via `validate_dag()`
- Dependency readiness via `ready_tasks()`
- Dependency-free PENDING Tasks are ready
- A dependent Task becomes ready only when all dependencies are COMPLETED
- PENDING, RUNNING, FAILED, or CANCELLED dependencies block readiness
- Ready Tasks preserve Workflow declaration order

Verification:

- Phase 40-E Workflow tests: 16 passed
- Full regression: 176 passed
- compileall: PASS
- git diff --check: PASS
- implementation commit scope: only `app/core/workflow.py` and `tests/test_workflow.py`

Decision:

- Workflow owns DAG validation and dependency readiness calculation.
- Task owns the individual execution lifecycle.
- TaskQueue / ExecutionWorker / TaskExecutor remain execution boundaries.
- Workflow does not execute Tasks.
- Retry, cancellation, progress events, and failure orchestration remain separate Phase 40 boundaries.

Next checkpoint:

Phase 40-F-B — Retry Execution Semantics.

Before implementation:

- Define how TaskExecutor applies RetryPolicy.
- Preserve correct Task lifecycle transitions and attempt counting.
- Add focused execution tests before production changes.
- Preserve the 184-test baseline.
- Do not stage unrelated working-tree changes.

Phase 40-F-A — Retry Policy Contract

Status: COMPLETE

Implementation commit:

    bf52f7f — Implement Phase 40-F-A retry policy contract

Current state:

- `app/core/retry_policy.py` defines the canonical RetryPolicy contract.
- `RetryPolicy.max_attempts` represents total execution attempts, including the initial attempt.
- Failed ActionResult values may be retried while attempts remain.
- Successful ActionResult values are never retried.
- `Task.attempts` remains the authoritative cumulative attempt counter.
- Task lifecycle behavior remains unchanged.
- TaskExecutor retry execution semantics remain deferred to Phase 40-F-B.
- No retry backoff, cancellation during retry, progress events, or workflow execution was introduced.

Verification:

    RetryPolicy targeted tests: 8 passed

    Full regression:
    184 passed in 6.66s

    Compile:
    PASS

    Diff check:
    PASS

    BOM audit:
    PASS

Continuity rule:

Resume from this checkpoint and preserve all unrelated working-tree changes as unstaged.

Continuity rule:

Resume from this checkpoint and preserve all unrelated working-tree changes as unstaged.

---

## Phase 40-F-B � Retry Execution Semantics

Status: COMPLETE

Implementation commit:

    2278a16 � Implement Phase 40-F-B retry execution semantics

Objective:

    Integrate the canonical RetryPolicy with TaskExecutor while preserving
    correct Task lifecycle transitions and cumulative attempt tracking.

Implementation:

- Added `Task.retry()` to return an intermediate failed execution from
  `RUNNING` to `PENDING`.
- `Task.retry()` preserves the authoritative cumulative `attempts` counter.
- `Task.retry()` preserves `started_at` and clears `completed_at`.
- Integrated `RetryPolicy` into the canonical `TaskExecutor`.
- `RetryPolicy.max_attempts` represents total execution attempts, including
  the initial attempt.
- Failed execution results are retried while attempts remain.
- Successful execution results complete the Task immediately.
- Only the final unsuccessful attempt transitions the Task to `FAILED`.
- Execution exceptions are converted to `EXECUTION_ERROR` ActionResults
  and participate in retry policy evaluation.
- Deterministic preflight failures (`MODULE_NOT_FOUND`,
  `ACTION_NOT_FOUND`, `DEVICE_NOT_FOUND`) remain terminal and are not
  retried.
- The legacy dictionary-task execution path remains unchanged.
- No `RETRYING` TaskStatus was introduced.
- No retry backoff or scheduling was introduced.
- Workflow execution, cancellation during retry, progress events, and
  broader failure orchestration remain outside this checkpoint.

Canonical execution architecture:

    Task
      -> TaskExecutor
      -> RetryPolicy
      -> ModuleRegistry / DeviceRegistry
      -> ActionResult
      -> Task lifecycle

Verification:

- Focused Task/RetryPolicy/TaskExecutor/ExecutionWorker/BusRuntime tests:
  41 passed in 0.90s
- Full regression:
  189 passed in 8.15s
- `compileall`: PASS
- `git diff --check`: PASS

Architectural decisions:

- `RetryPolicy` owns retry-decision semantics.
- `Task.attempts` remains the authoritative cumulative attempt counter.
- `Task` owns attempt lifecycle state through `start()`, `retry()`,
  `complete()`, and `fail()`.
- `TaskExecutor` owns application of the retry policy around actual
  canonical module execution.
- Intermediate failures are not terminal when retry attempts remain.
- Preflight resolution failures remain deterministic terminal failures.

Known limitations:

- No retry backoff or scheduling.
- No cancellation-aware retry behavior.
- No progress-event model.
- No workflow-level execution orchestration.

Next:

    Continue Phase 40 with the next remaining execution boundary
    after Retry Execution Semantics. Inspect the Phase 40 roadmap and
    existing cancellation/progress/failure boundaries before implementation.

Continuity rule:

    Preserve unrelated working-tree changes as unstaged and do not
    restart completed Phase 40 checkpoints without evidence.

---

## Phase 40-F-C — Cancellation Execution Semantics

Status: COMPLETE

Implementation commit:

    e66d62c — Implement Phase 40 cancellation execution semantics

Objective:

    Ensure cancelled canonical Tasks queued for execution are consumed
    safely by ExecutionWorker without being forwarded to the executor.

Implemented:

- ExecutionWorker now recognizes cancelled canonical `Task` instances.
- A cancelled canonical Task is consumed from the TaskQueue.
- Cancelled canonical Tasks are not forwarded to TaskExecutor.
- A cancelled-before-execution Task remains in `CANCELLED` state.
- A cancelled-before-execution Task retains `attempts == 0`.
- Legacy dictionary-task execution remains unchanged.
- Existing Task.cancel() lifecycle semantics remain unchanged.
- No forced interruption of a currently executing synchronous module
  was introduced.
- Retry semantics, RetryPolicy, backoff, and scheduling remain unchanged.

Canonical cancellation boundary:

    Task
      -> TaskQueue
      -> ExecutionWorker
           -> CANCELLED: consume and stop
           -> otherwise: Executor

Verification:

- ExecutionWorker cancellation tests: 6 passed
- Focused Phase 40 integration tests: 63 passed
- Full regression: 191 passed in 7.34s
- `compileall`: PASS
- `git diff --check`: PASS

Architectural decisions:

- ExecutionWorker owns the boundary that prevents queued cancelled
  canonical Tasks from entering execution.
- Task.cancel() remains the source of cancellation state.
- TaskExecutor is not responsible for silently accepting a cancelled
  queued Task.
- Legacy dictionary-task compatibility remains preserved.
- Running synchronous execution is not forcibly interrupted by this
  checkpoint.

Known limitations:

- No forced interruption of an already executing synchronous module.
- No cancellation-aware retry backoff or scheduling.
- No progress-event model.
- No workflow-level cancellation orchestration.

Next:

    Inspect the remaining Phase 40 progress-event and failure-handling
    boundaries before selecting the next implementation checkpoint.

Continuity rule:

    Preserve unrelated working-tree changes as unstaged and do not
    restart completed Phase 40 checkpoints without evidence.

---

## Phase 40-G-A — Progress Event Contract

Status: COMPLETE

Implementation commit:

    9fb360b — Implement Phase 40-G-A progress event contract

Objective:

    Establish the canonical TASK_PROGRESS event contract without making
    Task, TaskExecutor, Workflow, or RetryPolicy responsible for event
    publication.

Implemented:

- Added TASK_PROGRESS event validation to `app/core/events.py`.
- `task_id` is required and must be a non-empty string.
- `progress` is required and must be an integer from 0 through 100 inclusive.
- Boolean progress values are rejected.
- `message` is optional and, when present, must be a string.
- Existing event types retain their previous behavior.
- TASK_EXECUTED remains unchanged.
- TASK_PROGRESS does not modify Task lifecycle/status.
- Progress is defined per execution attempt, not as cumulative retry percentage.
- Task does not publish progress events.
- TaskExecutor does not automatically publish every progress event.
- Future execution/orchestration boundaries own progress publication.

Canonical progress event payload:

    {
        "task_id": "<global task id>",
        "progress": 0..100,
        "message": "<optional human-readable status>"
    }

Architectural decisions:

- `Event` validates the TASK_PROGRESS contract at construction time.
- Progress publication remains outside Task lifecycle ownership.
- RetryPolicy does not own progress semantics.
- Workflow does not own progress-event implementation.
- 100% progress does not replace or imply TASK_EXECUTED.
- No RETRYING status, backoff, scheduling, or workflow-level progress
  orchestration was introduced.
- Legacy event names in `core/event_types.py` remain untouched.

Verification:

- G-A targeted tests: 7 passed
- Canonical task event regression: 3 passed
- Full regression: 198 passed in 11.72s
- `compileall`: PASS
- `git diff --check`: PASS
- BOM audit after cleanup: PASS

Affected files:

    app/core/events.py
    tests/test_task_progress_event.py

Known limitations:

- No execution worker progress publication yet.
- No workflow-level progress aggregation.
- No progress persistence contract beyond the existing Event system.
- No UI progress consumer.
- No retry/backoff progress model.

Next:

    Phase 40-G-B — Progress Event Publication Boundary.

    Inspect the canonical TaskExecutor/ExecutionWorker/BusRuntime boundary
    and define the smallest safe mechanism for publishing TASK_PROGRESS
    events while preserving TASK_EXECUTED, retry, cancellation, and legacy
    dictionary-task behavior.

Continuity rule:

    Preserve unrelated working-tree changes as unstaged and do not restart
    completed Phase 40 checkpoints without evidence.

## Phase 40-G-B - Progress Event Publication Boundary

Status: COMPLETE

Implementation commit:

- `7ebf3c0` - `Implement Phase 40-G-B progress event publication boundary`

Implemented:

- Added an optional progress callback to the canonical TaskExecutor.
- TaskExecutor reports progress at execution-attempt boundaries.
- Successful attempts report progress 0 then 100.
- Retryable failed attempts report progress 0 then 100 before retry.
- Terminal failed attempts report progress 0 then 100 before final failure.
- BusRuntime owns TASK_PROGRESS event construction and publication.
- TASK_EXECUTED behavior remains unchanged.
- Retry semantics remain unchanged.
- Cancellation semantics remain unchanged.
- Legacy dictionary-task behavior remains unchanged.
- Progress is per execution attempt, not cumulative across retries.
- Task, Workflow, and RetryPolicy do not own EventBus publication.

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

Next:

    Phase 40-G-C - Workflow Progress Aggregation.

---

## Phase 40-G-C - Workflow Progress

Status: COMPLETE

Implementation commit:

- `4b7eae7` - `Implement Phase 40-G-C workflow progress`

Implemented:

- Added derived `Workflow.progress()` returning an integer from 0 through 100.
- Workflow progress is calculated from completed tasks.
- Completed tasks are the numerator.
- Total workflow tasks are the denominator.
- PENDING, RUNNING, FAILED, and CANCELLED tasks are not counted as completed.
- Empty workflows return 0.
- Workflow does not own EventBus publication.
- Workflow progress does not alter Task lifecycle semantics.
- RetryPolicy remains unchanged.
- TASK_PROGRESS event publication remains an orchestration-boundary concern.

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

Next:

    Phase 40-G-D-A - Workflow Progress Publication Boundary.

---

## Phase 40-G-D-A - Workflow Progress Publication Boundary

Status: COMPLETE

Implementation commit:

- `481e70b` - `Implement Phase 40-G-D workflow progress publication`

Implemented:

- Added a BusRuntime workflow progress publication boundary.
- BusRuntime publishes `WORKFLOW_PROGRESS`.
- Workflow progress is derived from `Workflow.progress()`.
- Published payload contains `workflow_id`, `progress`, and `message`.
- Workflow remains free of EventBus ownership.
- Task-level `TASK_PROGRESS` remains separate from workflow-level progress.
- TaskExecutor remains responsible only for task-level progress callbacks.
- Existing TASK_EXECUTED behavior remains unchanged.
- Existing retry and cancellation semantics remain unchanged.
- No unrelated working-tree changes were included in the implementation commit.

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

Next:

    Inspect the remaining Phase 40 failure-handling boundaries before
    selecting the next implementation checkpoint.

Continuity rule:

    Preserve unrelated working-tree changes as unstaged and do not restart
    completed Phase 40 checkpoints without evidence.
## Phase 40-H-A - Workflow Outcome Contract

Status: COMPLETE

Commit:
    2c070ea Implement Phase 40-H-A workflow outcome contract

Implementation:

- Added derived Workflow.status() outcome contract.
- Workflow outcome is derived from current TaskStatus values and is not stored as mutable workflow state.
- FAILED has precedence over CANCELLED.
- CANCELLED is reported when cancellation exists and no task has failed.
- COMPLETED is reported when all workflow tasks are completed.
- RUNNING is reported when at least one task is running and no terminal failure/cancellation exists.
- PENDING is reported otherwise, including workflows containing blocked pending dependencies.
- No BLOCKED workflow status was introduced.
- Workflow does not own EventBus or event publication.
- Existing Task retry, failure, cancellation, DAG readiness, and progress semantics remain unchanged.

TDD verification:

- RED: 7 workflow status tests failed as expected because Workflow.status() did not exist.
- GREEN: 7 workflow status tests passed after the minimal implementation.
- Focused Phase 40 regression: 59 passed in 3.32s.
- Full regression: 215 passed in 10.58s.
- Implementation diff audit: PASS.
- git diff --check: PASS.
- BOM audit: PASS.

Affected files:

    app/core/workflow.py
    tests/test_workflow_status.py

Known limitations:

- Workflow status is currently a derived query only.
- No automatic workflow execution/orchestration loop was introduced.
- No workflow terminal event publication was introduced.
- Empty-workflow outcome semantics remain intentionally unspecified pending an explicit contract decision.

Next:

    Define the next workflow failure-handling/publication boundary only after
    preserving the separation between Workflow state derivation and runtime
    event orchestration.

Continuity rule:

    Preserve unrelated working-tree changes as unstaged and do not restart
    completed Phase 40 checkpoints without evidence.

## Phase 40-H-B - Workflow Failure Handling / Terminal State

Status: COMPLETE

Commit:
    21b993b H-B Add workflow terminal state handling

Implemented:

- Added Workflow.is_terminal() as a pure derived terminal-state query.
- completed, failed, and cancelled workflows are terminal.
- pending and running workflows are non-terminal.
- Workflow failure handling remains derived from TaskStatus.
- FAILED retains precedence over CANCELLED.
- Failed dependencies continue to prevent dependent tasks from becoming ready.
- No redundant workflow-level failure result was introduced.
- Workflow remains free of EventBus ownership, execution orchestration,
  retry orchestration, and task mutation side effects.

Verification:

- Workflow failure-handling tests: 4 passed.
- Workflow terminal-state tests: 6 passed.
- Focused Phase 40 regression: 99 passed in 5.80s.
- Full regression: 225 passed in 19.58s.
- compileall: PASS.
- git diff --check: PASS.
- BOM audit: PASS.

Affected files:

    app/core/workflow.py
    tests/test_workflow_failure_handling.py
    tests/test_workflow_terminal.py

Known limitations:

- Workflow terminal state is currently a derived query only.
- No workflow terminal event publication was introduced in H-B.

Next:

    Phase 40-H-C - Workflow Terminal Outcome Publication Boundary.

---

## Phase 40-H-C - Workflow Terminal Outcome Publication Boundary

Status: COMPLETE

Commit:
    db0bba5 Implement workflow terminal outcome publication

Implemented:

- Added BusRuntime.publish_workflow_terminal_outcome(workflow).
- Terminal workflow outcomes are published at the BusRuntime orchestration
  and event boundary.
- COMPLETED publishes WORKFLOW_COMPLETED.
- FAILED publishes WORKFLOW_FAILED.
- CANCELLED publishes WORKFLOW_CANCELLED.
- Pending and running workflows publish no terminal outcome.
- Terminal event payload contains workflow_id and derived status.
- Workflow remains free of EventBus ownership and publication logic.
- Existing WORKFLOW_PROGRESS semantics remain separate.
- Task lifecycle, retry, cancellation, and TASK_EXECUTED semantics remain unchanged.

TDD verification:

- Initial test setup RED exposed an incorrect StreamBus.subscribe() usage.
- After aligning the test with the canonical three-argument StreamBus
  subscription contract, valid RED was established:
  BusRuntime.publish_workflow_terminal_outcome did not exist.
- GREEN: 4 passed in 0.55s.
- Focused Phase 40 regression: 99 passed in 6.79s.
- Full regression: 229 passed in 11.32s.
- compileall: PASS.
- git diff --check: PASS.
- BOM audit: PASS.
- Exact H-C staged scope: PASS.
- Commit scope: only app/core/bus_runtime.py and
  tests/test_workflow_terminal_publication.py.

Affected files:

    app/core/bus_runtime.py
    tests/test_workflow_terminal_publication.py

Known limitations:

- Terminal outcome publication is currently an explicit BusRuntime boundary API.
- No automatic workflow execution/orchestration loop was introduced.
- No UI consumer for workflow terminal events was introduced.
- No workflow terminal state is persisted separately from task-derived state.

Next:

    Continue Phase 40 workflow orchestration only after auditing the next
    execution/integration boundary while preserving Workflow as a derived
    state model and BusRuntime as the event publication boundary.

Continuity rule:

    Preserve unrelated working-tree changes as unstaged and do not restart
    completed Phase 40 checkpoints without evidence.
---

## Phase 40-I-A / I-B - Workflow Scheduling Boundary and BusRuntime Integration

Status: COMPLETE

Implementation commits:

    d11241a Implement Phase 40-I-A workflow scheduling boundary
    12d730d Integrate workflow scheduling with BusRuntime

Implemented:

- Added WorkflowExecutor as the canonical workflow scheduling boundary.
- WorkflowExecutor evaluates Workflow.ready_tasks() and enqueues ready canonical
  Tasks into the existing TaskQueue.
- WorkflowExecutor does not execute tasks, own retry policy, publish events, or
  own workflow lifecycle state.
- BusRuntime now owns WorkflowExecutor and connects it to the existing TaskQueue.
- Added BusRuntime.enqueue_workflow_ready_tasks(workflow) as the explicit
  runtime scheduling integration boundary.
- Existing TaskExecutor, ExecutionWorker, Task lifecycle, retry, cancellation,
  progress, and workflow terminal publication semantics remain unchanged.

Verification:

- Targeted workflow scheduling/runtime integration tests: 5 passed in 0.44s.
- Full regression: 234 passed in 8.84s.
- compileall: PASS.
- git diff --check: PASS.
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

Next:

    Audit the next Phase 40 workflow execution/orchestration boundary before
    introducing automatic workflow execution.

Continuity rule:

    Preserve unrelated working-tree changes as unstaged and do not restart
    completed Phase 40 checkpoints without evidence.