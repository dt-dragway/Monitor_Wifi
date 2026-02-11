# Monitor Wifi Profesional 📡

Un sistema avanzado de vigilancia y monitoreo de red local, diseñado con una interfaz moderna y funcionalidades premium para detectar dispositivos, identificar intrusos y gestionar la seguridad de tu Wifi.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Dashboard+Monitor+Wifi+Pro)

## 🚀 Características Premium

### 🎨 Interfaz Moderna (Glassmorphism)
- Diseño oscuro elegante con efectos de cristal y desenfoque.
- Animaciones suaves y transiciones fluidas.
- Iconos dinámicos que se adaptan al tipo de dispositivo (Windows, Apple, Android, SmartTV, Consolas, etc.).

### � Análisis de Tráfico en Tiempo Real
- **Monitor de Ancho de Banda:** Visualiza el consumo de subida y bajada de cada dispositivo en tiempo real (KB/MB).
- **Historial Detallado:** Gráficos interactivos de consumo por dispositivo (24h, 7 días, 30 días, 1 año).
- **Top Talkers:** Identifica rápidamente quién está consumiendo más ancho de banda en tu red.

### 🚀 Test de Velocidad Integrado
- Ejecuta pruebas de velocidad de internet (Ping, Bajada, Subida) directamente desde el dashboard.
- Guarda un historial de resultados para monitorear la calidad de tu conexión ISP.

### 🛡️ Seguridad Avanzada
- **Bloqueo de Intrusos:** Expulsa dispositivos no deseados de tu red mediante técnicas de desautenticación (requiere tarjeta compatible).
- **Escaneo de Vulnerabilidades:** Detecta puertos abiertos y servicios corriendo en los dispositivos conectados.
- **Alertas de Intruso:** Notificación visual inmediata y contadores de dispositivos desconocidos.

### 🗺️ Mapa de Red (Topología)
- Visualización gráfica de la red con nodos interactivos.
- Muestra la relación entre el gateway y los dispositivos conectados.

### 🎨 Experiencia de Usuario Premium
- **Persistencia de Vista:** El sistema recuerda en qué pestaña estabas (Mapa, Velocidad, Dispositivos) incluso si recargas la página.
- **Cero Saltos:** Actualización de datos en tiempo real sin recargar la página ni perder la posición de scroll.
- **Diseño Glassmorphism:** Interfaz oscura, moderna y responsiva.

## 🛠️ Instalación y Uso

### Prerequisitos
- Sistema operativo Linux (probado en Ubuntu/Debian/Mint).
- Python 3.10 o superior.
- Privilegios de administrador (`sudo`) para el escaneo de red ARP.

### Pasos
1.  **Clonar el repositorio** (o descargar los archivos):
    ```bash
    git clone https://github.com/tu-usuario/monitor-wifi-pro.git
    cd monitor-wifi-pro
    ```

2.  **Iniciar la aplicación**:
    El script `startup.sh` se encarga de todo: crear el entorno virtual, instalar dependencias y lanzar el servidor.
    ```bash
    sudo ./startup.sh
    ```
    *(La contraseña de sudo es necesaria para que `scapy` pueda enviar paquetes ARP a la red).*

3.  **Acceder al Dashboard**:
    Abre tu navegador web favorito y visita:
    👉 **http://localhost:8000**

## 🔧 Tecnologías Utilizadas

- **Backend:** Python, FastAPI, SQLModel (SQLite), Scapy.
- **Frontend:** HTML5, TailwindCSS (CDN), JavaScript (Vanilla), SweetAlert2.
- **Herramientas:** Uvicorn (Servidor ASGI), MacVendorLookup.

## ⚠️ Nota Legal y Responsabilidad
Este software está diseñado para uso educativo y personal en redes propias. El escaneo de redes ajenas sin autorización puede ser ilegal. El desarrollador no se hace responsable del mal uso de esta herramienta.

---
Desarrollado con ❤️ por DragwayDt
