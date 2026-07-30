import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

from config import (
    EMAIL_ENABLED,
    EMAIL_TO,
    EMAIL_FROM,
    EMAIL_SMTP_SERVER,
    EMAIL_SMTP_PORT,
    EMAIL_SMTP_USER,
    EMAIL_SMTP_PASSWORD,
    TELEGRAM_ENABLED,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    DISCORD_ENABLED,
    DISCORD_WEBHOOK_URL,
    URL_VISA_MAIN,
    URL_COUNTRY_CAPS,
    REQUEST_TIMEOUT_SECONDS,
)

logger = logging.getLogger("Visa462Monitor.Notifier")


def send_email_alert(subject: str, html_body: str, to_email: str = EMAIL_TO) -> bool:
    """
    Envía un correo electrónico urgente (alta prioridad) mediante servidor SMTP.
    Ideal para notificar apertura directamente a maverick6576@gmail.com.
    """
    if not EMAIL_ENABLED:
        logger.debug("Envío por Email deshabilitado en configuración.")
        return False

    if not EMAIL_SMTP_USER or not EMAIL_SMTP_PASSWORD:
        logger.warning(
            f"No se han configurado credenciales SMTP (EMAIL_SMTP_USER / EMAIL_SMTP_PASSWORD) en .env. "
            f"No se pudo enviar correo a {to_email}."
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM or EMAIL_SMTP_USER
        msg["To"] = to_email
        
        # Cabeceras de alta prioridad / importancia
        msg["X-Priority"] = "1 (Highest)"
        msg["X-MSMail-Priority"] = "High"
        msg["Importance"] = "High"

        part = MIMEText(html_body, "html", "utf-8")
        msg.attach(part)

        logger.info(f"Conectando al servidor SMTP {EMAIL_SMTP_SERVER}:{EMAIL_SMTP_PORT} para enviar correo a {to_email}...")
        with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT, timeout=REQUEST_TIMEOUT_SECONDS) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD)
            server.sendmail(msg["From"], [to_email], msg.as_string())

        logger.info(f"¡Correo urgente enviado exitosamente a {to_email}!")
        return True

    except Exception as e:
        logger.error(f"Error al enviar correo SMTP a {to_email}: {e}", exc_info=True)
        return False


def send_telegram_alert(message_html: str) -> bool:
    """
    Envía un mensaje formateado a un chat/canal de Telegram mediante Bot API.
    """
    if not TELEGRAM_ENABLED:
        logger.debug("Envío por Telegram deshabilitado en configuración.")
        return False

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en .env.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        logger.info(f"Enviando alerta a Telegram (Chat ID: {TELEGRAM_CHAT_ID})...")
        res = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        res.raise_for_status()
        logger.info("¡Alerta de Telegram enviada exitosamente!")
        return True
    except Exception as e:
        logger.error(f"Error al enviar mensaje a Telegram: {e}", exc_info=True)
        return False


def send_discord_webhook(title: str, description: str, color: int, fields: list = None) -> bool:
    """
    Envía una tarjeta embed enriquecida a un canal de Discord mediante Webhook.
    """
    if not DISCORD_ENABLED:
        logger.debug("Envío por Discord deshabilitado en configuración.")
        return False

    if not DISCORD_WEBHOOK_URL:
        logger.warning("Falta DISCORD_WEBHOOK_URL en .env.")
        return False

    embed = {
        "title": title,
        "description": description,
        "color": color,
        "url": URL_VISA_MAIN,
        "fields": fields or [],
        "footer": {"text": "Agente de Monitoreo Australia Work and Holiday 462"},
    }

    payload = {
        "username": "Australia Visa 462 Monitor",
        "embeds": [embed],
    }

    try:
        logger.info("Enviando alerta a Discord Webhook...")
        res = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        res.raise_for_status()
        logger.info("¡Alerta de Discord enviada exitosamente!")
        return True
    except Exception as e:
        logger.error(f"Error al enviar webhook de Discord: {e}", exc_info=True)
        return False


def notify_all_channels(analysis: dict, curr_scrape: dict, force_alert: bool = False) -> dict:
    """
    Compondrá y enviará las alertas por todos los canales habilitados
    cuando se detecta una apertura de la visa o un cambio importante.
    """
    status = curr_scrape.get("status", "UNKNOWN")
    raw_status = curr_scrape.get("raw_status", "N/D")
    cap = curr_scrape.get("annual_cap", "3,400")
    notes = curr_scrape.get("notes", "Sin notas")
    timestamp = curr_scrape.get("timestamp", "")
    country = curr_scrape.get("country", "Spain")

    is_open = (status == "OPEN") or force_alert

    # Colores para Discord (Hex en entero)
    color_map = {
        "OPEN": 0x2ECC71,    # Verde brillante
        "PAUSED": 0xF1C40F,  # Amarillo
        "CLOSED": 0xE74C3C,  # Rojo
        "UNKNOWN": 0x95A5A6, # Gris
    }
    discord_color = color_map.get(status, 0x3498DB)
    if is_open:
        discord_color = 0x2ECC71

    # Construcción de encabezados y títulos
    if is_open:
        title = f"🚨 ¡URGENTE: VISA WORK AND HOLIDAY 462 ABIERTA PARA ESPAÑA! 🚨"
        action_text = "¡El proceso de solicitud está DISPONIBLE! Entra inmediatamente a aplicar."
    else:
        title = f"🔔 Cambio de estado detectado - Visa 462 Australia ({country})"
        action_text = f"El estado ha cambiado a: {status} ({raw_status})."

    # --- 1. Formato de Correo Electrónico (HTML) ---
    email_subject = title
    email_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; border: 2px solid {'#2ecc71' if is_open else '#3498db'}; border-radius: 8px; padding: 20px; background-color: #f9fdfa;">
            <h2 style="color: {'#27ae60' if is_open else '#2980b9'}; text-align: center;">{title}</h2>
            <p style="font-size: 16px; font-weight: bold;">{action_text}</p>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>País:</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{country}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>Estado Oficial:</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd;"><span style="color: {'#27ae60' if is_open else '#e67e22'}; font-weight: bold;">{status}</span> ({raw_status})</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>Cupo Anual:</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{cap}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>Última Comprobación:</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{timestamp}</td>
                </tr>
            </table>
            <p><b>Notas oficiales:</b><br>{notes}</p>
            <div style="text-align: center; margin-top: 25px;">
                <a href="{URL_VISA_MAIN}" style="background-color: #27ae60; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">¡ENTRAR A APLICAR AHORA!</a>
            </div>
            <p style="font-size: 12px; color: #777; margin-top: 30px; text-align: center;">
                Enlaces oficiales:<br>
                <a href="{URL_VISA_MAIN}">First Work and Holiday Visa (Subclass 462)</a> |
                <a href="{URL_COUNTRY_CAPS}">Status of Country Caps</a>
            </p>
        </div>
    </body>
    </html>
    """

    # --- 2. Formato de Telegram (HTML) ---
    telegram_html = (
        f"<b>{title}</b>\n\n"
        f"🇪🇸 <b>País:</b> {country}\n"
        f"📌 <b>Estado:</b> <code>{status}</code> (<i>{raw_status}</i>)\n"
        f"📊 <b>Cupo Anual:</b> {cap}\n"
        f"⏰ <b>Hora:</b> {timestamp}\n\n"
        f"💬 <b>Notas:</b> {notes}\n\n"
        f"⚡️ <b>{action_text}</b>\n\n"
        f"🔗 <a href=\"{URL_VISA_MAIN}\">Aplicar en la página oficial (462)</a>\n"
        f"🔗 <a href=\"{URL_COUNTRY_CAPS}\">Ver tabla de cupos por país</a>"
    )

    # --- 3. Formato de Discord (Embed fields) ---
    discord_fields = [
        {"name": "Estado Oficial", "value": f"**{status}** ({raw_status})", "inline": True},
        {"name": "Cupo Anual", "value": str(cap), "inline": True},
        {"name": "Hora de Comprobación", "value": str(timestamp), "inline": False},
        {"name": "Notas", "value": str(notes)[:1000] or "Sin notas adicionales", "inline": False},
        {"name": "Enlace Directo", "value": f"[Aplicar Ahora (Subclass 462)]({URL_VISA_MAIN})", "inline": False},
    ]

    results = {
        "email": send_email_alert(email_subject, email_html, EMAIL_TO),
        "telegram": send_telegram_alert(telegram_html),
        "discord": send_discord_webhook(title, action_text, discord_color, discord_fields),
    }

    return results


def send_test_notification() -> dict:
    """
    Envía una notificación de prueba por todos los canales habilitados
    para comprobar que tokens, correos y webhooks están configurados correctamente.
    """
    fake_scrape = {
        "country": "Spain",
        "status": "OPEN",
        "raw_status": "Open (PRUEBA DE CONFIGURACIÓN)",
        "annual_cap": "3,400",
        "notes": "Esta es una alerta de PRUEBA enviada desde el CLI para confirmar la correcta recepción de alertas del agente.",
        "timestamp": "PRUEBA - AHORA",
    }
    logger.info("Iniciando prueba de envío de notificaciones por Email, Telegram y Discord...")
    return notify_all_channels({"is_now_open": True}, fake_scrape, force_alert=True)
