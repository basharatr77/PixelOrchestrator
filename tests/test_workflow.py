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
