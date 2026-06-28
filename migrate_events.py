
from sqlmodel import SQLModel
from backend.database import engine
from backend.models import EventLog

print("Creando tabla EventLog...")
SQLModel.metadata.create_all(engine)
print("Tabla creada.")
