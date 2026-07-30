import time
import argparse
import logging
from datetime import datetime
import schedule
from colorama import init, Fore, Style

import config
from scraper import scrape_spain_visa_status
from state_manager import load_state, save_state, analyze_changes, create_updated_state
from notifier import notify_all_channels, send_test_notification

# Inicializar colorama para soporte de colores en consola Windows
init(autoreset=True)

# Configurar sistema de logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Visa462Monitor.Main")


def print_banner(scrape_result: dict, analysis: dict):
    """
    Muestra en consola un cuadro resumen formateado con el estado actual de la visa.
    """
    status = scrape_result.get("status", "UNKNOWN")
    raw = scrape_result.get("raw_status", "N/D")
    cap = scrape_result.get("annual_cap", "Desconocido")
    timestamp = scrape_result.get("timestamp", datetime.now().isoformat())

    color = Fore.CYAN
    if status == "OPEN":
        color = Fore.GREEN + Style.BRIGHT
    elif status == "PAUSED":
        color = Fore.YELLOW + Style.BRIGHT
    elif status == "CLOSED":
        color = Fore.RED + Style.BRIGHT

    print("\n" + "=" * 70)
    print(color + "  AGENTE DE MONITOREO - VISA WORK AND HOLIDAY (SUBCLASS 462) AUSTRALIA")
    print("=" * 70)
    print(f"  País Monitorizado : {Style.BRIGHT}ESPAÑA (Spain){Style.RESET_ALL}")
    print(f"  Estado Oficial    : {color}{status} ({raw}){Style.RESET_ALL}")
    print(f"  Cupo Anual Asignado: {Style.BRIGHT}{cap}{Style.RESET_ALL}")
    print(f"  Fecha Comprobación: {timestamp}")
    print(f"  Resumen Cambios   : {analysis.get('summary', '')}")
    print("=" * 70 + "\n")


def run_single_check(force_alert: bool = False):
    """
    Ejecuta un ciclo completo de monitoreo:
    1. Carga el estado guardado anterior.
    2. Realiza scraping en vivo en las webs de Inmigración de Australia.
    3. Compara resultados y detecta apertura o cambios.
    4. Envía alertas por correo/Telegram/Discord si corresponde.
    5. Guarda el nuevo estado en visa_status.json.
    """
    logger.info("Iniciando comprobación del estado de la visa 462 para España...")
    
    # 1. Cargar estado anterior
    prev_state = load_state()

    # 2. Obtener datos de la web oficial
    curr_scrape = scrape_spain_visa_status()
    if not curr_scrape.get("success"):
        logger.error(f"Fallo al consultar la web oficial: {curr_scrape.get('error')}")
        return curr_scrape

    # 3. Analizar diferencias
    analysis = analyze_changes(prev_state, curr_scrape)
    print_banner(curr_scrape, analysis)

    # 4. Decidir si se debe enviar alerta prioritaria
    should_notify = (
        force_alert
        or analysis["is_now_open"]
        or (analysis["status_changed"] and not analysis["is_first_run"])
        or (analysis["is_first_run"] and config.NOTIFY_ON_FIRST_RUN)
    )

    if should_notify:
        reason = "ALERTA FORZADA" if force_alert else ("¡VISA ABIERTA!" if analysis["is_now_open"] else "CAMBIO DE ESTADO")
        logger.info(f"⚡ Disparando notificaciones urgentes ({reason})...")
        notify_all_channels(analysis, curr_scrape, force_alert=force_alert)
    else:
        logger.info("No se requieren notificaciones en este ciclo (sin cambios relevantes en el estado).")

    # 5. Guardar estado actualizado
    new_state = create_updated_state(prev_state, curr_scrape, analysis)
    save_state(new_state)
    logger.info("Ciclo de comprobación completado y estado persistido con éxito.\n")
    return curr_scrape


def run_daemon_mode():
    """
    Ejecuta el agente de forma continua en primer plano comprobando
    cada CHECK_INTERVAL_MINUTES minutos (alternativa al Task Scheduler).
    """
    interval = config.CHECK_INTERVAL_MINUTES
    logger.info(f"Iniciando modo demonio (Daemon). Se verificará cada {interval} minuto(s)...")
    
    # Ejecutar una primera comprobación al iniciar
    run_single_check()

    # Programar las siguientes ejecuciones
    schedule.every(interval).minutes.do(run_single_check)

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Modo demonio detenido por el usuario (Ctrl+C).")


def show_saved_status():
    """
    Muestra el estado actualmente guardado en visa_status.json sin conectar a internet.
    """
    state = load_state()
    print("\n" + "-" * 60)
    print("  ESTADO GUARDADO EN ARCHIVO LOCAL (visa_status.json)")
    print("-" * 60)
    for k, v in state.items():
        print(f"  {k:<15}: {v}")
    print("-" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Agente Automático de Monitoreo de Visa Work and Holiday 462 (Australia - España)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Ejecuta una comprobación puntual de estado y sale (ideal para Task Scheduler/Cron).",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Ejecuta en modo demonio continuo verificando cada N minutos (CHECK_INTERVAL_MINUTES).",
    )
    parser.add_argument(
        "--test-alert",
        action="store_true",
        help="Envía una alerta de prueba a Correo, Telegram y Discord para verificar configuración.",
    )
    parser.add_argument(
        "--force-alert",
        action="store_true",
        help="Ejecuta una comprobación real pero fuerza el envío de la alerta urgente como si estuviera ABIERTO.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Muestra el estado guardado actualmente en el archivo local visa_status.json.",
    )

    args = parser.parse_args()

    if args.daemon:
        run_daemon_mode()
    elif args.test_alert:
        send_test_notification()
    elif args.force_alert:
        run_single_check(force_alert=True)
    elif args.status:
        show_saved_status()
    else:
        # Modo por defecto: ejecutar una única comprobación
        run_single_check()


if __name__ == "__main__":
    main()
