from app.core.task import Task
from app.core.workflow import Workflow


def make_task(action_id):
    return Task(
        device_id="device-1",
        module_id="adb",
        action_id=action_id,
    )


def test_workflow_defaults_are_valid():
    task = make_task("probe")

    workflow = Workflow(
        tasks=[task],
    )

    assert workflow.id
    assert workflow.tasks == [task]
    assert workflow.dependencies == {}


def test_workflow_accepts_multiple_tasks():
    task1 = make_task("probe")
    task2 = make_task("shell")

    workflow = Workflow(
        tasks=[task1, task2],
    )

    assert workflow.tasks == [task1, task2]


def test_workflow_defensive_copies_task_list():
    tasks = [make_task("probe")]
    workflow = Workflow(tasks=tasks)

    tasks.append(make_task("shell"))

    assert workflow.tasks == [workflow.tasks[0]]


def test_workflow_dependency_links_tasks_by_id():
    task1 = make_task("probe")
    task2 = make_task("shell")

    workflow = Workflow(
        tasks=[task1, task2],
        dependencies={task2.id: {task1.id}},
    )

    assert workflow.dependencies == {
        task2.id: {task1.id},
    }


def test_workflow_rejects_duplicate_task_ids():
    task = make_task("probe")

    try:
        Workflow(tasks=[task, task])
    except ValueError:
        pass
    else:
        raise AssertionError("Workflow must reject duplicate task IDs")


def test_workflow_rejects_unknown_dependency_task():
    task1 = make_task("probe")
    task2 = make_task("shell")

    try:
        Workflow(
            tasks=[task1, task2],
            dependencies={task2.id: {"missing-task"}},
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Workflow must reject dependencies referencing unknown tasks"
        )


def test_workflow_rejects_self_dependency():
    task = make_task("probe")

    try:
        Workflow(
            tasks=[task],
            dependencies={task.id: {task.id}},
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Workflow must reject self-dependencies")


def test_workflow_rejects_non_task_items():
    try:
        Workflow(tasks=[{"id": "not-a-task"}])
    except TypeError:
        pass
    else:
        raise AssertionError("Workflow must contain Task objects")


def test_workflow_rejects_non_dict_dependencies():
    task = make_task("probe")

    try:
        Workflow(
            tasks=[task],
            dependencies=[],
        )
    except TypeError:
        pass
    else:
        raise AssertionError("Workflow dependencies must be a dictionary")

from app.core.module_contract import ActionResult
from app.core.task import Task, TaskStatus
from app.core.workflow import Workflow


def make_task(action_id):
    return Task(
        device_id="device-1",
        module_id="adb",
        action_id=action_id,
    )


def test_workflow_accepts_linear_dag():
    task1 = make_task("probe")
    task2 = make_task("shell")
    task3 = make_task("reboot")

    workflow = Workflow(
        tasks=[task1, task2, task3],
        dependencies={
            task2.id: {task1.id},
            task3.id: {task2.id},
        },
    )

    assert workflow.validate_dag() is True


def test_workflow_rejects_dependency_cycle():
    task1 = make_task("probe")
    task2 = make_task("shell")
    task3 = make_task("reboot")

    try:
        Workflow(
            tasks=[task1, task2, task3],
            dependencies={
                task2.id: {task1.id},
                task3.id: {task2.id},
                task1.id: {task3.id},
            },
        ).validate_dag()
    except ValueError:
        pass
    else:
        raise AssertionError("Workflow must reject dependency cycles")


def test_workflow_dependency_free_task_is_ready():
    task = make_task("probe")
    workflow = Workflow(tasks=[task])

    assert workflow.ready_tasks() == [task]


def test_workflow_dependent_task_is_not_ready_until_dependency_completes():
    task1 = make_task("probe")
    task2 = make_task("shell")

    workflow = Workflow(
        tasks=[task1, task2],
        dependencies={task2.id: {task1.id}},
    )

    assert workflow.ready_tasks() == [task1]

    task1.start()
    task1.complete(ActionResult(success=True, message="done"))

    assert workflow.ready_tasks() == [task2]


def test_workflow_dependent_task_not_ready_when_dependency_failed():
    task1 = make_task("probe")
    task2 = make_task("shell")

    workflow = Workflow(
        tasks=[task1, task2],
        dependencies={task2.id: {task1.id}},
    )

    task1.start()
    task1.fail(ActionResult(success=False, message="failed"))

    assert workflow.ready_tasks() == []


def test_workflow_dependent_task_not_ready_when_dependency_cancelled():
    task1 = make_task("probe")
    task2 = make_task("shell")

    workflow = Workflow(
        tasks=[task1, task2],
        dependencies={task2.id: {task1.id}},
    )

    task1.cancel()

    assert workflow.ready_tasks() == []


def test_workflow_ready_tasks_preserve_workflow_order():
    task1 = make_task("probe")
    task2 = make_task("shell")
    task3 = make_task("reboot")

    workflow = Workflow(
        tasks=[task1, task2, task3],
    )

    assert workflow.ready_tasks() == [task1, task2, task3]
