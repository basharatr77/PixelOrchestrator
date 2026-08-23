import asyncio

from app.core.bus_runtime import BusRuntime


def test_bus_runtime_publishes_task_executed_event():
    async def run():
        runtime = BusRuntime()

        result = runtime.execute_once({
            "action": "safe_probe",
            "serial": "PIXEL_8",
        })

        assert result == {
            "success": True,
            "action": "safe_probe",
            "serial": "PIXEL_8",
        }

        assert runtime.bus.queue.qsize() == 1

        offset, event = await runtime.bus.queue.get()

        assert event.type == "TASK_EXECUTED"
        assert event.payload == {
            "success": True,
            "action": "safe_probe",
            "serial": "PIXEL_8",
        }

    asyncio.run(run())
