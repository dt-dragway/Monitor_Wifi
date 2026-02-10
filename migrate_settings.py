
from sqlmodel import SQLModel
from backend.database import engine
from backend.models import Settings

print("Creando tabla Settings...")
SQLModel.metadata.create_all(engine)
print("Tabla Settings creada.")
