from sqlmodel import Session
from datetime import datetime
from .database import engine
from .models import EventLog

def log_event(event_type: str, message: str, device_mac: str = None):
    """
    Registra un evento en la base de datos.
    Tipos sugeridos: INFO, WARNING, DANGER, SYSTEM
    """
    try:
        with Session(engine) as session:
            event = EventLog(
                timestamp=datetime.utcnow(),
                event_type=event_type,
                message=message,
                device_mac=device_mac
            )
            session.add(event)
            session.commit()
            print(f"📝 LOG [{event_type}]: {message}")
            
            # Notificar si es importante
            if event_type in ["WARNING", "DANGER"]:
                from .notifier import send_notification
                send_notification(message, event_type)
                
    except Exception as e:
        print(f"Error logging event: {e}")
