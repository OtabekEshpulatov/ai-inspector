from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

@dataclass
class Employee:
    employee_id: str
    name: str
    department: str
    role: str
    is_resigning: bool = False
    is_insider: bool = False

@dataclass
class Event:
    event_id: str
    sender: str
    receiver: str
    timestamp: datetime
    channel: str
    metadata: Dict[str, Any]
    
    def to_dict(self):
        return {
            "event_id": self.event_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "timestamp": self.timestamp.isoformat(),
            "channel": self.channel,
            "metadata": self.metadata
        }
