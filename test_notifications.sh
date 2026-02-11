#!/bin/bash
# Script de prueba para notificaciones de escritorio

echo "============================================================"
echo "  PRUEBA DE NOTIFICACIONES - Monitor WiFi"
echo "============================================================"
echo ""

# Verificar que notify-send está instalado
if ! command -v notify-send &> /dev/null; then
    echo "❌ notify-send no está instalado"
    echo "   Instala con: sudo apt install libnotify-bin"
    exit 1
fi

echo "✅ notify-send está instalado"
echo ""

# Prueba 1: Notificación básica
echo "🧪 Prueba 1: Notificación básica..."
notify-send -u normal -i network-wireless -a "Monitor WiFi" "Prueba de Notificación" "Esta es una notificación de prueba"
sleep 2

# Prueba 2: Notificación crítica
echo "🧪 Prueba 2: Notificación crítica..."
notify-send -u critical -i security-high -a "Monitor WiFi" "🚨 ALERTA DE SEGURIDAD" "Dispositivo no autorizado detectado"
sleep 2

# Prueba 3: Notificación de intruso (simulada)
echo "🧪 Prueba 3: Notificación de intruso..."
notify-send -u critical -i security-high -a "Monitor WiFi" "🚨 INTRUSO DETECTADO" "Dispositivo Desconocido
IP: 192.168.0.123
MAC: aa:bb:cc:dd:ee:ff"

echo ""
echo "============================================================"
echo "✅ Todas las pruebas completadas"
echo "============================================================"
echo ""
echo "💡 Si viste las notificaciones en tu escritorio, ¡todo funciona!"
echo "💡 Si no las viste, verifica que estés en un entorno gráfico"
echo ""
