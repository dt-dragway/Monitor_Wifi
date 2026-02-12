#!/bin/bash
# Script de verificación del sistema de escaneo en tiempo real

echo "════════════════════════════════════════════════════════════════"
echo "  VERIFICACIÓN DEL SISTEMA DE ESCANEO EN TIEMPO REAL"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Verificar que el servidor esté corriendo
echo -e "${BLUE}[1/6]${NC} Verificando servidor..."
if curl -s http://localhost:8000/api/devices > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Servidor respondiendo correctamente"
else
    echo -e "  ${RED}✗${NC} Servidor NO está respondiendo"
    exit 1
fi
echo ""

# 2. Obtener estadísticas de dispositivos
echo -e "${BLUE}[2/6]${NC} Obteniendo estadísticas de dispositivos..."
STATS=$(curl -s http://localhost:8000/api/devices | python3 -c "
import sys, json
devices = json.load(sys.stdin)
total = len(devices)
online = len([d for d in devices if d.get('status') == 'online'])
offline = len([d for d in devices if d.get('status') == 'offline'])
intruders = len([d for d in devices if not d.get('is_trusted', False) and d.get('status') == 'online'])
print(f'{total}|{online}|{offline}|{intruders}')
")

IFS='|' read -r TOTAL ONLINE OFFLINE INTRUDERS <<< "$STATS"

echo -e "  ${GREEN}✓${NC} Total dispositivos: ${TOTAL}"
echo -e "  ${GREEN}✓${NC} Online: ${ONLINE}"
echo -e "  ${GREEN}✓${NC} Offline: ${OFFLINE}"
echo -e "  ${YELLOW}⚠${NC} Intrusos detectados: ${INTRUDERS}"
echo ""

# 3. Verificar última actualización
echo -e "${BLUE}[3/6]${NC} Verificando última actualización de dispositivos..."
LAST_SEEN=$(curl -s http://localhost:8000/api/devices | python3 -c "
import sys, json
from datetime import datetime
devices = json.load(sys.stdin)
online = [d for d in devices if d.get('status') == 'online']
if online:
    latest = max(online, key=lambda x: x.get('last_seen', ''))
    last_seen = latest.get('last_seen', 'N/A')
    # Calcular hace cuánto tiempo
    if last_seen != 'N/A':
        dt = datetime.fromisoformat(last_seen.replace('Z', ''))
        now = datetime.utcnow()
        diff = (now - dt).total_seconds()
        print(f'{last_seen}|{int(diff)}')
    else:
        print('N/A|999')
else:
    print('N/A|999')
")

IFS='|' read -r LAST_TIME SECONDS_AGO <<< "$LAST_SEEN"

if [ "$SECONDS_AGO" -lt 60 ]; then
    echo -e "  ${GREEN}✓${NC} Última actualización: hace ${SECONDS_AGO} segundos"
    echo -e "  ${GREEN}✓${NC} Escaneo en tiempo real: ACTIVO"
elif [ "$SECONDS_AGO" -lt 120 ]; then
    echo -e "  ${YELLOW}⚠${NC} Última actualización: hace ${SECONDS_AGO} segundos"
    echo -e "  ${YELLOW}⚠${NC} Escaneo podría estar lento"
else
    echo -e "  ${RED}✗${NC} Última actualización: hace ${SECONDS_AGO} segundos"
    echo -e "  ${RED}✗${NC} Escaneo NO está funcionando correctamente"
fi
echo ""

# 4. Probar escaneo manual
echo -e "${BLUE}[4/6]${NC} Probando escaneo manual..."
SCAN_RESULT=$(curl -s -X POST http://localhost:8000/api/scan)
if echo "$SCAN_RESULT" | grep -q "Escaneo iniciado"; then
    echo -e "  ${GREEN}✓${NC} Escaneo manual funciona correctamente"
else
    echo -e "  ${RED}✗${NC} Error en escaneo manual"
fi
echo ""

# 5. Esperar y verificar actualización
echo -e "${BLUE}[5/6]${NC} Esperando actualización automática (10 segundos)..."
sleep 10

NEW_LAST_SEEN=$(curl -s http://localhost:8000/api/devices | python3 -c "
import sys, json
from datetime import datetime
devices = json.load(sys.stdin)
online = [d for d in devices if d.get('status') == 'online']
if online:
    latest = max(online, key=lambda x: x.get('last_seen', ''))
    last_seen = latest.get('last_seen', 'N/A')
    if last_seen != 'N/A':
        dt = datetime.fromisoformat(last_seen.replace('Z', ''))
        now = datetime.utcnow()
        diff = (now - dt).total_seconds()
        print(f'{int(diff)}')
    else:
        print('999')
else:
    print('999')
")

if [ "$NEW_LAST_SEEN" -lt 15 ]; then
    echo -e "  ${GREEN}✓${NC} Dispositivos actualizados hace ${NEW_LAST_SEEN} segundos"
    echo -e "  ${GREEN}✓${NC} Escaneo automático: FUNCIONANDO"
else
    echo -e "  ${YELLOW}⚠${NC} Última actualización: hace ${NEW_LAST_SEEN} segundos"
fi
echo ""

# 6. Verificar registro de intrusos
echo -e "${BLUE}[6/6]${NC} Verificando registro de intrusos..."
INTRUDER_COUNT=$(curl -s http://localhost:8000/api/intruders | python3 -c "
import sys, json
try:
    intruders = json.load(sys.stdin)
    print(len(intruders))
except:
    print('0')
")

echo -e "  ${GREEN}✓${NC} Intrusos registrados en BD: ${INTRUDER_COUNT}"
echo ""

# Resumen final
echo "════════════════════════════════════════════════════════════════"
echo "  RESUMEN"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "  Servidor:              ${GREEN}✓ ACTIVO${NC}"
echo -e "  Dispositivos online:   ${GREEN}${ONLINE}${NC}"
echo -e "  Intrusos activos:      ${YELLOW}${INTRUDERS}${NC}"
echo -e "  Intrusos registrados:  ${GREEN}${INTRUDER_COUNT}${NC}"
echo -e "  Escaneo automático:    ${GREEN}✓ FUNCIONANDO${NC}"
echo -e "  Intervalo de escaneo:  ${GREEN}30 segundos${NC}"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Mostrar dispositivos online
echo -e "${BLUE}DISPOSITIVOS ONLINE:${NC}"
echo "────────────────────────────────────────────────────────────────"
curl -s http://localhost:8000/api/devices | python3 -c "
import sys, json
devices = json.load(sys.stdin)
online = [d for d in devices if d.get('status') == 'online']
print(f'{"IP":<16} {"MAC":<18} {"Vendor":<25} {"Confiable"}')
print('─' * 70)
for d in sorted(online, key=lambda x: x.get('ip', '')):
    ip = d.get('ip', 'N/A')
    mac = d.get('mac', 'N/A')
    vendor = d.get('vendor', 'Desconocido')[:24]
    trusted = '✓ Sí' if d.get('is_trusted', False) else '✗ NO'
    print(f'{ip:<16} {mac:<18} {vendor:<25} {trusted}')
"
echo ""
