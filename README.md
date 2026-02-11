# 🛡️ Monitor WiFi Profesional

<div align="center">

**Sistema Avanzado de Monitoreo y Seguridad de Red Local**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production-success.svg)]()

*Monitoreo en tiempo real • Detección de intrusos • Análisis de tráfico • Speedtest integrado*

</div>

---

## 📋 Tabla de Contenidos

- [Características](#-características-principales)
- [Capturas de Pantalla](#-capturas-de-pantalla)
- [Instalación](#-instalación-rápida)
- [Uso](#-uso)
- [Arquitectura](#-arquitectura-del-sistema)
- [API](#-api-rest)
- [Configuración](#-configuración-avanzada)
- [Troubleshooting](#-troubleshooting)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## 🚀 Características Principales

### 🎨 **Interfaz Moderna con Glassmorphism**
- ✨ Diseño oscuro premium con efectos de cristal y desenfoque
- 🎭 Animaciones fluidas y transiciones suaves
- 📱 Totalmente responsivo (Desktop, Tablet, Mobile)
- 🎯 Iconos dinámicos según tipo de dispositivo (Windows, Apple, Android, IoT, etc.)
- 💾 Persistencia de estado (recuerda tu última vista)

### 📊 **Dashboard en Tiempo Real**
- 🌐 **Velocidad de Red**: Monitoreo instantáneo del ancho de banda (actualización cada segundo)
- 📈 **Estadísticas Globales**: Dispositivos online/offline, intrusos detectados, tráfico total
- 🔔 **Actividad Reciente**: Log de eventos en tiempo real (conexiones, desconexiones, alertas)
- 📉 **Gráficos Interactivos**: Visualización de tráfico con Chart.js

### 🔍 **Gestión Avanzada de Dispositivos**
- 🖥️ **Detección Automática**: Escaneo ARP cada 30 segundos
- 🏷️ **Identificación Inteligente**: 
  - Vendor lookup (fabricante del dispositivo)
  - Hostname resolution automático
  - Iconos personalizados por tipo
- ✏️ **Personalización**:
  - Alias personalizados
  - Marcar como confiable/intruso
  - Notas y descripciones
- 📊 **Análisis Individual**:
  - Historial de tráfico (24h, 7d, 30d, 1 año, todo)
  - Gráficos de consumo (descarga/subida)
  - Última conexión y tiempo online

### 🚦 **Análisis de Tráfico**
- 📡 **Captura en Tiempo Real**: Sniffing de paquetes con Scapy
- 📊 **Métricas por Dispositivo**:
  - Bytes descargados/subidos
  - Velocidad instantánea (Mbps)
  - Consumo acumulado
- 📈 **Historial Detallado**:
  - Gráficos interactivos con Chart.js
  - Filtros por período (24h, 7d, 30d, 365d, todo)
  - Exportación de datos
- 🏆 **Top Talkers**: Ranking de dispositivos por consumo

### 🚀 **Speedtest Integrado**
- ⚡ **Tests Automáticos**: Programados cada 4 horas
- 📊 **Métricas Completas**:
  - Velocidad de descarga (Mbps)
  - Velocidad de subida (Mbps)
  - Latencia/Ping (ms)
- 📈 **Historial Gráfico**: Evolución de la velocidad en el tiempo
- 🎯 **Ejecución Manual**: Botón para test on-demand

### 🗺️ **Mapa de Red (Topología)**
- 🌐 **Visualización Interactiva**: Grafo de red con Vis.js
- 🎨 **Nodos Personalizados**:
  - Gateway (router)
  - Servidor (este equipo)
  - Dispositivos confiables
  - Intrusos detectados
- 🔗 **Conexiones Dinámicas**: Relaciones entre dispositivos
- 🎯 **Interactividad**: Click en nodos para ver detalles

### 🛡️ **Seguridad Avanzada**

#### **Sistema de Jail (Aislamiento)**
- 🔒 **Aislamiento de Dispositivos**: Bloqueo temporal de acceso
- ⏱️ **Duración Configurable**: Tiempo de jail personalizable
- 📝 **Razones Documentadas**: Registro del motivo de jail
- 🔓 **Liberación Manual**: Restaurar acceso cuando sea necesario

#### **Bloqueo Permanente**
- 🚫 **Blacklist**: Bloqueo definitivo de dispositivos
- 📋 **Gestión Centralizada**: Lista de dispositivos bloqueados
- 🔄 **Reversible**: Desbloqueo cuando sea necesario

#### **Detección de Intrusos**
- 🚨 **Alertas Automáticas**: Notificación de dispositivos no confiables
- 🔔 **Contador en Dashboard**: Intrusos activos en tiempo real
- 📊 **Historial de Eventos**: Log completo de actividad sospechosa

### 📱 **Notificaciones**
- 📧 **Email**: Alertas por correo electrónico (SMTP configurable)
- 💬 **Telegram**: Notificaciones instantáneas vía bot
- 🔔 **Eventos Monitoreados**:
  - Nuevos dispositivos detectados
  - Intrusos conectados
  - Dispositivos desconectados
  - Cambios de estado

### 📈 **Monitoreo y Logs**
- 📝 **Event Log**: Registro completo de eventos del sistema
- 🕐 **Timestamps**: Marcas de tiempo precisas
- 🏷️ **Categorización**: INFO, WARNING, ALERT
- 🔍 **Búsqueda y Filtrado**: Encuentra eventos específicos

---

## 📸 Capturas de Pantalla

### Dashboard Principal
![Dashboard](https://via.placeholder.com/800x450/1e293b/60a5fa?text=Dashboard+en+Tiempo+Real)

*Vista principal con estadísticas en tiempo real, velocidad de red y actividad reciente*

### Gestión de Dispositivos
![Devices](https://via.placeholder.com/800x450/1e293b/10b981?text=Gestión+de+Dispositivos)

*Lista completa de dispositivos con estado, vendor, IP y acciones rápidas*

### Mapa de Red
![Network Map](https://via.placeholder.com/800x450/1e293b/f59e0b?text=Topología+de+Red)

*Visualización gráfica de la topología de red con nodos interactivos*

### Speedtest
![Speedtest](https://via.placeholder.com/800x450/1e293b/ec4899?text=Test+de+Velocidad)

*Historial de tests de velocidad con gráficos de evolución*

---

## ⚡ Instalación Rápida

### Requisitos Previos

- **Sistema Operativo**: Linux (Ubuntu 20.04+, Debian 11+, Linux Mint 20+)
- **Python**: 3.10 o superior
- **Privilegios**: `sudo` (necesario para escaneo ARP y captura de paquetes)
- **Dependencias del Sistema**:
  ```bash
  sudo apt update
  sudo apt install -y python3 python3-pip python3-venv git libpcap-dev
  ```

### Instalación en 3 Pasos

#### 1️⃣ Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/monitor-wifi-pro.git
cd monitor-wifi-pro
```

#### 2️⃣ Ejecutar el Script de Inicio
```bash
sudo ./startup.sh
```

El script automáticamente:
- ✅ Crea un entorno virtual Python
- ✅ Instala todas las dependencias
- ✅ Inicializa la base de datos
- ✅ Inicia el servidor FastAPI
- ✅ Lanza los módulos de monitoreo

#### 3️⃣ Acceder al Dashboard
Abre tu navegador en:

🌐 **http://localhost:8000**

---

## 🎯 Uso

### Inicio Automático

El sistema se inicia automáticamente con `startup.sh`:

```bash
sudo ./startup.sh
```

### Detener el Sistema

```bash
# Presiona Ctrl+C en la terminal donde se ejecuta
# O mata el proceso:
sudo pkill -f "python.*main.py"
```

### Acceso Remoto

Para acceder desde otros dispositivos en tu red:

```bash
# Edita main.py y cambia:
uvicorn.run(app, host="0.0.0.0", port=8000)

# Luego accede desde cualquier dispositivo:
http://IP_DEL_SERVIDOR:8000
```

### Navegación

- **Dashboard**: Vista general con estadísticas en tiempo real
- **Dispositivos**: Gestión completa de dispositivos detectados
- **Mapa**: Visualización gráfica de la topología de red
- **Speedtest**: Pruebas de velocidad e historial

### Acciones Comunes

#### Marcar Dispositivo como Confiable
1. Ve a la pestaña **Dispositivos**
2. Encuentra el dispositivo
3. Click en el icono de escudo (🛡️)
4. Confirma la acción

#### Ver Historial de Tráfico
1. En la lista de dispositivos
2. Click en el icono de gráfico (📊)
3. Selecciona el período (24h, 7d, 30d, etc.)

#### Aislar Dispositivo (Jail)
1. Click en el menú (⋮) del dispositivo
2. Selecciona "Jail"
3. Ingresa duración y razón
4. Confirma

#### Ejecutar Speedtest
1. Ve a la pestaña **Speedtest**
2. Click en "Ejecutar Test de Velocidad"
3. Espera los resultados (~30 segundos)

---

## 🏗️ Arquitectura del Sistema

### Estructura del Proyecto

```
monitor-wifi-pro/
├── main.py                 # Aplicación FastAPI principal
├── startup.sh              # Script de inicio automático
├── requirements.txt        # Dependencias Python
├── devices.db             # Base de datos SQLite
│
├── backend/
│   ├── __init__.py
│   ├── database.py        # Configuración SQLModel
│   ├── models.py          # Modelos de datos (Device, TrafficLog, etc.)
│   ├── service.py         # Lógica de escaneo de red
│   ├── traffic_analyzer.py # Captura y análisis de tráfico
│   ├── logger.py          # Sistema de logging
│   ├── notifier.py        # Notificaciones (Email, Telegram)
│   ├── speedtest_service.py # Tests de velocidad
│   ├── security.py        # Módulos de seguridad (Jail, Block)
│   └── topology.py        # Generación de topología de red
│
├── templates/
│   └── index.html         # Plantilla HTML principal
│
├── static/
│   ├── css/
│   │   └── styles.css     # Estilos personalizados
│   └── js/
│       └── app.js         # Lógica frontend (Vanilla JS)
│
└── docs/
    ├── TESTING_PLAN.md
    ├── TESTING_REPORT.md
    └── API_DOCUMENTATION.md
```

### Stack Tecnológico

#### Backend
- **FastAPI**: Framework web moderno y rápido
- **SQLModel**: ORM con validación Pydantic
- **SQLite**: Base de datos embebida
- **Scapy**: Captura y análisis de paquetes
- **Uvicorn**: Servidor ASGI de alto rendimiento

#### Frontend
- **HTML5**: Estructura semántica
- **TailwindCSS**: Framework CSS utility-first
- **Vanilla JavaScript**: Sin frameworks, máximo rendimiento
- **Chart.js**: Gráficos interactivos
- **Vis.js**: Visualización de grafos de red
- **SweetAlert2**: Modales y alertas elegantes

#### Servicios
- **Speedtest-CLI**: Tests de velocidad
- **MacVendorLookup**: Identificación de fabricantes
- **SMTP/Telegram**: Notificaciones

### Flujo de Datos

```
┌─────────────────┐
│   Scapy ARP     │ ──> Escaneo cada 30s
│   Scanner       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Database      │ ──> SQLite (devices.db)
│   (SQLModel)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │ ──> API REST
│   Endpoints     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Frontend      │ ──> Actualización cada 1s
│   (JavaScript)  │
└─────────────────┘
```

---

## 🔌 API REST

### Endpoints Principales

#### Dispositivos

```http
GET /api/devices
```
Retorna lista completa de dispositivos detectados.

**Respuesta:**
```json
[
  {
    "id": 1,
    "mac": "aa:bb:cc:dd:ee:ff",
    "ip": "192.168.0.100",
    "vendor": "Apple Inc.",
    "alias": "iPhone de Juan",
    "status": "online",
    "is_trusted": true,
    "is_jailed": false,
    "is_blocked": false,
    "last_seen": "2026-02-11T13:30:00",
    "first_seen": "2026-02-10T08:00:00"
  }
]
```

```http
PUT /api/devices/{mac}/trust
```
Marca un dispositivo como confiable.

```http
POST /api/devices/{mac}/jail
```
Aísla un dispositivo temporalmente.

**Body:**
```json
{
  "duration_minutes": 60,
  "reason": "Consumo excesivo de ancho de banda"
}
```

#### Tráfico

```http
GET /api/traffic
```
Retorna estadísticas de tráfico en tiempo real.

**Respuesta:**
```json
{
  "aa:bb:cc:dd:ee:ff": {
    "down": 1048576,
    "up": 524288
  }
}
```

```http
GET /api/traffic/history/{mac}?period=24h
```
Historial de tráfico de un dispositivo.

**Períodos**: `24h`, `7d`, `30d`, `365d`, `all`

#### Speedtest

```http
GET /api/speedtest/history
```
Historial de tests de velocidad.

```http
POST /api/speedtest/run
```
Ejecuta un nuevo test de velocidad.

#### Topología

```http
GET /api/topology
```
Retorna la topología de red en formato Vis.js.

#### Seguridad

```http
GET /api/jailed_devices
```
Lista de dispositivos en jail.

```http
GET /api/blocked_devices
```
Lista de dispositivos bloqueados.

```http
GET /api/security/status
```
Estado general de seguridad.

**Ver documentación completa**: [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

---

## ⚙️ Configuración Avanzada

### Notificaciones por Email

Edita `backend/notifier.py`:

```python
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "tu-email@gmail.com"
SMTP_PASSWORD = "tu-contraseña-app"
EMAIL_TO = "destino@example.com"
```

### Notificaciones por Telegram

1. Crea un bot con [@BotFather](https://t.me/botfather)
2. Obtén tu Chat ID con [@userinfobot](https://t.me/userinfobot)
3. Configura en `backend/notifier.py`:

```python
TELEGRAM_BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
TELEGRAM_CHAT_ID = "123456789"
```

### Intervalo de Escaneo

En `backend/service.py`:

```python
# Cambiar de 30 a 60 segundos
await asyncio.sleep(60)
```

### Puerto del Servidor

En `main.py`:

```python
uvicorn.run(app, host="0.0.0.0", port=8080)  # Cambiar puerto
```

### Período de Gracia (Offline Detection)

En `backend/service.py`:

```python
GRACE_PERIOD = 300  # 5 minutos (en segundos)
```

---

## 🔧 Troubleshooting

### El servidor no inicia

**Error**: `Permission denied`

**Solución**: Ejecuta con `sudo`:
```bash
sudo ./startup.sh
```

---

### No detecta dispositivos

**Problema**: Lista de dispositivos vacía

**Soluciones**:
1. Verifica que estés ejecutando con `sudo`
2. Comprueba tu interfaz de red:
   ```bash
   ip addr show
   ```
3. Edita `backend/service.py` y especifica la interfaz:
   ```python
   scan_network(interface="eth0")  # o "wlan0"
   ```

---

### Dispositivos aparecen como offline

**Problema**: Dispositivos conectados aparecen offline

**Causa**: Algunos dispositivos (IoT, Alexa, etc.) no responden a ARP constantemente

**Solución**: Ajusta el `GRACE_PERIOD` en `backend/service.py`:
```python
GRACE_PERIOD = 600  # 10 minutos en lugar de 5
```

**Ver análisis completo**: [ANALISIS_OFFLINE_DEVICES.md](ANALISIS_OFFLINE_DEVICES.md)

---

### Velocidad en tiempo real muy baja

**Problema**: Dashboard muestra 0.01 Mbps

**Explicación**: Esto es **CORRECTO** si tu red está inactiva

**Verificación**: 
- Descarga un archivo grande
- Reproduce un video en YouTube
- Ejecuta un speedtest

La velocidad subirá automáticamente.

**Ver explicación completa**: [EXPLICACION_VELOCIDAD_REAL.md](EXPLICACION_VELOCIDAD_REAL.md)

---

### Error de base de datos

**Error**: `database is locked`

**Solución**:
```bash
# Detener el servidor
sudo pkill -f "python.*main.py"

# Eliminar archivo de lock
rm -f devices.db-journal

# Reiniciar
sudo ./startup.sh
```

---

### Notificaciones no funcionan

**Email**:
1. Verifica credenciales SMTP
2. Si usas Gmail, habilita "Aplicaciones menos seguras" o usa contraseña de aplicación
3. Revisa logs del servidor

**Telegram**:
1. Verifica el token del bot
2. Confirma el Chat ID
3. Prueba enviando un mensaje manual al bot

---

## 📊 Testing

El sistema incluye un plan de testing completo:

```bash
# Ver plan de testing
cat TESTING_PLAN.md

# Ver último reporte
cat TESTING_REPORT.md
```

**Último resultado**: ✅ **100% PASS** (432/432 tests)

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! 

### Cómo Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Guías de Estilo

- **Python**: Sigue PEP 8
- **JavaScript**: Usa ES6+
- **Commits**: Mensajes descriptivos en español o inglés

---

## 📝 Roadmap

### En Desarrollo
- [ ] Modo oscuro/claro toggle
- [ ] Exportación de reportes PDF
- [ ] Dashboard personalizable (drag & drop widgets)
- [ ] Soporte para múltiples interfaces de red

### Futuro
- [ ] Aplicación móvil (React Native)
- [ ] Detección de anomalías con ML
- [ ] Integración con Home Assistant
- [ ] Soporte para IPv6

---

## ⚠️ Nota Legal

Este software está diseñado para:
- ✅ Uso educativo y aprendizaje
- ✅ Monitoreo de redes propias
- ✅ Administración de redes autorizadas

**ADVERTENCIA**: El escaneo de redes ajenas sin autorización puede ser ilegal en tu jurisdicción. El desarrollador no se hace responsable del mal uso de esta herramienta.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 👨‍💻 Autor

**DragwayDt**

- GitHub: [@DragwayDt](https://github.com/DragwayDt)
- Email: contacto@dragwaydt.com

---

## 🙏 Agradecimientos

- [FastAPI](https://fastapi.tiangolo.com/) - Framework web increíble
- [Scapy](https://scapy.net/) - Manipulación de paquetes
- [TailwindCSS](https://tailwindcss.com/) - Framework CSS
- [Chart.js](https://www.chartjs.org/) - Gráficos hermosos
- [SweetAlert2](https://sweetalert2.github.io/) - Alertas elegantes

---

<div align="center">

**⭐ Si este proyecto te fue útil, considera darle una estrella ⭐**

Desarrollado con ❤️ y ☕ por DragwayDt

</div>
