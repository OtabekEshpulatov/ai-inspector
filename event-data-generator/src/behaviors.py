import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
from .models import Employee, Event

fake = Faker()

CHANNELS = ["email", "slack", "telegram", "file_share", "usb"]
BASE_PROBABILITIES = {
    "email": 0.40,
    "slack": 0.50,
    "file_share": 0.08,
    "telegram": 0.01,
    "usb": 0.01
}

def weighted_choice(choices_dict):
    choices = list(choices_dict.keys())
    weights = list(choices_dict.values())
    return random.choices(choices, weights=weights, k=1)[0]

def _generate_metadata(channel: str):
    if channel in ["file_share", "usb"]:
        return {
            "size": f"{random.randint(1, 500)}MB",
            "file_type": random.choice([".pdf", ".zip", ".csv", ".docx", ".xlsx", ".bin"]),
            "sensitivity_level": random.choice(["Low", "Medium", "High", "Critical"])
        }
    return {
        "size": f"{random.randint(1, 50)}KB",
        "file_type": "text",
        "sensitivity_level": "Low"
    }

def generate_events_for_day(date: datetime.date, employees: list[Employee], cross_dept_prob: float = 0.3, fixed_num_events: int = None) -> list[Event]:
    events = []
    if len(employees) < 2:
        return events
        
    # Base configuration
    start_time = datetime.combine(date, datetime.min.time()) + timedelta(hours=9)
    
    if fixed_num_events is not None:
        num_events = fixed_num_events
    elif date.weekday() >= 5: # Weekend, huge drop in activity
        num_events = random.randint(10, 50)
    else:
        num_events = random.randint(300, 1000)
        
    for _ in range(num_events):
        sender = random.choice(employees)
        
        # Natural cluster constraint: more likely to talk to own department
        if random.random() > cross_dept_prob:
            dept_emps = [e for e in employees if e.department == sender.department and e != sender]
            receiver = random.choice(dept_emps) if dept_emps else random.choice([e for e in employees if e != sender])
        else:
            potential_receivers = [e for e in employees if e != sender]
            receiver = random.choice(potential_receivers) if potential_receivers else None

        if not receiver:
            continue

        # Time clustering
        event_time = start_time + timedelta(minutes=random.randint(0, 9*60))
        
        # Abnormal behaviors overrides
        channel = weighted_choice(BASE_PROBABILITIES)
        
        # 1. Insider Secret Comm: Try to use telegram or usb outside hours
        if sender.is_insider and receiver.is_insider and random.random() < 0.3:
            channel = random.choice(["telegram", "usb"])
            event_time = event_time + timedelta(hours=random.randint(8, 12)) # late night communication
            
        # 2. Resignation Spike: Spikes file_share or usb activity massively
        if sender.is_resigning and random.random() < 0.15: # Random chance of data exfiltration behavior
            channel = random.choice(["file_share", "usb"])
            
        events.append(
            Event(
                event_id=f"msg_{uuid.uuid4()}",
                sender=sender.employee_id,
                receiver=receiver.employee_id,
                timestamp=event_time,
                channel=channel,
                metadata=_generate_metadata(channel)
            )
        )
        
    return sorted(events, key=lambda e: e.timestamp)
