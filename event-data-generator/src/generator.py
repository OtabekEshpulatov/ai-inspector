import json
import argparse
import os
from datetime import date, timedelta
from .profiles import generate_employees
from .behaviors import generate_events_for_day

def main():
    parser = argparse.ArgumentParser(description="Relationship Intelligence Fake Data Generator")
    parser.add_argument("--employees", type=int, default=100, help="Number of employees to generate or use")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory")
    parser.add_argument("--cross-dept-pct", type=float, default=30.0, help="Percentage of cross-department communications (0-100)")
    parser.add_argument("--events", type=int, default=None, help="Exact number of events to generate (overrides random distribution)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    employees_file = os.path.join(args.output_dir, "employees.json")
    
    if os.path.exists(employees_file):
        print(f"Loading existing employees from {employees_file}...")
        with open(employees_file, "r") as f:
            emp_data = json.load(f)
            from .models import Employee
            employees = [Employee(**data) for data in emp_data]
            import random
            if len(employees) > args.employees:
                employees = random.sample(employees, args.employees)
                print(f"Limited working set to {args.employees} employees from the existing file.")
            elif len(employees) < args.employees:
                print(f"Warning: Only {len(employees)} employees exist in the file. Using all of them.")
    else:
        print(f"Generating {args.employees} employees...")
        employees = generate_employees(args.employees)
        with open(employees_file, "w") as f:
            json.dump([e.__dict__ for e in employees], f, indent=2)
        print(f"Saved employee metadata to {employees_file}")

    current_date = date.today()
    total_events = []
    
    print(f"Generating events for {current_date}... ", end="")
    events = generate_events_for_day(current_date, employees, args.cross_dept_pct / 100.0, args.events)
    total_events.extend([e.to_dict() for e in events])
    print(f"[{len(events)} events]")
        
    # Generate timestamp for the filename
    current_datetime = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    output_filename = f"events_{current_datetime}.json"
    output_path = os.path.join(args.output_dir, output_filename)
            
    with open(output_path, "w") as f:
        json.dump(total_events, f, indent=2)
            
    print(f"Saved {len(total_events)} events to {output_path}")

if __name__ == "__main__":
    from datetime import datetime
    main()
