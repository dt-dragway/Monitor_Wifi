
import requests
import subprocess
import os
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


def send_desktop_notification(title: str, message: str, urgency: str = "normal", icon: str = "network-wireless"):
    """
    Envía una notificación de escritorio del sistema usando notify-send (Linux).
    
    Args:
        title: Título de la notificación
        message: Mensaje de la notificación
        urgency: Nivel de urgencia ('low', 'normal', 'critical')
        icon: Icono a mostrar ('network-wireless', 'security-high', 'dialog-warning', etc.)
    """
    try:
        # Verificar si notify-send está disponible
        if subprocess.run(["which", "notify-send"], capture_output=True).returncode != 0:
            print("notify-send no está instalado. Instala con: sudo apt install libnotify-bin")
            return
        
        # Obtener el DISPLAY y DBUS_SESSION_BUS_ADDRESS del usuario actual
        # Esto es necesario cuando se ejecuta con sudo
        display = os.environ.get('DISPLAY', ':0')
        
        # Construir el comando
        cmd = [
            "notify-send",
            "-u", urgency,  # Urgencia: low, normal, critical
            "-i", icon,     # Icono
            "-a", "Monitor WiFi",  # Nombre de la aplicación
            title,
            message
        ]
        
        # Ejecutar en el contexto del usuario (no root)
        env = os.environ.copy()
        env['DISPLAY'] = display
        
        # Intentar obtener el usuario real (no root)
        sudo_user = os.environ.get('SUDO_USER')
        if sudo_user:
            # Ejecutar como el usuario que invocó sudo
            subprocess.Popen(
                ["sudo", "-u", sudo_user] + cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # Ejecutar normalmente
            subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        print(f"✅ Notificación enviada: {title} - {message}")
        
    except Exception as e:
        print(f"Error enviando notificación de escritorio: {e}")


def notify_intruder(device_info: dict):
    """
    Envía notificaciones cuando se detecta un intruso.
    
    Args:
        device_info: Diccionario con información del dispositivo
                     {mac, ip, vendor, alias}
    """
    vendor = device_info.get('vendor', 'Desconocido')
    ip = device_info.get('ip', 'N/A')
    mac = device_info.get('mac', 'N/A')
    alias = device_info.get('alias', '')
    
    # Construir mensaje
    device_name = alias if alias else vendor
    title = "🚨 INTRUSO DETECTADO"
    message = f"{device_name}\nIP: {ip}\nMAC: {mac}"
    
    # Enviar notificación de escritorio (crítica)
    send_desktop_notification(
        title=title,
        message=message,
        urgency="critical",
        icon="security-high"
    )
    
    # También enviar a webhook si está configurado
    webhook_message = f"⚠️ **INTRUSO DETECTADO**\n\n**Dispositivo:** {device_name}\n**IP:** {ip}\n**MAC:** {mac}\n**Vendor:** {vendor}"
    send_notification(webhook_message, level="DANGER")
    
    print(f"🚨 ALERTA: Intruso detectado - {device_name} ({ip})")
