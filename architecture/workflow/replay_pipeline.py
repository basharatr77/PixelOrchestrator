from architecture.core.kafka_broker_v3 import KafkaBrokerV3
from architecture.core.replay_controller import ReplayController

broker = KafkaBrokerV3()

def handler(event):
    print("[REPLAY PROCESS]", event)

# produce events
for i in range(5):
    broker.publish("DEVICE_DETECTED", {
        "type": "DEVICE_DETECTED",
        "data": {"id": f"pixel-{i%2}"}
    })

# replay system
replay = ReplayController(broker)
replay.replay_topic("DEVICE_DETECTED", handler)
