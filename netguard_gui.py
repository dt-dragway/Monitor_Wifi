
import sys
import time
import threading
import requests
import webview
from webview.menu import Menu, MenuAction

# Configuración
BACKEND_URL = "http://localhost:8000"
WINDOW_TITLE = "NetGuard Profesional"
ICON_PATH = "/opt/netguard/icon.png"

def check_backend():
    """Espera a que el backend esté listo antes de mostrar la UI real"""
    max_retries = 30 # 30 segundos máximo de espera al inicio
    for _ in range(max_retries):
        try:
            r = requests.get(f"{BACKEND_URL}/api/devices", timeout=2)
            if r.status_code == 200:
                return True
        except:
            time.sleep(1)
    return False

def on_loaded():
    # Lógica al cargar (opcional)
    pass

def load_ui(window):
    # Mostrar pantalla de carga
    window.load_url(f"data:text/html,<html><body style='background:#0f172a;color:white;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif;'><h1>🛡️ Iniciando NetGuard...</h1></body></html>")
    
    # Verificar backend en hilo aparte para no congelar UI
    if check_backend():
        window.load_url(BACKEND_URL)
    else:
        window.load_url(f"data:text/html,<html><body style='background:#0f172a;color:#ef4444;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif;'><h1>❌ Error: El servicio NetGuard no responde.</h1><p>Verifica 'systemctl status netguard'</p></body></html>")

if __name__ == '__main__':
    # Crear ventana
    window = webview.create_window(
        WINDOW_TITLE, 
        url='about:blank',
        width=1280, 
        height=800, 
        resizable=True,
        min_size=(800, 600)
    )
    
    # Iniciar carga
    webview.start(load_ui, window)
