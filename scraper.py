import re
import time
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import (
    URL_VISA_MAIN,
    URL_COUNTRY_CAPS,
    DEFAULT_HEADERS,
    REQUEST_TIMEOUT_SECONDS,
)

logger = logging.getLogger("Visa462Monitor.Scraper")


def get_requests_session():
    """
    Crea una sesión HTTP con política de reintentos automáticos
    para tolerar fallos puntuales de red o servidores gubernamentales.
    """
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_html(url: str, session: requests.Session) -> str:
    """
    Obtiene el contenido HTML de una URL con timeout y control de errores.
    """
    logger.debug(f"Consultando URL: {url}")
    response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.text


def parse_country_caps_status(html_content: str, country_name="spain"):
    """
    Analiza la página de estado de cupos (Status of country caps) y busca la fila
    correspondiente a España.
    
    Devuelve un tupla: (standardized_status, raw_status, annual_cap)
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Buscar tablas en la página
    tables = soup.find_all("table")
    
    raw_status = "No encontrado"
    annual_cap = "Desconocido"
    found = False

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all(["td", "th"])
            if not cols:
                continue
            
            # Limpiar texto del nombre del país (eliminar caracteres invisibles, espacios extras)
            first_col_text = cols[0].get_text(strip=True)
            first_col_clean = re.sub(r"[\u200b\u00a0]", "", first_col_text).strip()
            
            if country_name.lower() in first_col_clean.lower():
                found = True
                if len(cols) >= 2:
                    raw_status = re.sub(r"[\u200b\u00a0]", "", cols[1].get_text(strip=True)).strip()
                if len(cols) >= 3:
                    annual_cap = re.sub(r"[\u200b\u00a0]", "", cols[2].get_text(strip=True)).strip()
                break
        if found:
            break

    # Normalización del estado (OPEN, PAUSED, CLOSED)
    status_upper = raw_status.upper()
    if "OPEN" in status_upper or "ABIERTO" in status_upper or "AVAILABLE" in status_upper:
        standard_status = "OPEN"
    elif "PAUSE" in status_upper or "CAPPED" in status_upper or "SUSPEND" in status_upper or "PAUSADO" in status_upper:
        standard_status = "PAUSED"
    elif "CLOSE" in status_upper or "CERRADO" in status_upper:
        standard_status = "CLOSED"
    else:
        standard_status = "UNKNOWN"

    return standard_status, raw_status, annual_cap


def inspect_main_visa_page(html_content: str, country_name="spain") -> str:
    """
    Inspecciona la página principal de la visa 462 por si hay alertas destacadas
    o menciones especiales referidas a España.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    notes = []
    
    # Buscar banners o contenedores de alertas del encabezado
    alerts = soup.find_all("div", class_=re.compile(r"alert|warning|notice", re.I))
    for alert in alerts:
        text = alert.get_text(separator=" ", strip=True)
        if text and len(text) > 5 and len(text) < 300:
            notes.append(text)

    # Buscar referencias a Spain en párrafos destacados
    for p in soup.find_all("p"):
        p_text = p.get_text(strip=True)
        if country_name.lower() in p_text.lower() and ("cap" in p_text.lower() or "open" in p_text.lower() or "ballot" in p_text.lower()):
            if p_text not in notes:
                notes.append(p_text)

    return " | ".join(notes) if notes else "Sin notas adicionales en la página principal."


def scrape_spain_visa_status() -> dict:
    """
    Función principal de scraping:
    1. Consulta la página de cupos por país (Status of country caps) para España.
    2. Consulta la página principal de la visa 462.
    3. Retorna un diccionario estructurado con el estado actual.
    """
    session = get_requests_session()
    result = {
        "country": "Spain",
        "status": "UNKNOWN",
        "raw_status": "No consultado",
        "annual_cap": "Desconocido",
        "timestamp": datetime.now().isoformat(),
        "source_url": URL_COUNTRY_CAPS,
        "main_page_url": URL_VISA_MAIN,
        "notes": "",
        "success": False,
        "error": None,
    }

    try:
        # 1. Scraping de estado de cupos
        logger.info(f"Consultando página oficial de cupos: {URL_COUNTRY_CAPS}")
        html_caps = fetch_html(URL_COUNTRY_CAPS, session)
        standard_status, raw_status, annual_cap = parse_country_caps_status(html_caps, "Spain")
        
        # 2. Scraping complementario de página principal 462
        logger.info(f"Consultando página principal de la visa 462: {URL_VISA_MAIN}")
        html_main = fetch_html(URL_VISA_MAIN, session)
        notes = inspect_main_visa_page(html_main, "Spain")

        result.update({
            "status": standard_status,
            "raw_status": raw_status,
            "annual_cap": annual_cap,
            "notes": notes,
            "success": True,
        })
        logger.info(f"Resultado de scraping -> Estado: {standard_status} ({raw_status}), Cupo: {annual_cap}")

    except Exception as e:
        error_msg = f"Error durante el scraping web: {str(e)}"
        logger.error(error_msg, exc_info=True)
        result["error"] = error_msg
        result["success"] = False

    return result


if __name__ == "__main__":
    # Prueba rápida de scraping si se ejecuta el módulo directamente
    logging.basicConfig(level=logging.INFO)
    data = scrape_spain_visa_status()
    print("Resultado obtenido:", data)
