# PixelOrchestrator — Phase Plan

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
| 1–34 | Earlier architecture and foundation work | COMPLETE |
| 35 | Canonical Device Identity & Transport State | COMPLETE |
| 36 | Device Detection & Registry | NEXT |
| 37 | Device State / Lifecycle Hardening | PLANNED |
| 38 | Unified Transport Layer Hardening | PLANNED |
| 39 | Device Capability System | PLANNED |
| 40 | Workflow / Task Execution Layer | PLANNED |
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

# PHASE 35 — Canonical Device Identity & Transport State

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

# PHASE 36 — Device Detection & Registry

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

# PHASE 37 — Device State / Lifecycle Hardening

Objective:

Formalize device lifecycle transitions.

Scope:

- DISCONNECTED
- ADB
- RECOVERY
- SIDELOAD
- FASTBOOT
- FASTBOOTD
- EDL
- UNKNOWN

Focus:

- Valid transitions
- Invalid transition protection
- Mode changes
- Connect/disconnect events
- State synchronization
- Lifecycle event correctness

---

# PHASE 38 — Unified Transport Layer Hardening

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

# PHASE 39 — Device Capability System

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

# PHASE 40 — Workflow / Task Execution Layer

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

# PHASE 41 — Persistent Event & Replay Infrastructure

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

# PHASE 42 — Device Farm / Multi-Device Orchestration

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

# PHASE 43 — Worker Pool & Distributed Execution

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

# PHASE 44 — WebSocket / Remote Device Transport

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

# PHASE 45 — Plugin Architecture

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

# PHASE 46 — AI Diagnosis & Decision Engine

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

# PHASE 47 — Self-Healing / Auto-Repair Workflows

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

# PHASE 48 — GUI Device Operations & UX

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

# PHASE 49 — Production Hardening

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

# PHASE 50 — Release / Packaging / Deployment

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
