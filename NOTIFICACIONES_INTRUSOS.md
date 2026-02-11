# 🔔 Sistema de Notificaciones de Intrusos

**Fecha de Implementación**: 2026-02-11  
**Estado**: ✅ Activo

---

## 📋 Descripción

El sistema ahora incluye **notificaciones automáticas de escritorio** cuando se detecta un intruso (dispositivo no confiable) conectándose a tu red WiFi.

---

## 🚀 Características

### ✅ Notificaciones Automáticas

El sistema envía notificaciones en los siguientes casos:

1. **Nuevo Intruso Detectado**
   - Cuando un dispositivo desconocido se conecta por primera vez
   - El dispositivo NO está marcado como confiable

2. **Intruso Reconectado**
   - Cuando un dispositivo no confiable que estaba offline se reconecta
   - Útil para detectar dispositivos que se conectan intermitentemente

### 🎨 Tipos de Notificación

#### 1️⃣ **Notificación de Escritorio (Linux)**
- **Tecnología**: `notify-send` (libnotify)
- **Urgencia**: Crítica (máxima prioridad)
- **Icono**: `security-high` (escudo de seguridad)
- **Título**: 🚨 INTRUSO DETECTADO
- **Contenido**:
  ```
  Nombre del Dispositivo
  IP: 192.168.0.123
  MAC: aa:bb:cc:dd:ee:ff
  ```

#### 2️⃣ **Webhook (Opcional)**
- Discord, Slack, Telegram, etc.
- Se envía si está configurado en la base de datos
- Formato enriquecido con embeds (Discord)

---

## 🔧 Requisitos

### Sistema Operativo
- ✅ **Linux** con entorno gráfico (GNOME, KDE, XFCE, etc.)
- ✅ `notify-send` instalado (viene por defecto en la mayoría de distribuciones)

### Verificar Instalación
```bash
which notify-send
```

Si no está instalado:
```bash
sudo apt install libnotify-bin
```

---

## 🧪 Pruebas

### Prueba Manual de Notificaciones

Ejecuta el script de prueba:
```bash
./test_notifications.sh
```

Deberías ver **3 notificaciones** en tu escritorio:
1. Notificación básica (normal)
2. Alerta de seguridad (crítica)
3. Intruso detectado (crítica)

### Prueba Real con Dispositivo

1. **Conecta un dispositivo nuevo** a tu red WiFi
2. **Espera hasta 30 segundos** (tiempo de escaneo)
3. **Verás una notificación** si el dispositivo no está marcado como confiable

---

## 📊 Flujo de Detección

```
┌─────────────────────┐
│  Escaneo ARP        │  (cada 30 segundos)
│  (scan_network)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  ¿Dispositivo       │
│  nuevo o            │
│  reconectado?       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  ¿Es confiable?     │
│  (is_trusted)       │
└──────────┬──────────┘
           │
           ├─ SÍ ──→ No notificar
           │
           └─ NO ──→ 🚨 NOTIFICAR
                     │
                     ├─→ Notificación de Escritorio
                     └─→ Webhook (si configurado)
```

---

## 🔍 Detalles Técnicos

### Archivos Modificados

#### 1. `backend/notifier.py`
**Funciones Agregadas**:

- `send_desktop_notification(title, message, urgency, icon)`
  - Envía notificaciones usando `notify-send`
  - Maneja ejecución con `sudo` (detecta `SUDO_USER`)
  - Configura `DISPLAY` correctamente

- `notify_intruder(device_info)`
  - Función especializada para notificar intrusos
  - Formatea el mensaje con información del dispositivo
  - Llama a `send_desktop_notification` + `send_notification` (webhook)

#### 2. `backend/service.py`
**Modificaciones**:

- **Línea ~115**: Notificación para **nuevos dispositivos** no confiables
  ```python
  if not is_trusted:
      from .notifier import notify_intruder
      notify_intruder({...})
  ```

- **Línea ~100**: Notificación para **intrusos reconectados**
  ```python
  if was_offline and is_intruder:
      from .notifier import notify_intruder
      notify_intruder({...})
  ```

---

## ⚙️ Configuración

### Nivel de Urgencia

En `backend/notifier.py`, puedes cambiar la urgencia:
```python
send_desktop_notification(
    title=title,
    message=message,
    urgency="critical",  # Opciones: low, normal, critical
    icon="security-high"
)
```

### Iconos Disponibles

Puedes usar cualquier icono del sistema:
- `security-high` - Escudo de seguridad (por defecto)
- `dialog-warning` - Advertencia
- `network-wireless` - WiFi
- `dialog-error` - Error
- `emblem-important` - Importante

### Desactivar Notificaciones

Si quieres desactivar las notificaciones temporalmente:

**Opción 1**: Comentar las líneas en `service.py`
```python
# if not is_trusted:
#     from .notifier import notify_intruder
#     notify_intruder({...})
```

**Opción 2**: Modificar `notify_intruder` para que no haga nada
```python
def notify_intruder(device_info: dict):
    return  # Desactivado
```

---

## 🐛 Troubleshooting

### No veo las notificaciones

**Problema**: Las notificaciones no aparecen en el escritorio

**Soluciones**:

1. **Verifica que estés en un entorno gráfico**
   ```bash
   echo $DISPLAY
   # Debería mostrar algo como: :0 o :1
   ```

2. **Verifica que notify-send funcione**
   ```bash
   notify-send "Prueba" "Hola mundo"
   ```

3. **Si ejecutas con sudo**, verifica que `SUDO_USER` esté configurado
   ```bash
   echo $SUDO_USER
   # Debería mostrar tu nombre de usuario
   ```

4. **Revisa los logs del servidor**
   ```bash
   # En la terminal donde corre startup.sh
   # Busca mensajes como:
   # ✅ Notificación enviada: ...
   ```

### Las notificaciones aparecen pero no tienen sonido

**Solución**: Configura el sonido en las preferencias del sistema
- GNOME: Configuración → Notificaciones → Sonidos
- KDE: Configuración del Sistema → Notificaciones → Sonidos

### Error: "notify-send not found"

**Solución**: Instala libnotify
```bash
sudo apt install libnotify-bin
```

---

## 📈 Próximas Mejoras

- [ ] Notificaciones por email (SMTP)
- [ ] Notificaciones por Telegram
- [ ] Historial de notificaciones en el dashboard
- [ ] Configuración de notificaciones desde la UI
- [ ] Filtros personalizados (notificar solo ciertos vendors)
- [ ] Sonidos personalizados por tipo de alerta

---

## 📝 Ejemplo de Uso

### Escenario Real

1. **Situación**: Estás trabajando en tu computadora
2. **Evento**: Un vecino intenta conectarse a tu WiFi
3. **Detección**: El sistema detecta el nuevo dispositivo en 30 segundos
4. **Notificación**: Aparece una alerta en tu escritorio:

   ```
   🚨 INTRUSO DETECTADO
   
   Samsung Galaxy S21
   IP: 192.168.0.156
   MAC: 12:34:56:78:9a:bc
   ```

5. **Acción**: Abres el dashboard y:
   - Ves el dispositivo en la lista
   - Lo bloqueas o lo pones en Jail
   - O lo marcas como confiable si es legítimo

---

## ✅ Conclusión

El sistema de notificaciones de intrusos está **completamente funcional** y se ejecuta automáticamente en segundo plano. No requiere configuración adicional y funciona inmediatamente después de iniciar el servidor con `sudo ./startup.sh`.

**Beneficios**:
- ✅ Detección instantánea de intrusos
- ✅ Notificaciones no intrusivas
- ✅ Funciona en segundo plano
- ✅ Sin configuración necesaria
- ✅ Compatible con todos los entornos de escritorio Linux

---

**Desarrollado por**: DragwayDt  
**Versión**: 1.0  
**Última actualización**: 2026-02-11
