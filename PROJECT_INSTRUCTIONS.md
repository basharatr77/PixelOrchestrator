# PixelOrchestrator — Project Instructions

## 1. Primary Rule

The repository is the source of truth.

Chat history is supplementary and must never be treated as more authoritative than the current repository state.

Always begin continuation work by checking:

    PROJECT_STATE.md
    PHASE_PLAN.md
    PROJECT_INSTRUCTIONS.md

---

## 2. New Chat / Resume Procedure

When starting a new ChatGPT conversation about PixelOrchestrator:

1. Read `PROJECT_STATE.md`.
2. Read the relevant section of `PHASE_PLAN.md`.
3. Check Git status.
4. Check the latest commit.
5. Check the current test baseline.
6. Identify the exact next step recorded in `PROJECT_STATE.md`.
7. Continue from that checkpoint.
8. Do not restart completed phases without evidence that they need correction.

---

## 3. Architecture Safety

Do not introduce duplicate models when a canonical contract already exists.

Before creating a new class/model/interface:

1. Search the repository for existing implementations.
2. Identify the canonical implementation.
3. Reuse the canonical contract.
4. Migrate consumers systematically.
5. Add/update tests.
6. Remove obsolete implementations only after references are eliminated.

For Device identity, the canonical contract is currently:

    app/core/module_contract.py

Do not recreate:

    app/agents/device_agent/device_model.py

Do not reintroduce legacy:

    device.mode

Use canonical DeviceState/module/transport fields instead.

---

## 4. Change Discipline

Prefer small, coherent architectural phases.

Do not mix unrelated refactors into a phase.

For every meaningful change:

1. Inspect.
2. Plan.
3. Modify.
4. Compile.
5. Test.
6. Audit references.
7. Review diff.
8. Commit.
9. Update project state.

---

## 5. Testing Rule

Before declaring a phase complete:

    python -m compileall -q .\app .\tests

Then:

    python -m pytest -q

Then:

    git diff --check

If tests fail, do not mark the phase complete.

Record failures in `PROJECT_STATE.md` when they are relevant to the checkpoint.

---

## 6. Legacy Reference Rule

When replacing an architectural component:

- Search imports.
- Search direct attribute references.
- Search constructors.
- Search tests.
- Search documentation where relevant.
- Remove obsolete files only after migration.
- Re-run the search after migration.

A successful test suite alone is not enough to prove that a legacy abstraction has disappeared.

---

## 7. Checkpoint Rule

At the end of every completed phase, update `PROJECT_STATE.md`.

The update should include:

- Phase
- Status
- Commit
- Test result
- Compile result
- Important architectural changes
- Files/components affected
- Known limitations
- Next exact step

Then create the Git commit.

The commit hash must be recorded in `PROJECT_STATE.md`.

---

## 8. Chat Continuity Rule

If a new chat begins, do not ask the user to repeat the entire project history if the repository state files contain the required information.

First use the project state files and Git state to reconstruct the current checkpoint.

The preferred opening procedure is:

    Read PROJECT_STATE.md
    Read PHASE_PLAN.md
    git status
    git log -1 --oneline

Then continue.

---

## 9. User Workflow

The user commonly works from Windows PowerShell at:

    C:\PixelOrchestrator-dev

Commands should therefore normally be provided in PowerShell-compatible form.

When giving a sequence of commands, keep the sequence explicit and checkpoint-oriented.

Do not ask the user to make destructive changes without first establishing the current state.

---

## 10. Definition of Done

A phase is complete only when:

- Implementation is complete
- Tests pass
- Compile check passes
- Diff check passes
- Architecture references are clean
- Project state is updated
- Git commit exists
- Next phase is clearly identified

---

## 11. Current Checkpoint

At the time this file was created:

Phase 35 is complete.

Commit:

    3d30994 Canonicalize device identity and transport state

Tests:

    102 passed

Next:

    Phase 36 — Device Detection & Registry

---

## 12. Important Principle

Never optimize for "code changed".

Optimize for:

    correct architecture
    + tested behavior
    + clean migration
    + reproducible checkpoint
    + easy future continuation

---

## 13. Persistent Project State System

The project uses three persistent continuity files:

    PROJECT_STATE.md
    PHASE_PLAN.md
    PROJECT_INSTRUCTIONS.md

### PROJECT_STATE.md

This is the exact current development checkpoint.

It must contain:

- current phase
- phase status
- latest commit
- verification results
- architecture changes
- known limitations
- exact next phase
- exact next action

### PHASE_PLAN.md

This is the master roadmap.

It records:

- completed phases
- current phase
- upcoming phases
- phase objectives
- architectural boundaries
- completion criteria

### PROJECT_INSTRUCTIONS.md

This file defines the rules for maintaining the project and continuing development safely.

---

## 14. Mandatory Checkpoint Update

Whenever a phase reaches COMPLETE status:

1. Verify implementation.
2. Run compile check.
3. Run full test suite.
4. Run diff check.
5. Run architecture/reference audit.
6. Update `PROJECT_STATE.md`.
7. Update `PHASE_PLAN.md` if phase status changed.
8. Review the complete diff.
9. Commit the phase.
10. Record the new commit hash in `PROJECT_STATE.md`.
11. Verify Git status.

Do not declare the phase complete before all steps succeed.

---

## 15. New Chat Continuation Contract

At the beginning of a new project conversation, reconstruct the project state from the repository.

Required order:

    Get-Content .\PROJECT_STATE.md
    Get-Content .\PHASE_PLAN.md
    Get-Content .\PROJECT_INSTRUCTIONS.md
    git status --short
    git log -1 --oneline

The current repository state has priority over old chat history.

Do not ask the user to repeat project history when these files provide the required context.

---

## 16. Checkpoint Is Not Automatic

Markdown files do not update themselves automatically.

The development workflow must explicitly update them at every completed phase.

When making a meaningful architectural change, prefer:

    inspect
    plan
    modify
    compile
    test
    audit
    review
    update state
    commit

The state files are therefore treated as part of the project's version-controlled architecture documentation.

---

## 17. No Silent Phase Advancement

Do not silently move from one phase to another.

Before starting a new phase:

- identify the phase in `PROJECT_STATE.md`
- confirm its objective in `PHASE_PLAN.md`
- define the exact first inspection step
- keep unrelated work outside the phase

---

## 18. Recovery Principle

If chat history is lost:

    PROJECT_STATE.md
        +
    PHASE_PLAN.md
        +
    PROJECT_INSTRUCTIONS.md
        +
    Git history

must be sufficient to reconstruct the development checkpoint.

The project should never depend exclusively on conversational memory.

---

## 19. Current Canonical Device Architecture

The canonical Device contract is:

    app/core/module_contract.py

Current canonical fields include:

    device_id
    module_type
    state
    serial
    transport
    model
    properties

Do not recreate:

    app/agents/device_agent/device_model.py

Do not reintroduce:

    device.mode

All new device-related architecture must build on the canonical contract unless a documented architectural decision explicitly changes it.

---

## 20. Current Resume Point

Current completed phase:

    Phase 35 — Canonical Device Identity & Transport State

Current commit:

    3d30994

Next phase:

    Phase 36 — Device Detection & Registry

The first action of Phase 36 is inspection and architecture mapping, not immediate modification.

---

# Phase 40 Continuity Update

Phase 40-A Task Contract is complete at commit 1a2b713.

Phase 40-B Task Queue is complete at commit 0e12c95.

The Phase 40-B queue contract is considered complete without an additional B-B code change. The queue supports FIFO behavior, inspection, sizing, clearing, empty-state handling, canonical Task objects, and compatibility with existing legacy consumers.

Next implementation checkpoint:

    Phase 40-C — Task Execution Layer

When continuing Phase 40, inspect the canonical Task contract and existing legacy TaskExecutor/ExecutionWorker boundaries before modifying execution behavior. Preserve the existing 150-test regression baseline and do not stage unrelated working-tree changes.

Repository continuity remains based on:

    PROJECT_STATE.md
    PHASE_PLAN.md
    PROJECT_INSTRUCTIONS.md

---

---

# Phase 40-C-B ? Canonical Execution Path Checkpoint

Status:

    COMPLETE

Commit:

    1bbc156

Current execution architecture:

    Canonical Task -> TaskQueue -> ExecutionWorker -> TaskExecutor
    -> ModuleRegistry / DeviceRegistry -> ActionResult
    -> BusRuntime TASK_EXECUTED event boundary

Key decisions:

- TaskExecutor now supports the canonical Task contract.
- ExecutionWorker forwards canonical Task objects without owning execution policy.
- BusRuntime can enqueue and execute canonical Tasks.
- ActionResult remains the execution result object.
- TASK_EXECUTED event payloads are converted to JSON-safe dictionaries
  before publication.
- Legacy task execution compatibility remains intact.
- Existing unrelated working-tree changes must remain unstaged.

Verification:

    Full regression: 160 passed in 10.33s
    Targeted regression: 13 passed in 0.95s
    Compile: PASS
    Diff check: PASS

Next:

    Continue Phase 40 workflow execution design.
    Inspect the remaining workflow, DAG dependency, retry,
    cancellation, progress-event, and failure-handling boundaries
    before implementing the next checkpoint.

## Phase 40-D — Workflow Definition Contract

Status: COMPLETE

Commit: `2e1a16f`

The canonical Workflow contract was introduced in `app/core/workflow.py` with tests in `tests/test_workflow.py`.

Architecture:
`Workflow -> Tasks + dependency declarations`

Workflow groups canonical `Task` objects and describes dependency relationships. It does not execute tasks and does not own queueing, retry, cancellation, progress, or failure handling.

Verification:
- 9 Workflow tests passed
- 41 Phase 40 targeted tests passed
- 169 full regression tests passed
- compileall PASS
- git diff --check PASS
- staged implementation scope contained only the Workflow contract and its tests

Decision:
- Task remains the execution unit.
- Workflow owns grouping and dependency structure.
- DAG cycle/readiness semantics are deferred to the next Phase 40 boundary.

Next:
- Phase 40-E — DAG dependency validation/execution readiness.

## Phase 40-E — DAG Dependency Validation / Execution Readiness

Status: COMPLETE

Commit: `23c7749`

The Workflow contract now validates dependency graphs as DAGs and determines execution-ready canonical Tasks.

Implemented:
- `validate_dag()` cycle detection
- `ready_tasks()` dependency readiness
- dependency-free pending Tasks are ready
- dependent Tasks become ready only when all dependencies are COMPLETED
- FAILED, CANCELLED, RUNNING, or PENDING dependencies block readiness
- ready Tasks preserve Workflow order

Verification:
- Phase 40-E Workflow tests: 16 passed
- Full regression: 176 passed
- compileall PASS
- git diff --check PASS
- implementation commit contained only the canonical Workflow and Workflow tests

Decision:
- Workflow owns DAG validation and readiness calculation.
- Task owns execution lifecycle.
- TaskQueue / ExecutionWorker / TaskExecutor remain execution boundaries.
- Workflow execution is not introduced yet.
- Retry, cancellation, progress, and failure orchestration remain separate boundaries.

Next:
- Phase 40-F-B — Retry Execution Semantics.
- Define and test TaskExecutor retry behavior while preserving canonical Task lifecycle correctness.
- Preserve the 184-test baseline and do not stage unrelated working-tree changes.

## Phase 40-F-A — Retry Policy Contract

Status: COMPLETE

Implementation commit:
- `bf52f7f` — `Implement Phase 40-F-A retry policy contract`

Verification:
- RetryPolicy tests: 8 passed
- Full regression: 184 passed
- Compile: PASS
- Diff check: PASS
- BOM audit: PASS

Decisions:
- `RetryPolicy.max_attempts` means total attempts, including the initial attempt.
- Successful results are never retried.
- Failed results may retry while attempts remain.
- `Task.attempts` remains the authoritative cumulative attempt counter.
- Task lifecycle and TaskExecutor retry execution were not changed in 40-F-A.
- No retry backoff, cancellation, progress, or workflow execution was introduced.

---

## Phase 40-F-B � Retry Execution Semantics

Status: COMPLETE

Commit:

    2278a16

Phase 40-F-B integrates the canonical RetryPolicy with TaskExecutor.

The canonical Task lifecycle now supports intermediate retry transitions
through `Task.retry()`, returning a failed execution from RUNNING to PENDING
while preserving cumulative attempt tracking. TaskExecutor retries failed
module executions while RetryPolicy permits another attempt, completes
successful executions, and terminally fails only the final unsuccessful
attempt.

Execution exceptions are converted into `EXECUTION_ERROR` ActionResults
and participate in retry evaluation. Deterministic module/action/device
preflight failures remain terminal and are not retried.

Verification:

- Focused regression: 41 passed
- Full regression: 189 passed in 8.15s
- compileall: PASS
- git diff --check: PASS

The legacy dictionary-task execution path remains unchanged. No RETRYING
TaskStatus, retry backoff, or scheduling was introduced.

Next:

    Inspect the remaining Phase 40 cancellation/progress/failure boundaries
    before implementing the next checkpoint.

Repository continuity remains based on:

    PROJECT_STATE.md
    PHASE_PLAN.md
    PROJECT_INSTRUCTIONS.md

---

## Phase 40-F-C — Cancellation Execution Semantics

Status: COMPLETE

Commit:

    e66d62c

Phase 40-F-C establishes the canonical cancellation execution boundary.

ExecutionWorker consumes cancelled canonical Tasks from TaskQueue without
forwarding them to TaskExecutor. Cancelled-before-execution Tasks remain
CANCELLED with attempts == 0.

Verification:

- ExecutionWorker cancellation tests: 6 passed
- Focused Phase 40 regression: 63 passed
- Full regression: 191 passed in 7.34s
- compileall: PASS
- git diff --check: PASS

Decisions:

- Task.cancel() remains the canonical cancellation state transition.
- ExecutionWorker prevents queued cancelled canonical Tasks from entering
  execution.
- Legacy dictionary-task execution remains unchanged.
- Already-running synchronous module execution is not forcibly interrupted.
- Retry semantics remain separate from cancellation semantics.
- No progress-event or workflow-level cancellation model was introduced.

Next:

    Inspect the remaining Phase 40 progress-event and failure-handling
    boundaries before implementing the next checkpoint.

Repository continuity remains based on:

    PROJECT_STATE.md
    PHASE_PLAN.md
    PROJECT_INSTRUCTIONS.md

---

## Phase 40-G-A — Progress Event Contract

Status: COMPLETE

Commit:

    9fb360b

Phase 40-G-A establishes the canonical TASK_PROGRESS event contract.

The Event model now validates TASK_PROGRESS payloads with a required
non-empty task_id, an integer progress value from 0 through 100, and an
optional string message. Existing event types remain unchanged.

TASK_PROGRESS does not alter Task lifecycle/status. Progress is defined
per execution attempt rather than as cumulative retry percentage.
Task, TaskExecutor, Workflow, and RetryPolicy do not own progress
publication.

Verification:

- G-A targeted tests: 7 passed
- Canonical task event regression: 3 passed
- Full regression: 198 passed in 11.72s
- compileall: PASS
- git diff --check: PASS
- BOM audit: PASS

Architectural decisions:

- Event validates TASK_PROGRESS at construction time.
- TASK_EXECUTED remains unchanged.
- 100% progress does not replace or imply TASK_EXECUTED.
- Progress publication remains an execution/orchestration concern.
- Legacy event names remain untouched.
- No RETRYING status, retry backoff, scheduling, or workflow-level
  progress orchestration was introduced.

Next:

    Phase 40-G-B — Progress Event Publication Boundary.

    Inspect the canonical TaskExecutor/ExecutionWorker/BusRuntime
    boundary and define the smallest safe mechanism for publishing
    TASK_PROGRESS while preserving retry, cancellation, TASK_EXECUTED,
    and legacy dictionary-task behavior.

Repository continuity remains based on:

    PROJECT_STATE.md
    PHASE_PLAN.md
    PROJECT_INSTRUCTIONS.md

---

## Phase 40-H-B - Workflow Failure Handling / Terminal State

Status: COMPLETE

Commit:

    21b993b

Phase 40-H-B establishes the workflow terminal-state query boundary.

Workflow now exposes is_terminal() as a pure derived query based on
Workflow.status(). completed, failed, and cancelled are terminal;
pending and running are non-terminal.

FAILED retains precedence over CANCELLED. Failed dependencies remain
unavailable to dependent tasks. Workflow does not own EventBus,
execution orchestration, retry orchestration, or terminal event
publication.

Verification:

- Workflow failure-handling tests: 4 passed
- Workflow terminal tests: 6 passed
- Focused Phase 40 regression: 99 passed in 5.80s
- Full regression: 225 passed in 19.58s
- compileall: PASS
- git diff --check: PASS
- BOM audit: PASS

Affected files:

    app/core/workflow.py
    tests/test_workflow_failure_handling.py
    tests/test_workflow_terminal.py

Next:

    Phase 40-H-C - Workflow Terminal Outcome Publication Boundary.

---

## Phase 40-H-C - Workflow Terminal Outcome Publication Boundary

Status: COMPLETE

Commit:

    db0bba5

Phase 40-H-C establishes the workflow terminal outcome publication
boundary in BusRuntime.

BusRuntime now exposes publish_workflow_terminal_outcome(workflow).

Terminal workflow outcomes publish dedicated events:

    WORKFLOW_COMPLETED
    WORKFLOW_FAILED
    WORKFLOW_CANCELLED

The event payload contains:

    workflow_id
    status

Pending and running workflows do not publish terminal outcome events.

Workflow remains a pure derived state model and does not own EventBus
publication. WORKFLOW_PROGRESS remains separate from terminal outcome
events. Task lifecycle, retry, cancellation, and TASK_EXECUTED semantics
remain unchanged.

The StreamBus publish_now() path queues the event; dispatch remains an
explicit bus operation and is handled by the consuming orchestration or
test boundary.

Verification:

- Valid RED: missing BusRuntime.publish_workflow_terminal_outcome
- GREEN: 4 passed in 0.55s
- Focused Phase 40 regression: 99 passed in 6.79s
- Full regression: 229 passed in 11.32s
- compileall: PASS
- git diff --check: PASS
- BOM audit: PASS
- Exact staged scope: PASS

Affected files:

    app/core/bus_runtime.py
    tests/test_workflow_terminal_publication.py

Known limitations:

- Terminal outcome publication is currently an explicit BusRuntime
  boundary API.
- No automatic workflow execution/orchestration loop was introduced.
- No separate persisted workflow terminal state was introduced.
- No UI consumer for workflow terminal events was introduced.

Next:

    Audit the next Phase 40 workflow execution/integration boundary
    before introducing automatic orchestration.

Repository continuity remains based on:

    PROJECT_STATE.md
    PHASE_PLAN.md
    PROJECT_INSTRUCTIONS.md

Continuity rule:

    Preserve unrelated working-tree changes as unstaged and do not
    restart completed Phase 40 checkpoints without evidence.

---