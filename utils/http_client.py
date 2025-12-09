"""
HTTP Client con reintentos y timeout mejorado
"""

import requests
import time
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def request_with_retry(
    url: str,
    params: Dict[str, Any],
    timeout: int = 45,
    max_retries: int = 2,
    retry_delay: float = 2.0
) -> Optional[Dict]:
    """
    Hace una petición GET con reintentos automáticos para timeouts.
    
    Args:
        url: URL de la API
        params: Parámetros de la petición
        timeout: Timeout en segundos
        max_retries: Número máximo de reintentos
        retry_delay: Segundos entre reintentos
    
    Returns:
        Dict con la respuesta JSON o None si falla
    """
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(f"Timeout en intento {attempt + 1}, reintentando en {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Timeout después de {max_retries + 1} intentos")
                
        except requests.exceptions.RequestException as e:
            last_error = e
            logger.error(f"Error en request: {e}")
            break
    
    return None


def safe_request(
    url: str,
    params: Dict[str, Any],
    timeout: int = 45,
    max_retries: int = 2,
    default: Optional[Dict] = None
) -> Dict:
    """
    Versión safe que siempre retorna un dict (nunca None).
    
    Args:
        url: URL de la API
        params: Parámetros de la petición
        timeout: Timeout en segundos
        max_retries: Número máximo de reintentos
        default: Valor por defecto si falla
    
    Returns:
        Dict con la respuesta o el default
    """
    result = request_with_retry(url, params, timeout, max_retries)
    
    if result is not None:
        return result
    
    return default if default is not None else {}
