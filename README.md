# 🇦🇺 Agente Automático de Monitoreo: Visa Work and Holiday (Subclass 462) Australia - España

Este proyecto es un agente autónomo de monitoreo en **Python** diseñado para comprobar periódicamente la página oficial del Gobierno de Australia y alertar **inmediatamente** cuando la visa **Work and Holiday (Subclass 462)** para ciudadanos de **España (Spain)** pase a estar **ABIERTA (`open`)** o cuando ocurran cambios de estado relevantes.

---

## 🌟 Características Principales

1. **Scraping Inteligente y Resiliente (`scraper.py`)**:
   - Inspecciona dos páginas oficiales del Departamento de Home Affairs de Australia:
     - [First Work and Holiday visa (subclass 462)](https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing/work-holiday-462/first-work-holiday-462)
     - [Status of country caps](https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps)
   - Extrae de forma automática el estado de **España (`Spain`)** (`OPEN`, `PAUSED`, `CLOSED`, `CAPPED`) y el cupo anual oficial (`3,400`).
   - Incluye cabeceras de navegador y política de reintentos con *exponential backoff* para evitar fallos de conexión.

2. **Gestión de Estado Persistente (`state_manager.py`)**:
   - Guarda el historial de cada comprobación en `visa_status.json`.
   - Compara el estado anterior y el actual para **evitar notificaciones repetidas**.
   - Identifica cuándo se abre el cupo (`is_now_open`), cambios en la cuota o notas oficiales nuevas.

3. **Notificaciones Multi-Canal (`notifier.py`)**:
   - **Correo Electrónico Urgente (SMTP)**: Envía correos con formato HTML y cabeceras de prioridad máxima (configurado por defecto para `maverick6576@gmail.com`).
   - **Telegram Bot API**: Envía alertas con formato HTML y botones/enlaces directos.
   - **Discord Webhook**: Envía tarjetas (*Rich Embeds*) con colores de alerta (Verde para abierto, Amarillo para pausado, Rojo para cerrado).

4. **Programación Automática Cada 15 Minutos**:
   - Compatible con **Programador de Tareas de Windows (Task Scheduler)** mediante scripts automáticos (`setup_scheduled_task.ps1` y `run_monitor.bat`).
   - Compatible con **Modo Demonio (`--daemon`)** y con crontabs en Linux/macOS.

---

## 🚀 Instalación y Configuración Paso a Paso

### 1. Requisitos Previos y Dependencias
Asegúrate de tener Python 3.10+ instalado. Abre la consola en el directorio `australia_462_visa_monitor/` e instala las librerías necesarias:
```bash
pip install -r requirements.txt
```

### 2. Configuración de Variables de Entorno (`.env`)
Copia el archivo de plantilla `.env.example` a un archivo `.env` en la misma carpeta:
```bash
copy .env.example .env
```
Edita el archivo `.env` con tus credenciales:

- **Para Correo Electrónico (Gmail)**:
  - `EMAIL_ENABLED=true`
  - `EMAIL_TO=maverick6576@gmail.com`
  - `EMAIL_SMTP_USER=tu_correo@gmail.com`
  - `EMAIL_SMTP_PASSWORD=tu_app_password_de_16_letras`
  > *Nota sobre Gmail*: Debes generar una **Contraseña de aplicación (App Password)** en la configuración de tu cuenta de Google (Seguridad -> Verificación en 2 pasos -> Contraseñas de aplicaciones). No uses tu contraseña normal de Google.

- **Para Telegram**:
  - Habla con [@BotFather](https://t.me/BotFather) en Telegram para crear un bot y obtener el token: `TELEGRAM_BOT_TOKEN`.
  - Habla con [@userinfobot](https://t.me/userinfobot) para obtener tu ID numérico: `TELEGRAM_CHAT_ID`.
  - Configura `TELEGRAM_ENABLED=true`.

- **Para Discord**:
  - En tu servidor de Discord: Configuración de canal -> Integraciones -> Crear Webhook -> Copiar URL del webhook.
  - Configura `DISCORD_ENABLED=true` y pega la URL en `DISCORD_WEBHOOK_URL`.

---

## 🛠️ Modos de Uso del CLI (`main.py`)

El agente cuenta con comandos limpios desde la terminal:

```bash
# 1. Comprobación puntual y actualización de estado (ideal para Cron/Scheduler)
python main.py --check

# 2. Ver el estado local actualmente guardado en visa_status.json
python main.py --status

# 3. Probar el envío de notificaciones (Correo, Telegram, Discord)
python main.py --test-alert

# 4. Forzar una alerta urgente simulando apertura de visa (para probar diseño del correo)
python main.py --force-alert

# 5. Ejecutar en segundo plano de forma continua (Modo Demonio cada 15 min)
python main.py --daemon
```

---

## ⏰ Programación Automática (Cada 15 Minutos)

### A. Tarea Programada en Windows (Recomendado)
Hemos creado un script en PowerShell para registrar la tarea programada en Windows sin esfuerzo:

1. Abre **PowerShell** en la carpeta `australia_462_visa_monitor/`.
2. Ejecuta el comando de configuración:
   ```powershell
   .\setup_scheduled_task.ps1
   ```
3. ¡Listo! Se habrá creado una tarea llamada `AustraliaVisa462Monitor_Spain` que se ejecutará cada 15 minutos indefinidamente y guardará su registro en `monitor.log`.
   - Puedes abrir `taskschd.msc` (Programador de tareas) en Windows en cualquier momento para ver o deshabilitar la tarea.

### B. Modo Crontab en Linux/macOS
Si vas a ejecutar este agente en un servidor Linux o Raspberry Pi:
```bash
# Editar crontab
crontab -e

# Añadir la línea para ejecución cada 15 minutos
*/15 * * * * cd /ruta/al/proyecto/australia_462_visa_monitor && /usr/bin/python3 main.py --check >> monitor.log 2>&1
```

---

## 📁 Estructura del Directorio

```text
australia_462_visa_monitor/
│
├── config.py                   # Gestión centralizada de URLs y variables de entorno
├── scraper.py                  # Scraping dual (status-of-country-caps & visa 462)
├── state_manager.py            # Lectura/escritura de visa_status.json y análisis de cambios
├── notifier.py                 # Envío de alertas por Email (SMTP), Telegram y Discord
├── main.py                     # Punto de entrada y CLI (--check, --daemon, --test-alert...)
├── run_monitor.bat             # Script para Programador de Tareas de Windows
├── setup_scheduled_task.ps1    # Instalador automático de tarea programada Windows
├── requirements.txt            # Dependencias de Python
├── .env.example                # Plantilla de variables de entorno (.env)
└── README.md                   # Este manual
```
