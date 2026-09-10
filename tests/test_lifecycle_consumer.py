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

def test_canonical_device_transport_tracks_mode_transition():
    from app.core.device_registry import DeviceRegistry

    registry = DeviceRegistry()
    queue = TaskQueue()

    consumer = LifecycleConsumer(
        task_queue=queue,
        registry_updater=lambda device, status, offset: True,
        device_registry=registry,
    )

    serial = "PIXEL_42C_TRANSPORT"

    consumer.handle(
        Event(
            "DEVICE_CONNECTED",
            {
                "serial": serial,
                "mode": "ADB",
                "brand": "",
                "model": "",
                "android_version": "",
            },
        ),
        1,
        "orchestrator",
    )

    device = registry.get(f"device:{serial}")

    assert device is not None
    assert device.device_id == f"device:{serial}"
    assert device.state.value == "adb"
    assert device.transport == "adb"
    assert len(registry) == 1

    consumer.handle(
        Event(
            "DEVICE_MODE_CHANGED",
            {
                "serial": serial,
                "previous_mode": "ADB",
                "mode": "FASTBOOT",
            },
        ),
        2,
        "orchestrator",
    )

    device = registry.get(f"device:{serial}")

    assert device is not None
    assert device.device_id == f"device:{serial}"
    assert device.state.value == "fastboot"
    assert device.transport == "fastboot"
    assert len(registry) == 1

    consumer.handle(
        Event(
            "DEVICE_MODE_CHANGED",
            {
                "serial": serial,
                "previous_mode": "FASTBOOT",
                "mode": "ADB",
            },
        ),
        3,
        "orchestrator",
    )

    device = registry.get(f"device:{serial}")

    assert device is not None
    assert device.device_id == f"device:{serial}"
    assert device.state.value == "adb"
    assert device.transport == "adb"
    assert len(registry) == 1


def test_ownership_survives_disconnect_and_reconnect():
    from app.core.agent_device_ownership import AgentDeviceOwnership
    from app.core.device_registry import DeviceRegistry

    queue = TaskQueue()
    device_registry = DeviceRegistry()
    ownership = AgentDeviceOwnership()

    serial = "PIXEL_45I"
    device_id = f"device:{serial}"
    agent_id = "agent-001"

    ownership.assign(agent_id, device_id)

    consumer = LifecycleConsumer(
        task_queue=queue,
        registry_updater=lambda device, status, offset: True,
        device_registry=device_registry,
    )

    consumer.handle(
        Event(
            "DEVICE_CONNECTED",
            {
                "serial": serial,
                "mode": "ADB",
                "brand": "",
                "model": "",
                "android_version": "",
            },
        ),
        1,
        "orchestrator",
    )

    assert ownership.owner_of(device_id) == agent_id

    consumer.handle(
        Event(
            "DEVICE_DISCONNECTED",
            {
                "serial": serial,
            },
        ),
        2,
        "orchestrator",
    )

    device = device_registry.get(device_id)

    assert device is not None
    assert device.state.value == "disconnected"
    assert ownership.owner_of(device_id) == agent_id

    consumer.handle(
        Event(
            "DEVICE_CONNECTED",
            {
                "serial": serial,
                "mode": "ADB",
                "brand": "",
                "model": "",
                "android_version": "",
            },
        ),
        3,
        "orchestrator",
    )

    device = device_registry.get(device_id)

    assert device is not None
    assert device.state.value == "adb"
    assert ownership.owner_of(device_id) == agent_id
