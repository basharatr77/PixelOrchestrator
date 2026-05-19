from dataclasses import dataclass, field
import time
import uuid
from typing import Any, Dict, Optional

@dataclass
class Message:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    requires_ack: bool = True
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "payload": self.payload,
            "requires_ack": self.requires_ack,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        return cls(
            id=data["id"],
            type=data["type"],
            payload=data.get("payload", {}),
            requires_ack=data.get("requires_ack", True),
            timestamp=data.get("timestamp", time.time())
        )