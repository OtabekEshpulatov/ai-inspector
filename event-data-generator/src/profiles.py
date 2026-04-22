import random
from faker import Faker
from .models import Employee

fake = Faker()

DEPARTMENTS = ["Engineering", "Sales", "HR", "Marketing", "Executive", "Finance"]
ROLES = ["Staff", "Senior", "Lead", "Manager", "Director"]

def generate_employees(count: int, insider_count: int = 3, resigning_count: int = 2) -> list[Employee]:
    employees = []
    
    for _ in range(count):
        emp = Employee(
            employee_id=f"emp_{fake.unique.random_number(digits=6)}",
            name=fake.name(),
            department=random.choice(DEPARTMENTS),
            role=random.choice(ROLES)
        )
        employees.append(emp)
        
    # Assign special tags
    if len(employees) >= insider_count + resigning_count:
        insiders = random.sample(employees, insider_count)
        for i in insiders:
            i.is_insider = True
            
        non_insider = [e for e in employees if not e.is_insider]
        resigners = random.sample(non_insider, min(resigning_count, len(non_insider)))
        for r in resigners:
            r.is_resigning = True
        
    return employees
