"""
Módulo centralizado de funciones de formateo
Evita duplicación de format_number, format_volume, format_change, etc.
"""

from typing import Union, Optional
from datetime import datetime, timedelta


def format_number(num: Union[int, float, None], decimals: int = 0) -> str:
    """
    Formatea un número con separadores de miles
    
    Args:
        num: Número a formatear
        decimals: Decimales a mostrar (default 0)
        
    Returns:
        String formateado (ej: "1.234.567" o "1,23M")
    """
    if num is None:
        return "N/A"
    
    try:
        num = float(num)
    except (ValueError, TypeError):
        return "N/A"
    
    if abs(num) >= 1_000_000_000:
        return f"{num/1_000_000_000:.1f}B"
    elif abs(num) >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif abs(num) >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        if decimals > 0:
            return f"{num:,.{decimals}f}".replace(",", ".")
        return f"{num:,.0f}".replace(",", ".")


def format_volume(volume: Union[int, float, None]) -> str:
    """
    Formatea volumen de búsquedas (de Google Ads o similares)
    
    Args:
        volume: Volumen mensual
        
    Returns:
        String formateado (ej: "10K", "1.2M")
    """
    if volume is None or volume == 0:
        return "—"
    
    try:
        volume = int(volume)
    except (ValueError, TypeError):
        return "—"
    
    if volume >= 1_000_000:
        return f"{volume/1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"{volume/1_000:.0f}K"
    else:
        return str(volume)


def format_change(change: Union[float, None], include_sign: bool = True) -> str:
    """
    Formatea cambio porcentual con color/emoji
    
    Args:
        change: Cambio en porcentaje (ej: 15.5 = +15.5%)
        include_sign: Si incluir + para positivos
        
    Returns:
        String formateado con indicador (ej: "↑15.5%", "↓3.2%")
    """
    if change is None:
        return "—"
    
    try:
        change = float(change)
    except (ValueError, TypeError):
        return "—"
    
    if change > 0:
        arrow = "↑"
        sign = "+" if include_sign else ""
        return f"{arrow}{sign}{change:.1f}%"
    elif change < 0:
        arrow = "↓"
        return f"{arrow}{change:.1f}%"
    else:
        return "→0%"


def format_change_simple(change: Union[float, None]) -> str:
    """
    Formatea cambio sin flechas, solo signo
    
    Args:
        change: Cambio en porcentaje
        
    Returns:
        String formateado (ej: "+15%", "-3%")
    """
    if change is None:
        return "—"
    
    try:
        change = float(change)
    except (ValueError, TypeError):
        return "—"
    
    if change > 0:
        return f"+{change:.0f}%"
    elif change < 0:
        return f"{change:.0f}%"
    else:
        return "0%"


def format_score(score: Union[int, float, None], max_score: int = 100) -> str:
    """
    Formatea un score con indicador visual
    
    Args:
        score: Score a formatear
        max_score: Score máximo (para calcular %)
        
    Returns:
        String con score y barra visual
    """
    if score is None:
        return "—"
    
    try:
        score = int(score)
    except (ValueError, TypeError):
        return "—"
    
    # Proteger división por cero
    if max_score <= 0:
        max_score = 100
    
    # Barra visual simple
    filled = int((score / max_score) * 5)
    filled = max(0, min(5, filled))  # Clamp entre 0 y 5
    bar = "█" * filled + "░" * (5 - filled)
    
    return f"{score} {bar}"


def format_date(dt: Union[datetime, str, None], format_str: str = "%d/%m/%Y") -> str:
    """
    Formatea fecha de forma consistente
    
    Args:
        dt: Datetime o string ISO
        format_str: Formato de salida
        
    Returns:
        String formateado
    """
    if dt is None:
        return "—"
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            return dt
    
    return dt.strftime(format_str)


def format_relative_time(dt: Union[datetime, str, None]) -> str:
    """
    Formatea tiempo relativo (hace X días/horas)
    
    Args:
        dt: Datetime o string ISO
        
    Returns:
        String relativo (ej: "Hace 2 días", "Hace 3 horas")
    """
    if dt is None:
        return "—"
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            return dt
    
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"Hace {years} año{'s' if years > 1 else ''}"
    elif diff.days > 30:
        months = diff.days // 30
        return f"Hace {months} mes{'es' if months > 1 else ''}"
    elif diff.days > 0:
        return f"Hace {diff.days} día{'s' if diff.days > 1 else ''}"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"Hace {hours} hora{'s' if hours > 1 else ''}"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"Hace {minutes} minuto{'s' if minutes > 1 else ''}"
    else:
        return "Ahora"


def format_currency(amount: Union[float, int, None], currency: str = "EUR") -> str:
    """
    Formatea cantidad monetaria
    
    Args:
        amount: Cantidad
        currency: Código de moneda (EUR, USD, GBP)
        
    Returns:
        String formateado (ej: "1.234,56 €")
    """
    if amount is None:
        return "—"
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return "—"
    
    symbols = {"EUR": "€", "USD": "$", "GBP": "£"}
    symbol = symbols.get(currency, currency)
    
    # Formato europeo: 1.234,56 €
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    return f"{formatted} {symbol}"


def format_percentage(value: Union[float, None], decimals: int = 1) -> str:
    """
    Formatea porcentaje
    
    Args:
        value: Valor (0.15 = 15%)
        decimals: Decimales a mostrar
        
    Returns:
        String formateado (ej: "15.0%")
    """
    if value is None:
        return "—"
    
    try:
        value = float(value) * 100
    except (ValueError, TypeError):
        return "—"
    
    return f"{value:.{decimals}f}%"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Trunca texto largo
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo para texto truncado
        
    Returns:
        Texto truncado si excede max_length
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_list(items: list, separator: str = ", ", max_items: int = 5) -> str:
    """
    Formatea lista como string
    
    Args:
        items: Lista de items
        separator: Separador
        max_items: Máximo de items a mostrar
        
    Returns:
        String con items separados
    """
    if not items:
        return "—"
    
    if len(items) <= max_items:
        return separator.join(str(item) for item in items)
    
    shown = separator.join(str(item) for item in items[:max_items])
    remaining = len(items) - max_items
    return f"{shown} (+{remaining} más)"
