
import requests
from sqlmodel import Session, select
from .database import engine
from .models import Settings

def send_notification(message: str, level: str = "INFO"):
    """
    Envía una notificación al Webhook configurado (Discord/Slack/Telegram).
    """
    try:
        with Session(engine) as session:
            # Obtener URL del webhook
            setting = session.get(Settings, "webhook_url")
            if not setting or not setting.value:
                return # No hay webhook configurado
            
            webhook_url = setting.value
            
            # Formato simple para Discord/Slack
            # Si es Discord, podemos usar embeds para colores
            
            payload = {}
            if "discord" in webhook_url:
                color = 3447003 # Blue
                if level == "WARNING": color = 16776960 # Yellow
                if level == "DANGER": color = 15158332 # Red
                
                payload = {
                    "embeds": [{
                        "title": f"🚨 Monitor Wifi: {level}",
                        "description": message,
                        "color": color
                    }]
                }
            else:
                # Genérico
                payload = {"text": f"[{level}] {message}"}
            
            requests.post(webhook_url, json=payload, timeout=5)
            
    except Exception as e:
        print(f"Error enviando notificación: {e}")
