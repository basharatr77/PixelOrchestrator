# PixelOrchestrator

**Android Device Orchestration Platform**

PixelOrchestrator is an event-driven Android device orchestration platform designed to manage device detection, canonical device identity, lifecycle state, transport operations, task execution, diagnostics, and future distributed device-farm workflows.

The project is being developed as a modular foundation for reliable Android device automation and smart device-service infrastructure.

---

## Architecture

![PixelOrchestrator Orchestrator Workflow](docs/architecture/orchestrator-workflow.png)

PixelOrchestrator is designed around a canonical device model and an event-driven orchestration pipeline:

```text
Android Device
      |
      v
Device Detection
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
Lifecycle Consumer
      |
      +------------------+
      |                  |
      v                  v
Device State        Task Generation
Machine                  |
      |                  v
      +------------> Task Queue
                           |
                           v
                    Workflow Execution
                           |
                           v
                    Unified Transport
                           |
                           v
                    Device Operations
```

The architecture is intentionally modular, testable, transport-agnostic, and designed for future distributed execution.

---

## Current Status

### Phase 37 — Device State / Lifecycle Hardening

**Status: COMPLETE**

Latest Phase 37 commits:

```text
31e8613  Integrate device state machine into lifecycle runtime
3e61c50  Document Phase 37 completion and advance to Phase 38
```

Current regression baseline:

```text
118 passed
```

The Phase 37 implementation introduced deterministic device lifecycle state transitions and integrated the canonical device registry with lifecycle processing.

---

## Implemented Core Features

### Device Detection

Current device detection is centered around Android transport discovery, including:

* ADB
* Fastboot

Additional vendor-specific transports are planned for future phases.

---

### Canonical Device Model

PixelOrchestrator uses a canonical `Device` contract instead of maintaining multiple competing device models.

The canonical contract includes concepts such as:

* Device ID
* Serial
* Device state
* Transport
* Module type
* Device properties

Canonical device contracts are defined in:

```text
app/core/module_contract.py
```

---

### Device Registry

The canonical in-memory device registry provides:

* Device registration
* Device lookup
* Device update
* Device removal
* Duplicate protection
* Registry snapshots
* Registry isolation

Implementation:

```text
app/core/device_registry.py
```

The registry is intentionally separated from vendor-specific modules and database persistence.

---

### Device Lifecycle

Lifecycle events are handled through the orchestrator lifecycle consumer.

Supported lifecycle events include:

```text
DEVICE_CONNECTED
DEVICE_MODE_CHANGED
DEVICE_DISCONNECTED
```

Implementation:

```text
app/agents/orchestrator/lifecycle_consumer.py
```

---

### Device State Machine

Phase 37 introduced a deterministic device state machine.

Supported lifecycle states include:

```text
UNKNOWN
DISCONNECTED
ADB
RECOVERY
SIDELOAD
FASTBOOT
FASTBOOTD
EDL
```

State transitions are validated before being applied.

Invalid transitions are rejected instead of silently changing device state.

Implementation:

```text
app/core/device_state.py
```

Example lifecycle flow:

```text
UNKNOWN
   |
   v
 ADB <----> RECOVERY
  |            |
  |            v
  |         SIDELOAD
  |
  v
FASTBOOT <--> FASTBOOTD

EDL
 |
 v
DISCONNECTED
```

The state machine is designed to prevent inconsistent lifecycle state from propagating through the orchestration system.

---

## Event-Driven Runtime

PixelOrchestrator uses an event-driven architecture to separate detection, lifecycle handling, orchestration, and execution.

The runtime contains components for:

* Event publishing
* Event consumption
* Event persistence
* Lifecycle processing
* Task generation
* Event replay
* Deduplication

Core runtime components include:

```text
app/core/event_bus.py
app/core/event_store.py
app/core/event_broker.py
app/core/bus_runtime.py
```

---

## Task and Workflow Architecture

Device lifecycle events can generate orchestration tasks.

The broader execution architecture is designed to support:

* Task queues
* Task executors
* Workflow definitions
* DAG-based dependencies
* Retry policies
* Cancellation
* Progress reporting
* Failure handling

These capabilities are being developed incrementally through the project phases.

---

## Transport Layer

The transport architecture is designed to provide a common abstraction for device communication.

Current transports include:

```text
ADB
Fastboot
```

The transport architecture includes components such as:

```text
Transport
Transport Resolver
Transport Factory
ADB Transport
Fastboot Transport
```

### Phase 38

The next development phase is:

**Unified Transport Layer Hardening**

Planned focus:

* Stable transport interface
* ADB transport hardening
* Fastboot transport hardening
* Transport resolver
* Transport factory
* Error normalization
* Command execution
* Timeout handling
* Device availability checks

---

## Device Capabilities

A dedicated capability system is planned to represent what each device or module can safely perform.

Potential capabilities include:

```text
ADB shell
Reboot
Bootloader
Fastboot operations
Recovery operations
Diagnostics
```

Capability validation will be used to prevent unsupported operations from reaching device execution.

---

## Diagnostics and AI

PixelOrchestrator is designed to support AI-assisted diagnostics.

The planned intelligence layer includes:

```text
Logs
  |
  v
Diagnostics
  |
  v
Error Classification
  |
  v
Root Cause Analysis
  |
  v
AI Decision Engine
  |
  v
Safe Remediation
```

AI is intended to assist with diagnosis and decision support.

**AI must not bypass deterministic safety checks or capability validation.**

Provider integration and advanced AI decision functionality remain future work.

---

## Future Self-Healing Architecture

A future self-healing pipeline is planned:

```text
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
Policy / Approval
  |
  v
Execution
  |
  v
Verification
  |
  v
Recovery / Escalation
```

This functionality is planned for later development phases and is not represented as fully implemented today.

---

## Plugin Architecture

PixelOrchestrator is designed to support vendor-specific modules without destabilizing the core platform.

Potential modules include:

* Pixel
* Qualcomm
* MediaTek
* Samsung / Odin
* Unisoc
* Generic Android

Future plugins will use explicit contracts and capability declarations.

---

## Distributed Device Farm

A future version of PixelOrchestrator is intended to support multiple devices concurrently.

Planned capabilities include:

```text
Device Pools
Device Reservations
Per-Device Queues
Parallel Execution
Device Health
Worker Pools
Distributed Workers
Remote Devices
WebSocket Transport
Heartbeats
Autoscaling
```

This will allow PixelOrchestrator to evolve from a local device-management application into a distributed Android device orchestration platform.

---

## GUI

The project includes a GUI layer intended to provide a user-friendly interface over the orchestration backend.

Planned/available GUI concepts include:

* Device dashboard
* Connected devices
* Device state
* Device details
* Tasks
* Workflows
* Logs
* Diagnostics
* AI assistant
* Repair operations
* Windows Device Manager shortcut
* Drivers shortcut

The GUI is intended to consume backend contracts rather than implementing device lifecycle or transport logic independently.

---

## Supported Device Direction

The architecture is intended to support multiple Android device families.

### Pixel

Primary project focus.

Potential areas include:

* ADB
* Fastboot
* Recovery
* FastbootD
* Modem recovery
* Device diagnostics

### Samsung

Samsung device support is being considered through the transport/plugin architecture, including future Odin-oriented workflows.

### Qualcomm

Future vendor modules may provide Qualcomm-specific diagnostic and recovery functionality.

### MediaTek

Future MediaTek modules may provide device detection and service workflows where supported.

### Unisoc

Future Unisoc support can be integrated through the plugin architecture.

---

## Development Principles

PixelOrchestrator follows several architectural principles:

### Modular

Components should have clear responsibilities and contracts.

### Event-Driven

Lifecycle and orchestration behavior should communicate through explicit events.

### Transport-Agnostic

Core orchestration should not depend directly on one vendor transport.

### Testable

Core behavior should be independently testable.

### Extensible

New device vendors and transports should be addable without rewriting the core.

### Recoverable

Events, state, and workflows should support recovery and replay.

### Automation-Ready

The architecture should support reliable automation from individual devices to distributed device farms.

---

## Project Structure

A simplified view of the current architecture:

```text
PixelOrchestrator/
|
+-- app/
|   |
|   +-- agents/
|   |   +-- device_agent/
|   |   +-- orchestrator/
|   |
|   +-- core/
|       +-- module_contract.py
|       +-- device_registry.py
|       +-- device_state.py
|       +-- bus_runtime.py
|       +-- event_bus.py
|       +-- event_store.py
|       +-- event_broker.py
|       +-- transport/
|       +-- ...
|
+-- tests/
|
+-- docs/
|   +-- architecture/
|       +-- orchestrator-workflow.png
|
+-- PHASE_PLAN.md
+-- PROJECT_STATE.md
+-- PROJECT_INSTRUCTIONS.md
+-- README.md
```

The repository structure will continue evolving as the architecture advances.

---

## Verification

The project uses automated tests to protect architectural changes.

Current Phase 37 regression baseline:

```text
118 passed in 6.32s
```

Run the complete test suite:

```powershell
python -m pytest -q
```

Compile-check application and tests:

```powershell
python -m compileall -q .\app .\tests
```

Check Git whitespace errors:

```powershell
git diff --check
```

---

## Development Roadmap

| Phase | Area                                            | Status   |
| ----- | ----------------------------------------------- | -------- |
| 1–34  | Architecture & Foundation                       | COMPLETE |
| 35    | Canonical Device Identity & Transport State     | COMPLETE |
| 36    | Device Detection & Registry                     | COMPLETE |
| 37    | Device State / Lifecycle Hardening              | COMPLETE |
| 38    | Unified Transport Layer Hardening               | NEXT     |
| 39    | Device Capability System                        | PLANNED  |
| 40    | Workflow / Task Execution Layer                 | PLANNED  |
| 41    | Persistent Event & Replay Infrastructure        | PLANNED  |
| 42    | Device Farm / Multi-Device Orchestration        | PLANNED  |
| 43    | Worker Pool & Distributed Execution             | PLANNED  |
| 44    | WebSocket / Remote Device Transport             | PLANNED  |
| 45    | Plugin Architecture                             | PLANNED  |
| 46    | AI Diagnosis & Decision Engine                  | PLANNED  |
| 47    | Self-Healing / Auto-Repair Workflows            | PLANNED  |
| 48    | GUI Device Operations & UX                      | PLANNED  |
| 49    | Production Hardening / Security / Observability | PLANNED  |
| 50    | Release / Packaging / Deployment                | PLANNED  |

The authoritative development checkpoint is maintained in:

```text
PROJECT_STATE.md
```

The broader architectural roadmap is maintained in:

```text
PHASE_PLAN.md
```

---

## Current Development Focus

The immediate development target is:

### Phase 38 — Unified Transport Layer Hardening

The goal is to establish a stable transport abstraction that allows ADB, Fastboot, and future transports to operate through consistent interfaces.

The implementation will be developed incrementally with tests and regression verification at each checkpoint.

---

## Safety and Architecture Rules

PixelOrchestrator follows these core rules:

1. Do not introduce duplicate `Device` models.
2. Use the canonical `Device` contract.
3. Keep device lifecycle state deterministic.
4. Validate state transitions.
5. Do not bypass capability checks.
6. Keep vendor-specific logic isolated.
7. Keep GUI logic separate from device-control logic.
8. Do not claim planned features as implemented.
9. Add tests alongside architectural changes.
10. Keep the repository as the source of truth.

---

## License

License information will be added as the project approaches its release and packaging phase.

---

## Project Status

**Active Development**

PixelOrchestrator is currently under active architectural development.

The project is being built incrementally from a stable core toward:

**Android Device Orchestration → Workflow Automation → Device Farm → Distributed Execution → Intelligent Diagnostics → Self-Healing Infrastructure**

---

**PixelOrchestrator**

*Modular · Event-Driven · Transport-Agnostic · Testable · Extensible · Recoverable · Automation-Ready*
