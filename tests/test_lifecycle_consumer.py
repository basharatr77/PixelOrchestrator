import sqlite3

from app.agents.orchestrator.lifecycle_consumer import LifecycleConsumer
from app.agents.orchestrator.task_queue import TaskQueue
from app.core.event_bus import StreamBus
from app.core.events import Event


def test_connected_event_updates_registry_and_creates_task(tmp_path):
    db_path = tmp_path / "devices.db"
    queue = TaskQueue()

    def update_registry(device, status, offset):
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS device_registry "
            "(device_name TEXT PRIMARY KEY, status TEXT)"
        )
        conn.execute(
            "INSERT INTO device_registry(device_name, status) "
            "VALUES (?, ?) "
            "ON CONFLICT(device_name) DO UPDATE SET status=excluded.status",
            (device, status),
        )
        conn.commit()
        conn.close()
        return True

    consumer = LifecycleConsumer(
        task_queue=queue,
        registry_updater=update_registry,
    )

    event = Event(
        "DEVICE_CONNECTED",
        {
            "serial": "PIXEL_8",
            "mode": "ADB",
            "brand": "",
            "model": "",
            "android_version": "",
        },
    )

    consumer.handle(event, 1, "orchestrator")

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT device_name, status FROM device_registry"
    ).fetchone()
    conn.close()

    assert row == ("PIXEL_8", "ADB")
    assert queue.tasks == [
        {
            "action": "safe_probe",
            "serial": "PIXEL_8",
        }
    ]


def test_mode_changed_updates_registry_and_creates_task(tmp_path):
    db_path = tmp_path / "devices.db"
    queue = TaskQueue()

    def update_registry(device, status, offset):
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS device_registry "
            "(device_name TEXT PRIMARY KEY, status TEXT)"
        )
        conn.execute(
            "INSERT INTO device_registry(device_name, status) "
            "VALUES (?, ?) "
            "ON CONFLICT(device_name) DO UPDATE SET status=excluded.status",
            (device, status),
        )
        conn.commit()
        conn.close()
        return True

    consumer = LifecycleConsumer(
        task_queue=queue,
        registry_updater=update_registry,
    )

    event = Event(
        "DEVICE_MODE_CHANGED",
        {
            "serial": "PIXEL_8",
            "previous_mode": "ADB",
            "mode": "FASTBOOT",
        },
    )

    consumer.handle(event, 2, "orchestrator")

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT device_name, status FROM device_registry"
    ).fetchone()
    conn.close()

    assert row == ("PIXEL_8", "FASTBOOT")
    assert queue.tasks == [
        {
            "action": "diagnostic_scan",
            "serial": "PIXEL_8",
        }
    ]


def test_disconnected_event_updates_registry_without_task(tmp_path):
    db_path = tmp_path / "devices.db"
    queue = TaskQueue()

    def update_registry(device, status, offset):
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS device_registry "
            "(device_name TEXT PRIMARY KEY, status TEXT)"
        )
        conn.execute(
            "INSERT INTO device_registry(device_name, status) "
            "VALUES (?, ?) "
            "ON CONFLICT(device_name) DO UPDATE SET status=excluded.status",
            (device, status),
        )
        conn.commit()
        conn.close()
        return True

    consumer = LifecycleConsumer(
        task_queue=queue,
        registry_updater=update_registry,
    )

    event = Event(
        "DEVICE_DISCONNECTED",
        {
            "serial": "PIXEL_8",
        },
    )

    consumer.handle(event, 3, "orchestrator")

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT device_name, status FROM device_registry"
    ).fetchone()
    conn.close()

    assert row == ("PIXEL_8", "disconnected")
    assert queue.tasks == []


def test_consumer_registers_with_stream_bus():
    bus = StreamBus()
    queue = TaskQueue()

    consumer = LifecycleConsumer(
        task_queue=queue,
        registry_updater=lambda device, status, offset: True,
    )

    consumer.subscribe(bus)

    assert len(
        bus.handlers[("orchestrator", "DEVICE_CONNECTED")]
    ) == 1

    assert len(
        bus.handlers[("orchestrator", "DEVICE_MODE_CHANGED")]
    ) == 1

    assert len(
        bus.handlers[("orchestrator", "DEVICE_DISCONNECTED")]
    ) == 1
