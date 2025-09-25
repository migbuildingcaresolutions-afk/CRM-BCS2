from app import db
from models import Service

services = [
    {"category": "Cleaning", "name": "Basic Janitorial", "unit_price": 75},
    {"category": "Cleaning", "name": "Deep Cleaning", "unit_price": 150},
    {"category": "Maintenance", "name": "HVAC Inspection", "unit_price": 120},
    {"category": "Maintenance", "name": "Light Fixture Replacement", "unit_price": 90},
    {"category": "Exterior", "name": "Window Washing", "unit_price": 100},
    {"category": "Exterior", "name": "Pressure Washing", "unit_price": 130},
]

for s in services:
    db.session.add(Service(**s))
db.session.commit()
print("Services seeded.")
