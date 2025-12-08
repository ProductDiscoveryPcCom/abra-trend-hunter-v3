"""
Safe Operations Module
Operaciones seguras que nunca fallan - fallbacks y contingencias

Este módulo proporciona funciones que garantizan que la aplicación
no crashee por valores None, cero, listas vacías, etc.
"""

from typing import Any, Dict, List, Optional, Union, Callable
from numbers import Number


# =============================================================================
# DIVISIONES SEGURAS
# =============================================================================

def safe_divide(
    numerator: Any, 
    denominator: Any, 
    default: float = 0.0
) -> float:
    """
    División segura que nunca falla
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor por defecto si no se puede dividir
        
    Returns:
        Resultado de la división o default
    """
    try:
        num = float(numerator) if numerator is not None else 0
        den = float(denominator) if denominator is not None else 0
        
        if den == 0:
            return default
            
        return num / den
    except (TypeError, ValueError, ZeroDivisionError):
        return default


def safe_percentage_change(
    current: Any, 
    previous: Any, 
    default: float = 0.0
) -> float:
    """
    Cálculo seguro de cambio porcentual
    
    Args:
        current: Valor actual
        previous: Valor anterior
        default: Valor por defecto
        
    Returns:
        Cambio porcentual o default
    """
    try:
        curr = float(current) if current is not None else 0
        prev = float(previous) if previous is not None else 0
        
        if prev == 0:
            # Si previous es 0 pero current > 0, es crecimiento infinito
            # Retornamos 100 como indicador de crecimiento alto
            return 100.0 if curr > 0 else default
            
        return ((curr - prev) / prev) * 100
    except (TypeError, ValueError, ZeroDivisionError):
        return default


# =============================================================================
# PROMEDIOS Y AGREGACIONES SEGURAS
# =============================================================================

def safe_average(
    values: Any, 
    default: float = 0.0
) -> float:
    """
    Promedio seguro de una lista
    
    Args:
        values: Lista de valores (puede ser None o vacía)
        default: Valor por defecto
        
    Returns:
        Promedio o default
    """
    if not values:
        return default
        
    try:
        # Filtrar valores válidos
        valid = [float(v) for v in values if v is not None]
        
        if not valid:
            return default
            
        return sum(valid) / len(valid)
    except (TypeError, ValueError):
        return default


def safe_sum(
    values: Any, 
    default: float = 0.0
) -> float:
    """
    Suma segura de una lista
    
    Args:
        values: Lista de valores
        default: Valor por defecto
        
    Returns:
        Suma o default
    """
    if not values:
        return default
        
    try:
        valid = [float(v) for v in values if v is not None]
        return sum(valid)
    except (TypeError, ValueError):
        return default


def safe_max(
    values: Any, 
    default: float = 0.0
) -> float:
    """
    Máximo seguro de una lista
    """
    if not values:
        return default
        
    try:
        valid = [float(v) for v in values if v is not None]
        return max(valid) if valid else default
    except (TypeError, ValueError):
        return default


def safe_min(
    values: Any, 
    default: float = 0.0
) -> float:
    """
    Mínimo seguro de una lista
    """
    if not values:
        return default
        
    try:
        valid = [float(v) for v in values if v is not None]
        return min(valid) if valid else default
    except (TypeError, ValueError):
        return default


# =============================================================================
# ACCESO SEGURO A DATOS
# =============================================================================

def safe_get(
    data: Any, 
    key: Any, 
    default: Any = None
) -> Any:
    """
    Acceso seguro a diccionario, lista o atributo
    
    Args:
        data: Diccionario, lista u objeto
        key: Clave, índice o nombre de atributo
        default: Valor por defecto
        
    Returns:
        Valor o default
    """
    if data is None:
        return default
        
    try:
        if isinstance(data, dict):
            return data.get(key, default)
        elif isinstance(data, (list, tuple)):
            if isinstance(key, int) and -len(data) <= key < len(data):
                return data[key]
            return default
        else:
            return getattr(data, key, default)
    except (KeyError, IndexError, TypeError, AttributeError):
        return default


def safe_get_nested(
    data: Any, 
    *keys, 
    default: Any = None
) -> Any:
    """
    Acceso seguro a datos anidados
    
    Args:
        data: Datos (dict/list/objeto)
        *keys: Secuencia de claves/índices
        default: Valor por defecto
        
    Returns:
        Valor anidado o default
        
    Ejemplo:
        safe_get_nested(data, "user", "profile", "name", default="Unknown")
    """
    result = data
    
    for key in keys:
        result = safe_get(result, key, None)
        if result is None:
            return default
            
    return result if result is not None else default


# =============================================================================
# CONVERSIONES SEGURAS
# =============================================================================

def safe_int(
    value: Any, 
    default: int = 0
) -> int:
    """
    Conversión segura a int
    """
    if value is None:
        return default
        
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def safe_float(
    value: Any, 
    default: float = 0.0
) -> float:
    """
    Conversión segura a float
    """
    if value is None:
        return default
        
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_str(
    value: Any, 
    default: str = ""
) -> str:
    """
    Conversión segura a string
    """
    if value is None:
        return default
        
    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def safe_bool(
    value: Any, 
    default: bool = False
) -> bool:
    """
    Conversión segura a bool
    """
    if value is None:
        return default
        
    if isinstance(value, bool):
        return value
        
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'si', 'sí')
        
    try:
        return bool(value)
    except (TypeError, ValueError):
        return default


# =============================================================================
# LISTAS SEGURAS
# =============================================================================

def safe_first(
    values: Any, 
    default: Any = None
) -> Any:
    """
    Obtiene el primer elemento de forma segura
    """
    if not values:
        return default
        
    try:
        return values[0]
    except (IndexError, TypeError):
        return default


def safe_last(
    values: Any, 
    default: Any = None
) -> Any:
    """
    Obtiene el último elemento de forma segura
    """
    if not values:
        return default
        
    try:
        return values[-1]
    except (IndexError, TypeError):
        return default


def safe_slice(
    values: Any, 
    start: int = 0, 
    end: Optional[int] = None, 
    default: List = None
) -> List:
    """
    Slice seguro de una lista
    """
    if default is None:
        default = []
        
    if not values:
        return default
        
    try:
        if end is None:
            return list(values[start:])
        return list(values[start:end])
    except (TypeError, IndexError):
        return default


# =============================================================================
# OPERACIONES CONDICIONALES SEGURAS
# =============================================================================

def safe_call(
    func: Callable, 
    *args, 
    default: Any = None, 
    **kwargs
) -> Any:
    """
    Llamada segura a una función
    
    Args:
        func: Función a llamar
        *args: Argumentos posicionales
        default: Valor por defecto si falla
        **kwargs: Argumentos con nombre
        
    Returns:
        Resultado de la función o default
    """
    try:
        return func(*args, **kwargs)
    except Exception:
        return default


def coalesce(*values, default: Any = None) -> Any:
    """
    Retorna el primer valor no-None
    Similar a COALESCE de SQL
    
    Args:
        *values: Valores a evaluar
        default: Valor si todos son None
        
    Returns:
        Primer valor no-None o default
    """
    for value in values:
        if value is not None:
            return value
    return default


def if_none(value: Any, replacement: Any) -> Any:
    """
    Retorna replacement si value es None
    """
    return replacement if value is None else value


def if_empty(value: Any, replacement: Any) -> Any:
    """
    Retorna replacement si value está vacío (None, "", [], {})
    """
    if value is None:
        return replacement
    if isinstance(value, (str, list, dict, tuple, set)) and len(value) == 0:
        return replacement
    return value


# =============================================================================
# MÉTRICAS ESPECÍFICAS PARA TRENDS
# =============================================================================

def safe_growth_rate(
    values: List[float], 
    periods: int = 3, 
    default: float = 0.0
) -> float:
    """
    Calcula tasa de crecimiento de forma segura
    
    Args:
        values: Lista de valores temporales
        periods: Número de períodos a comparar
        default: Valor por defecto
        
    Returns:
        Tasa de crecimiento como porcentaje
    """
    if not values or len(values) < periods * 2:
        return default
        
    try:
        recent = safe_average(values[-periods:], 0)
        previous = safe_average(values[:periods], 0)
        
        return safe_percentage_change(recent, previous, default)
    except Exception:
        return default


def safe_trend_score(
    current: Any, 
    average: Any, 
    max_score: float = 100.0, 
    default: float = 50.0
) -> float:
    """
    Calcula score de tendencia de forma segura
    
    Args:
        current: Valor actual
        average: Valor promedio
        max_score: Score máximo
        default: Valor por defecto
        
    Returns:
        Score entre 0 y max_score
    """
    try:
        curr = safe_float(current, 0)
        avg = safe_float(average, 0)
        
        if avg == 0:
            return default
            
        ratio = curr / avg
        score = ratio * (max_score / 2)  # ratio 1.0 = 50 points
        
        return min(max_score, max(0, score))
    except Exception:
        return default


# =============================================================================
# VALIDACIONES
# =============================================================================

def is_valid_number(value: Any) -> bool:
    """Verifica si es un número válido (no None, no NaN, no Inf)"""
    if value is None:
        return False
        
    try:
        f = float(value)
        import math
        return not (math.isnan(f) or math.isinf(f))
    except (TypeError, ValueError):
        return False


def is_valid_list(value: Any, min_length: int = 0) -> bool:
    """Verifica si es una lista válida con longitud mínima"""
    if not isinstance(value, (list, tuple)):
        return False
    return len(value) >= min_length


def is_valid_dict(value: Any, required_keys: List[str] = None) -> bool:
    """Verifica si es un diccionario válido con claves requeridas"""
    if not isinstance(value, dict):
        return False
    if required_keys:
        return all(k in value for k in required_keys)
    return True


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Divisiones
    'safe_divide',
    'safe_percentage_change',
    
    # Agregaciones
    'safe_average',
    'safe_sum',
    'safe_max',
    'safe_min',
    
    # Acceso a datos
    'safe_get',
    'safe_get_nested',
    
    # Conversiones
    'safe_int',
    'safe_float',
    'safe_str',
    'safe_bool',
    
    # Listas
    'safe_first',
    'safe_last',
    'safe_slice',
    
    # Condicionales
    'safe_call',
    'coalesce',
    'if_none',
    'if_empty',
    
    # Métricas trends
    'safe_growth_rate',
    'safe_trend_score',
    
    # Validaciones
    'is_valid_number',
    'is_valid_list',
    'is_valid_dict',
    
    # Retry y resiliencia
    'retry_with_backoff',
    'check_service_health',
]


# =============================================================================
# RETRY CON BACKOFF EXPONENCIAL
# =============================================================================

import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorador para reintentar funciones con backoff exponencial
    
    Args:
        max_retries: Número máximo de reintentos
        base_delay: Delay inicial en segundos
        max_delay: Delay máximo en segundos
        exceptions: Tupla de excepciones a capturar
        on_retry: Callback opcional (attempt, exception, delay)
    
    Usage:
        @retry_with_backoff(max_retries=3)
        def fetch_data():
            return api.get_data()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Último intento, propagar excepción
                        logger.warning(
                            f"[Retry] {func.__name__} falló después de {max_retries + 1} intentos: {e}"
                        )
                        raise
                    
                    # Calcular delay con backoff exponencial
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    logger.info(
                        f"[Retry] {func.__name__} intento {attempt + 1}/{max_retries + 1} "
                        f"falló: {e}. Reintentando en {delay:.1f}s..."
                    )
                    
                    if on_retry:
                        on_retry(attempt + 1, e, delay)
                    
                    time.sleep(delay)
            
            # No debería llegar aquí, pero por seguridad
            if last_exception:
                raise last_exception
            return None
        
        return wrapper
    return decorator


def check_service_health(
    name: str,
    check_func: Callable,
    timeout: float = 5.0
) -> Dict[str, Any]:
    """
    Verifica el estado de un servicio
    
    Args:
        name: Nombre del servicio
        check_func: Función que verifica el servicio (debe devolver True/False)
        timeout: Timeout en segundos
    
    Returns:
        Dict con estado del servicio
    """
    import threading
    
    result = {"name": name, "ok": False, "message": "Timeout", "latency_ms": None}
    
    def run_check():
        nonlocal result
        start = time.time()
        try:
            is_ok = check_func()
            latency = (time.time() - start) * 1000
            result = {
                "name": name,
                "ok": bool(is_ok),
                "message": "OK" if is_ok else "Error en verificación",
                "latency_ms": round(latency, 1)
            }
        except Exception as e:
            latency = (time.time() - start) * 1000
            result = {
                "name": name,
                "ok": False,
                "message": str(e)[:100],
                "latency_ms": round(latency, 1)
            }
    
    thread = threading.Thread(target=run_check)
    thread.start()
    thread.join(timeout=timeout)
    
    return result
