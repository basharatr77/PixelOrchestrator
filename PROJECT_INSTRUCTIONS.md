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
