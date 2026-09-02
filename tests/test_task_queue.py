from app.agents.orchestrator.task_queue import TaskQueue
from app.core.task import Task


def test_queue_starts_empty():
    queue = TaskQueue()

    assert queue.tasks == []
    assert queue.size() == 0
    assert queue.is_empty()
    assert queue.peek_task() is None
    assert queue.pop_task() is None


def test_queue_is_fifo():
    queue = TaskQueue()
    first = {"action": "safe_probe", "serial": "A"}
    second = {"action": "diagnostic_scan", "serial": "B"}

    queue.add_task(first)
    queue.add_task(second)

    assert queue.pop_task() == first
    assert queue.pop_task() == second
    assert queue.is_empty()


def test_peek_does_not_remove_task():
    queue = TaskQueue()
    task = {"action": "safe_probe", "serial": "A"}

    queue.add_task(task)

    assert queue.peek_task() == task
    assert queue.size() == 1
    assert queue.peek_task() == task
    assert queue.size() == 1


def test_queue_size_and_empty_state():
    queue = TaskQueue()

    assert queue.is_empty()

    queue.add_task({"action": "one"})
    assert queue.size() == 1
    assert not queue.is_empty()

    queue.add_task({"action": "two"})
    assert queue.size() == 2


def test_clear_removes_all_tasks():
    queue = TaskQueue()

    queue.add_task({"action": "one"})
    queue.add_task({"action": "two"})

    queue.clear()

    assert queue.tasks == []
    assert queue.size() == 0
    assert queue.is_empty()
    assert queue.peek_task() is None


def test_queue_accepts_canonical_task():
    queue = TaskQueue()
    task = Task(
        device_id="device-1",
        module_id="adb",
        action_id="safe_probe",
    )

    queue.add_task(task)

    assert queue.peek_task() is task
    assert queue.pop_task() is task
    assert queue.is_empty()


def test_tasks_property_is_compatible_snapshot():
    queue = TaskQueue()
    task = {"action": "safe_probe"}

    queue.add_task(task)

    snapshot = queue.tasks
    snapshot.clear()

    assert queue.size() == 1
    assert queue.peek_task() == task
