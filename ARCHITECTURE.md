# PixelOrchestrator Architecture

## Purpose
PixelOrchestrator is a modular Android device orchestration platform.

## Source of Truth
- PROJECT_STATE.md: current checkpoint and closure gates.
- PHASE_PLAN.md: phase scope and roadmap.
- PROJECT_INSTRUCTIONS.md: development and architecture rules.
- README.md: project overview.

## High-Level Architecture
Desktop GUI -> Application Adapters -> Orchestration Runtime -> Device Integration -> Connected Devices.

## Runtime Components
- Canonical device contract: app/core/module_contract.py
- Device registry: app/core/device_registry.py
- Event bus: app/core/event_bus.py
- Event store: app/core/event_store.py
- Event broker: app/core/event_broker.py
- Bus runtime: app/core/bus_runtime.py
- GUI adapters: app/gui/

## Conceptual Event and Task Flow
Device Detection -> Canonical Device -> Registry -> Lifecycle Events -> Task Queue -> Worker / Executor -> Transport Operation.

## Transport and Remote Access
Documented transport families include ADB and Fastboot. The project also contains a remote-agent/WebSocket architecture. Verify specific device-mode and operation support against implementation and tests.

## Security and Observability
Important concerns include authorization, device ownership, cancellation, safe cleanup, secret-safe logging, connection lifecycle, persistence, recovery, health checks, and error handling. Documentation alone does not prove every control is complete.

## Health Center Direction
Documented areas: System Health, Device Health, Connection Health, Diagnostics, and Alerts & Issues. Verify implementation status before claiming completion.

## Phase Boundary
Phase 49 - Production Hardening / Security / Observability: IN PROGRESS - CLOSURE PENDING.
Phase 50 - Release / Packaging / Deployment: PLANNED - NOT STARTED.
Do not start Phase 50 until Phase 49 closure requirements are satisfied.

## Verification Rules
Read the project-state documents, inspect implementation and tests, preserve unrelated changes, and review the exact staged diff before committing.

## Related Documentation
- README.md
- PROJECT_STATE.md
- PHASE_PLAN.md
- PROJECT_INSTRUCTIONS.md
