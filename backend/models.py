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
    status: str = Field(default="offline") # online, offline
    is_blocked: bool = Field(default=False)
    interface: Optional[str] = None # wlan0, eno1, etc

class EventLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str # INFO, WARNING, DANGER, SYSTEM
    message: str
    device_mac: Optional[str] = None

class Settings(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str

class SpeedTestResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ping: float # ms
    download: float # Mbps
    download: float # Mbps
    upload: float # Mbps

class TrafficLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    device_mac: str
    bytes_down: int
    bytes_up: int

class IntruderLog(SQLModel, table=True):
    """Registro de intrusos detectados"""
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    device_mac: str
    device_ip: str
    vendor: Optional[str] = None
    alias: Optional[str] = None
    detection_type: str # "new_device" o "reconnection"
