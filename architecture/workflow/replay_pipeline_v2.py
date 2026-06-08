from architecture.core.kafka_broker_v3 import KafkaBrokerV3
from architecture.core.replay_controller_v2 import ReplayControllerV2

broker = KafkaBrokerV3()

def handler(event):
    print("[REPLAY v2 PROCESS]", event)

# produce events
for i in range(10):
    broker.publish("DEVICE_DETECTED", {
        "type": "DEVICE_DETECTED",
        "data": {"id": f"pixel-{i%3}"}
    })

# replay only recent half
replay = ReplayControllerV2(broker)
replay.replay_topic("DEVICE_DETECTED", handler, from_offset=5)
