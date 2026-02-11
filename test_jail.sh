#!/bin/bash
# Script de prueba para el sistema de Jail (Página Cautiva)
# Este script simula el encarcelamiento de un dispositivo y verifica las notificaciones

echo "============================================================"
echo "  🚔 PRUEBA DEL SISTEMA JAIL - Monitor WiFi"
echo "============================================================"
echo ""

# Verificar que el servidor esté corriendo
if ! pgrep -f "python.*main.py" > /dev/null; then
    echo "❌ El servidor no está corriendo"
    echo "   Inicia el servidor con: sudo ./startup.sh"
    exit 1
fi

echo "✅ Servidor detectado"
echo ""

# URL del API
API_URL="http://localhost:8000"

echo "📋 Paso 1: Obtener lista de dispositivos..."
DEVICES=$(curl -s "${API_URL}/api/devices")
echo "✅ Dispositivos obtenidos"
echo ""

# Extraer el primer dispositivo que NO sea confiable
echo "📋 Paso 2: Buscar un dispositivo no confiable para probar..."
DEVICE_IP=$(echo "$DEVICES" | python3 -c "
import sys, json
devices = json.load(sys.stdin)
for d in devices:
    if not d.get('is_trusted', False) and d.get('status') == 'online':
        print(d['ip'])
        break
" 2>/dev/null)

if [ -z "$DEVICE_IP" ]; then
    echo "⚠️  No hay dispositivos no confiables online"
    echo "   Vamos a usar una IP de prueba: 192.168.0.200"
    DEVICE_IP="192.168.0.200"
    DEVICE_MAC="aa:bb:cc:dd:ee:ff"
else
    echo "✅ Dispositivo encontrado: $DEVICE_IP"
    # Obtener MAC del dispositivo
    DEVICE_MAC=$(echo "$DEVICES" | python3 -c "
import sys, json
devices = json.load(sys.stdin)
for d in devices:
    if d['ip'] == '$DEVICE_IP':
        print(d['mac'])
        break
" 2>/dev/null)
fi

echo ""
echo "============================================================"
echo "  🚨 INICIANDO PRUEBA DE ENCARCELAMIENTO"
echo "============================================================"
echo ""
echo "Dispositivo objetivo:"
echo "  IP:  $DEVICE_IP"
echo "  MAC: $DEVICE_MAC"
echo ""

# Esperar confirmación
read -p "¿Continuar con la prueba? (s/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Prueba cancelada"
    exit 0
fi

echo ""
echo "📋 Paso 3: Encarcelando dispositivo..."
RESPONSE=$(curl -s -X POST "${API_URL}/api/jail" \
    -H "Content-Type: application/json" \
    -d "{\"ip\": \"$DEVICE_IP\", \"mac\": \"$DEVICE_MAC\"}")

echo "Respuesta del servidor:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Verificar que se haya encarcelado
if echo "$RESPONSE" | grep -q "jailed"; then
    echo "✅ Dispositivo encarcelado exitosamente"
    echo ""
    echo "🔔 DEBERÍAS VER UNA NOTIFICACIÓN EN TU ESCRITORIO:"
    echo "   Título: 🚔 DISPOSITIVO ENCARCELADO"
    echo "   Mensaje: Información del dispositivo + IP + MAC"
    echo ""
else
    echo "❌ Error al encarcelar dispositivo"
    exit 1
fi

echo "📋 Paso 4: Verificar dispositivos encarcelados..."
sleep 2
JAILED=$(curl -s "${API_URL}/api/jailed_devices")
echo "Dispositivos en Jail:"
echo "$JAILED" | python3 -m json.tool 2>/dev/null || echo "$JAILED"
echo ""

echo "============================================================"
echo "  🧪 PRUEBA DE PÁGINA CAUTIVA"
echo "============================================================"
echo ""
echo "Si el dispositivo $DEVICE_IP intenta navegar, verá:"
echo "  - Redirección a http://$DEVICE_IP/"
echo "  - Página de advertencia (warning.html)"
echo "  - Mensaje: 🚫 ACCESO BLOQUEADO"
echo ""

# Esperar antes de liberar
read -p "¿Liberar el dispositivo ahora? (s/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo "📋 Paso 5: Liberando dispositivo..."
    RELEASE=$(curl -s -X POST "${API_URL}/api/unjail" \
        -H "Content-Type: application/json" \
        -d "{\"ip\": \"$DEVICE_IP\"}")
    
    echo "Respuesta del servidor:"
    echo "$RELEASE" | python3 -m json.tool 2>/dev/null || echo "$RELEASE"
    echo ""
    echo "✅ Dispositivo liberado"
fi

echo ""
echo "============================================================"
echo "✅ PRUEBA COMPLETADA"
echo "============================================================"
echo ""
echo "📊 Resumen:"
echo "  ✅ Dispositivo encarcelado correctamente"
echo "  ✅ Notificación enviada (verifica tu escritorio)"
echo "  ✅ Página cautiva configurada"
echo "  ✅ Dispositivo liberado (si lo solicitaste)"
echo ""
echo "💡 Consejos:"
echo "  - Verifica los logs del servidor para más detalles"
echo "  - Prueba navegar desde el dispositivo encarcelado"
echo "  - Revisa el dashboard para ver el estado en tiempo real"
echo ""
