#!/usr/bin/env python3
"""
Script de prueba para las notificaciones de intrusos.
Simula la detección de un intruso y envía una notificación de escritorio.
"""

import sys
import os

# Agregar el directorio padre al path para importar los módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.notifier import notify_intruder, send_desktop_notification

def test_basic_notification():
    """Prueba una notificación básica del sistema"""
    print("🧪 Probando notificación básica del sistema...")
    send_desktop_notification(
        title="Monitor WiFi - Prueba",
        message="Esta es una notificación de prueba",
        urgency="normal",
        icon="network-wireless"
    )
    print("✅ Notificación básica enviada\n")

def test_intruder_notification():
    """Prueba una notificación de intruso"""
    print("🧪 Probando notificación de intruso...")
    
    # Simular datos de un intruso
    intruder_data = {
        'mac': 'aa:bb:cc:dd:ee:ff',
        'ip': '192.168.0.123',
        'vendor': 'Dispositivo Desconocido',
        'alias': 'Intruso Sospechoso'
    }
    
    notify_intruder(intruder_data)
    print("✅ Notificación de intruso enviada\n")

def test_critical_notification():
    """Prueba una notificación crítica"""
    print("🧪 Probando notificación crítica...")
    send_desktop_notification(
        title="🚨 ALERTA DE SEGURIDAD",
        message="Dispositivo no autorizado detectado en la red\nIP: 192.168.0.100\nMAC: aa:bb:cc:dd:ee:ff",
        urgency="critical",
        icon="security-high"
    )
    print("✅ Notificación crítica enviada\n")

if __name__ == "__main__":
    print("=" * 60)
    print("  PRUEBA DE NOTIFICACIONES - Monitor WiFi")
    print("=" * 60)
    print()
    
    # Ejecutar pruebas
    test_basic_notification()
    
    import time
    time.sleep(2)  # Esperar 2 segundos entre notificaciones
    
    test_critical_notification()
    
    time.sleep(2)
    
    test_intruder_notification()
    
    print("=" * 60)
    print("✅ Todas las pruebas completadas")
    print("=" * 60)
    print()
    print("💡 Si viste las notificaciones en tu escritorio, ¡todo funciona!")
    print("💡 Si no las viste, verifica que estés en un entorno gráfico (no SSH)")
