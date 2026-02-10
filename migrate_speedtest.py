
from sqlmodel import SQLModel
from backend.database import engine
from backend.models import SpeedTestResult

print("Creando tabla SpeedTestResult...")
SQLModel.metadata.create_all(engine)
print("Tabla SpeedTestResult creada.")
