from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class Device(SQLModel, table=True):
    mac: str = Field(primary_key=True)
    ip: str
    vendor: Optional[str] = None
    alias: Optional[str] = None
    is_trusted: bool = Field(default=False)
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="offline") # online, offline, blocked
