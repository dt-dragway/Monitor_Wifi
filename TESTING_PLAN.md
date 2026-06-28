# Plan de Testing Profesional - Monitor WiFi
**Fecha**: 2026-02-10
**Versión**: 1.0

## 1. PRUEBAS DE BACKEND (API)

### 1.1 Endpoints Críticos
- [ ] `GET /api/devices` - Lista de dispositivos
- [ ] `GET /api/traffic` - Estadísticas de tráfico en tiempo real
- [ ] `GET /api/traffic/monthly` - Consumo mensual agregado
- [ ] `GET /api/traffic/history/{mac}?period={range}` - Historial por dispositivo
- [ ] `GET /api/events` - Logs del sistema
- [ ] `POST /api/scan` - Escaneo manual
- [ ] `GET /api/speedtest/history` - Historial de velocidad
- [ ] `GET /api/topology` - Mapa de red

### 1.2 Funcionalidades de Seguridad
- [ ] `POST /api/devices/{ip}/warn` - Activar protocolo de expulsión
- [ ] `POST /api/devices/{ip}/unwarn` - Desactivar protocolo
- [ ] `GET /api/jailed_devices` - Lista de dispositivos en jail
- [ ] `GET /api/blocked_devices` - Lista de bloqueados

### 1.3 Gestión de Dispositivos
- [ ] `POST /api/devices/{mac}/trust` - Marcar como confiable
- [ ] `POST /api/devices/{mac}/alias` - Asignar nombre
- [ ] Persistencia de estado (bloqueos sobreviven reinicio)

## 2. PRUEBAS DE FRONTEND

### 2.1 Dashboard
- [ ] Contador de dispositivos (Total/Online/Intrusos)
- [ ] Velocidad de Internet en tiempo real (Mbps)
- [ ] Top Talkers (Mayor Consumo Mensual)
  - [ ] Paginación funcional (< >)
  - [ ] Velocidad en tiempo real por dispositivo
  - [ ] Dispositivos offline con histórico
- [ ] Actividad Reciente (logs)
- [ ] Actualización automática cada 1-3 segundos

### 2.2 Gestión de Dispositivos
- [ ] Filtros por categoría (Todos/Intrusos/Confiables/Bloqueados/Offline)
- [ ] Búsqueda por IP/MAC/Alias
- [ ] Paginación
- [ ] Editar alias
- [ ] Marcar como confiable/desconfiar
- [ ] Historial de tráfico (modal)
  - [ ] Botones de rango (24h/7d/30d/1año/Todo)
  - [ ] Indicador de carga
  - [ ] Botón activo resaltado

### 2.3 Mapa de Red
- [ ] Visualización de topología
- [ ] Nodos diferenciados (Gateway/Dispositivos/Intrusos)
- [ ] Actualización dinámica

### 2.4 Monitor de Velocidad
- [ ] Gráfica de historial
- [ ] Botón "Iniciar Test"
- [ ] Resultado mostrado correctamente

## 3. PRUEBAS DE INTEGRACIÓN

### 3.1 Persistencia de Datos
- [ ] TrafficLog se guarda cada 60 segundos
- [ ] Dispositivos bloqueados persisten tras reinicio
- [ ] Configuración de webhook se mantiene

### 3.2 Módulos de Seguridad
- [ ] Traffic Analyzer captura paquetes
- [ ] Jail redirecciona dispositivos correctamente
- [ ] Blocker aplica reglas

## 4. PRUEBAS DE RENDIMIENTO

- [ ] Frontend responde en < 200ms
- [ ] API endpoints responden en < 500ms
- [ ] Uso de memoria estable (sin leaks)
- [ ] CPU < 30% en idle

## 5. PRUEBAS DE ERRORES

- [ ] Manejo de dispositivo inexistente (404)
- [ ] Manejo de parámetros inválidos
- [ ] Recuperación ante fallo de base de datos
- [ ] Timeout en speedtest

---

## RESULTADO ESPERADO
✅ **PASS**: Todas las funcionalidades críticas operativas
⚠️ **WARN**: Funcionalidades secundarias con issues menores
❌ **FAIL**: Funcionalidades críticas rotas
