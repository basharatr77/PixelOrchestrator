from app.core.events import Event


def test_task_progress_event_has_canonical_type():
    event = Event(
        type="TASK_PROGRESS",
        payload={
            "task_id": "task-1",
            "progress": 50,
            "message": "Working",
        },
    )

    assert event.type == "TASK_PROGRESS"


def test_task_progress_payload_contains_required_fields():
    event = Event(
        type="TASK_PROGRESS",
        payload={
            "task_id": "task-1",
            "progress": 50,
            "message": "Working",
        },
    )

    assert event.payload["task_id"] == "task-1"
    assert event.payload["progress"] == 50
    assert event.payload["message"] == "Working"


def test_task_progress_allows_zero_and_hundred():
    for progress in (0, 100):
        event = Event(
            type="TASK_PROGRESS",
            payload={
                "task_id": "task-1",
                "progress": progress,
            },
        )

        assert event.payload["progress"] == progress


def test_task_progress_rejects_invalid_progress():
    for progress in (-1, 101, 50.5, "50"):
        try:
            Event(
                type="TASK_PROGRESS",
                payload={
                    "task_id": "task-1",
                    "progress": progress,
                },
            )
        except (TypeError, ValueError):
            continue

        raise AssertionError(
            f"Invalid progress value was accepted: {progress!r}"
        )


def test_task_progress_requires_task_id():
    try:
        Event(
            type="TASK_PROGRESS",
            payload={
                "progress": 50,
            },
        )
    except (TypeError, ValueError):
        return

    raise AssertionError("TASK_PROGRESS accepted a payload without task_id")


def test_task_progress_message_is_optional():
    event = Event(
        type="TASK_PROGRESS",
        payload={
            "task_id": "task-1",
            "progress": 25,
        },
    )

    assert event.payload["task_id"] == "task-1"
    assert event.payload["progress"] == 25


def test_task_progress_message_must_be_string_when_present():
    try:
        Event(
            type="TASK_PROGRESS",
            payload={
                "task_id": "task-1",
                "progress": 25,
                "message": 123,
            },
        )
    except (TypeError, ValueError):
        return

    raise AssertionError("TASK_PROGRESS accepted a non-string message")
