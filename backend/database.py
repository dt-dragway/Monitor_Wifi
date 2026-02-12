from sqlmodel import SQLModel, create_engine, Session
from .models import Device

sqlite_file_name = "devices.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    # Optimización SQLite para concurrencia (WAL Mode)
    from sqlalchemy import text
    with engine.connect() as connection:
        connection.execute(text("PRAGMA journal_mode=WAL;"))
        connection.execute(text("PRAGMA synchronous=NORMAL;")) # Más velocidad, algo menos seguridad (crash)

def get_session():
    with Session(engine) as session:
        yield session
