import json
import logging
from pathlib import Path
from datetime import datetime

from config import STATE_FILE_PATH

logger = logging.getLogger("Visa462Monitor.StateManager")


def get_initial_state() -> dict:
    """
    Retorna la estructura inicial de estado cuando no existe un historial previo.
    """
    return {
        "country": "Spain",
        "status": "NONE",
        "raw_status": "Sin datos previos",
        "annual_cap": "Desconocido",
        "last_checked": "",
        "last_changed": "",
        "notes": "",
        "check_count": 0,
    }


def load_state(path: Path = STATE_FILE_PATH) -> dict:
    """
    Carga el archivo local de estado visa_status.json.
    Si el archivo no existe o está dañado, devuelve un estado inicial.
    """
    if not path.exists():
        logger.info(f"No existe archivo de estado en {path}. Se creará en la primera comprobación.")
        return get_initial_state()
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.debug("Estado cargado exitosamente.")
            return data
    except Exception as e:
        logger.warning(f"No se pudo leer {path} ({e}). Inicializando nuevo estado.")
        return get_initial_state()


def save_state(state: dict, path: Path = STATE_FILE_PATH) -> bool:
    """
    Guarda el estado actual en visa_status.json con formato legible.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        logger.debug(f"Estado persistido correctamente en {path}")
        return True
    except Exception as e:
        logger.error(f"Error al guardar estado en {path}: {e}", exc_info=True)
        return False


def analyze_changes(prev_state: dict, curr_scrape: dict) -> dict:
    """
    Compara el estado previamente guardado con el resultado recién obtenido en la web.
    
    Determina si ha ocurrido:
    - Cambio de estado principal (ej. PAUSED -> OPEN, CLOSED -> OPEN)
    - Apertura de la visa (is_now_open)
    - Cambio en el cupo anual asignado
    - Cambio en notas adicionales
    """
    old_status = prev_state.get("status", "NONE")
    new_status = curr_scrape.get("status", "UNKNOWN")

    old_cap = prev_state.get("annual_cap", "Desconocido")
    new_cap = curr_scrape.get("annual_cap", "Desconocido")

    old_notes = prev_state.get("notes", "")
    new_notes = curr_scrape.get("notes", "")

    is_first_run = (old_status == "NONE")
    status_changed = (old_status != new_status) and not is_first_run
    cap_changed = (old_cap != new_cap) and not is_first_run and (new_cap != "Desconocido")
    notes_changed = (old_notes != new_notes) and not is_first_run and bool(new_notes)

    # Considerar como cambio si cambió el estado principal o el cupo
    has_changed = status_changed or cap_changed

    # Detectar explícitamente si ahora la visa está ABIERTA
    is_now_open = (new_status == "OPEN")

    if is_first_run:
        summary = f"Primera comprobación registrada: {new_status} ({curr_scrape.get('raw_status')})"
    elif status_changed:
        summary = f"¡CAMBIO DE ESTADO DETECTADO! De '{old_status}' a '{new_status}' ({curr_scrape.get('raw_status')})"
    elif cap_changed:
        summary = f"Cambio de cupo anual detectado: de {old_cap} a {new_cap}"
    else:
        summary = f"Sin cambios en el estado de la visa ({new_status} - {curr_scrape.get('raw_status')})"

    return {
        "has_changed": has_changed,
        "is_first_run": is_first_run,
        "is_now_open": is_now_open,
        "status_changed": status_changed,
        "old_status": old_status,
        "new_status": new_status,
        "cap_changed": cap_changed,
        "old_cap": old_cap,
        "new_cap": new_cap,
        "notes_changed": notes_changed,
        "old_notes": old_notes,
        "new_notes": new_notes,
        "summary": summary,
    }


def create_updated_state(prev_state: dict, curr_scrape: dict, analysis: dict) -> dict:
    """
    Construye el nuevo objeto de estado para guardar en JSON.
    Actualiza la fecha de último cambio únicamente cuando cambió el estado.
    """
    now_iso = datetime.now().isoformat()
    last_changed = prev_state.get("last_changed", now_iso)

    if analysis["status_changed"] or analysis["is_first_run"]:
        last_changed = now_iso

    check_count = prev_state.get("check_count", 0) + 1

    return {
        "country": curr_scrape.get("country", "Spain"),
        "status": curr_scrape.get("status", "UNKNOWN"),
        "raw_status": curr_scrape.get("raw_status", "No disponible"),
        "annual_cap": curr_scrape.get("annual_cap", "Desconocido"),
        "last_checked": now_iso,
        "last_changed": last_changed,
        "notes": curr_scrape.get("notes", ""),
        "check_count": check_count,
    }
