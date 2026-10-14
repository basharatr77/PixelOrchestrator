import threading
from concurrent.futures import ThreadPoolExecutor

from app.core.module_contract import (
    Action,
    ActionResult,
    Capability,
    ModuleContract,
    ModuleManifest,
    ModuleType,
)
from app.gui.module_adapter import GUIModuleAdapter


class _ConcurrentApprovalModule(ModuleContract):
    manifest = ModuleManifest(
        id="phase49_concurrency_test",
        name="Phase 49 Concurrency Test",
        version="1.0.0",
        module_type=ModuleType.COMMON,
        description="Isolated dangerous-action approval concurrency test.",
        capabilities=(
            Capability(
                id="concurrency_capability",
                name="Concurrency Capability",
            ),
        ),
        actions=(
            Action(
                id="dangerous_action",
                name="Dangerous Action",
                capability_id="concurrency_capability",
                requires_device=False,
                dangerous=True,
            ),
        ),
    )

    def __init__(self):
        self.execution_lock = threading.Lock()
        self.execution_count = 0

    def detect(self):
        return []

    def execute(self, action_id, device=None, **kwargs):
        with self.execution_lock:
            self.execution_count += 1

        return ActionResult(
            success=True,
            message="Action executed.",
        )



def test_concurrent_dangerous_action_approval_is_consumed_safely():
    adapter = GUIModuleAdapter()
    module = _ConcurrentApprovalModule()
    adapter.registry.register(module)

    approval_key = (module.manifest.id, "dangerous_action")
    approval_token = adapter.approve_dangerous_action(*approval_key)

    start_barrier = threading.Barrier(2)

    def execute_action():
        start_barrier.wait(timeout=5)
        return adapter.execute_action(
            module.manifest.id,
            "dangerous_action",
            approval_token=approval_token,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(execute_action)
            for _ in range(2)
        ]
        outcomes = [future.result(timeout=10) for future in futures]

    assert all(isinstance(result, ActionResult) for result in outcomes)
    assert sum(result.success for result in outcomes) == 1
    assert module.execution_count == 1
    assert adapter._dangerous_action_approvals == {}

