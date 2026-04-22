# Event Data Generator

A Python-based simulation engine designed to generate realistic corporate communication structures, natural department clustering, and anomalous data exfiltration behaviors.

## Overview
This tool randomly generates fake `Employee` directories, then simulates chronologically sequential communication events (emails, slacks, USB transfers) across those employees. It serves as the primary data seeding tool for the Relationship Intelligence Graph model.

## Features
- **Idempotency Ready**: Generates UUID `event_id` keys perfectly compatible with downstream Redis architectures.
- **Natural Grouping**: Natively biases communication to remain inside an employee's immediate department.
- **Insider Threat Simulation**: Forces cross-department/after-hours events strictly out of specific flagged individuals utilizing `telegram`/`usb` tags to spoof insider behavior metrics.
- **Stateful Execution**: Seamlessly retains memory of the `employees.json` files between executions to continually build history on static graph targets!

## Usage

Create a virtual environment and run the generator:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 -m src.generator --employees 50 --cross-dept-pct 15 --events 5000
```

### Arguments
| Flag | Description | Default |
| :--- | :--- | :--- |
| `--employees` | Number of employees to generate or pull from the local JSON registry. | `100` |
| `--cross-dept-pct` | The exact percentage of traffic that spills across different departments. | `30.0` |
| `--events` | Override calendar-based generation logic and explicitly output $X events. | `None` |
| `--output-dir` | Directory string to export the payloads. | `data/` |
