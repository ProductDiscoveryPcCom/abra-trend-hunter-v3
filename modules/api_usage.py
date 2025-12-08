"""
API Usage Tracking Module
Registra el uso de APIs de pago (SerpAPI, Claude, OpenAI, Perplexity)
para control de costes en Supabase
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Intentar importar supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class APIName(Enum):
    """APIs soportadas"""
    SERPAPI = "serpapi"
    CLAUDE = "claude"
    OPENAI = "openai"
    PERPLEXITY = "perplexity"


class SerpAPIEndpoint(Enum):
    """Endpoints de SerpAPI"""
    GOOGLE_TRENDS = "google_trends"
    GOOGLE_NEWS = "google_news"
    GOOGLE_SHOPPING = "google_shopping"
    YOUTUBE_SEARCH = "youtube_search"
    RELATED_SEARCHES = "related_searches"
    PAA = "people_also_ask"


# Costes estimados por llamada/token (en EUR, conversión ~0.92 de USD)
# Actualizado: Diciembre 2025
API_COSTS_EUR = {
    "serpapi": {
        "per_call": 0.012,  # ~€50/4000 searches ≈ €0.012/search
    },
    "claude": {
        "input_per_1k": 0.003,   # Claude Sonnet 4.5
        "output_per_1k": 0.014,
    },
    "openai": {
        "input_per_1k": 0.0014,  # GPT-4o-mini
        "output_per_1k": 0.0055,
    },
    "perplexity": {
        "per_call": 0.005,  # Estimado
        "input_per_1k": 0.001,
        "output_per_1k": 0.001,
    }
}


@dataclass
class APIUsageRecord:
    """Registro de uso de API"""
    api_name: str
    endpoint: Optional[str] = None
    keyword: Optional[str] = None
    tokens_input: int = 0
    tokens_output: int = 0
    estimated_cost: float = 0.0
    success: bool = True
    cached: bool = False
    error_message: Optional[str] = None


def _get_supabase_client() -> Optional[Client]:
    """Obtiene cliente de Supabase si está configurado"""
    if not SUPABASE_AVAILABLE:
        return None
    
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    
    return None


def _get_current_user() -> str:
    """Obtiene el email del usuario actual de la sesión"""
    return st.session_state.get("user_email", "anonymous")


def calculate_cost(
    api_name: str,
    tokens_input: int = 0,
    tokens_output: int = 0,
    is_cached: bool = False
) -> float:
    """
    Calcula el coste estimado de una llamada a API
    
    Args:
        api_name: Nombre de la API
        tokens_input: Tokens de entrada (para LLMs)
        tokens_output: Tokens de salida (para LLMs)
        is_cached: Si es respuesta cacheada (coste 0)
    
    Returns:
        Coste estimado en EUR
    """
    if is_cached:
        return 0.0
    
    costs = API_COSTS_EUR.get(api_name, {})
    
    if api_name == "serpapi":
        return costs.get("per_call", 0.012)
    
    # LLMs - coste por tokens
    input_cost = (tokens_input / 1000) * costs.get("input_per_1k", 0)
    output_cost = (tokens_output / 1000) * costs.get("output_per_1k", 0)
    
    return input_cost + output_cost


def log_api_usage(
    api_name: str,
    endpoint: Optional[str] = None,
    keyword: Optional[str] = None,
    tokens_input: int = 0,
    tokens_output: int = 0,
    success: bool = True,
    cached: bool = False,
    error_message: Optional[str] = None
) -> bool:
    """
    Registra el uso de una API en Supabase
    
    Args:
        api_name: 'serpapi', 'claude', 'openai', 'perplexity'
        endpoint: Tipo de llamada específica
        keyword: Keyword buscada (si aplica)
        tokens_input: Tokens de entrada
        tokens_output: Tokens de salida
        success: Si la llamada fue exitosa
        cached: Si se usó caché (no se cobra)
        error_message: Mensaje de error si falló
    
    Returns:
        True si se registró correctamente
    """
    client = _get_supabase_client()
    
    # Calcular coste
    estimated_cost = calculate_cost(
        api_name=api_name,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        is_cached=cached
    )
    
    # Preparar registro
    record = {
        "user_email": _get_current_user(),
        "api_name": api_name,
        "endpoint": endpoint,
        "keyword": keyword[:200] if keyword else None,  # Limitar longitud
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "estimated_cost": estimated_cost,
        "response_status": "success" if success else "error",
        "cached": cached,
        "error_message": error_message[:500] if error_message else None
    }
    
    # También guardar en session_state para debug
    if "api_usage_session" not in st.session_state:
        st.session_state.api_usage_session = []
    
    st.session_state.api_usage_session.append({
        **record,
        "timestamp": datetime.now().isoformat()
    })
    
    # Guardar en Supabase si está disponible
    if client:
        try:
            client.table("api_usage_logs").insert(record).execute()
            return True
        except Exception as e:
            # Silenciar errores de logging para no interrumpir el flujo
            print(f"Warning: Could not log API usage: {e}")
            return False
    
    return True  # Registrado en session_state al menos


def log_serpapi_call(
    endpoint: str,
    keyword: str,
    cached: bool = False,
    success: bool = True,
    error_message: Optional[str] = None
) -> bool:
    """
    Atajo para registrar llamadas a SerpAPI
    
    Args:
        endpoint: 'google_trends', 'google_news', 'youtube_search', etc.
        keyword: Keyword buscada
        cached: Si se usó caché
        success: Si fue exitosa
        error_message: Mensaje de error
    
    Returns:
        True si se registró
    """
    return log_api_usage(
        api_name="serpapi",
        endpoint=endpoint,
        keyword=keyword,
        cached=cached,
        success=success,
        error_message=error_message
    )


def log_ai_call(
    provider: str,  # 'claude', 'openai', 'perplexity'
    tokens_input: int,
    tokens_output: int,
    endpoint: Optional[str] = None,
    keyword: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> bool:
    """
    Atajo para registrar llamadas a APIs de IA
    
    Args:
        provider: 'claude', 'openai', 'perplexity'
        tokens_input: Tokens de entrada
        tokens_output: Tokens de salida
        endpoint: Tipo de análisis
        keyword: Keyword analizada
        success: Si fue exitosa
        error_message: Mensaje de error
    
    Returns:
        True si se registró
    """
    return log_api_usage(
        api_name=provider.lower(),
        endpoint=endpoint,
        keyword=keyword,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        success=success,
        error_message=error_message
    )


def get_session_usage_summary() -> Dict[str, Any]:
    """
    Obtiene resumen de uso de APIs en la sesión actual
    
    Returns:
        Dict con totales por API
    """
    usage = st.session_state.get("api_usage_session", [])
    
    summary = {
        "total_calls": len(usage),
        "total_cost_eur": 0.0,
        "by_api": {}
    }
    
    for record in usage:
        api = record.get("api_name", "unknown")
        cost = record.get("estimated_cost", 0)
        
        if api not in summary["by_api"]:
            summary["by_api"][api] = {
                "calls": 0,
                "cached": 0,
                "cost_eur": 0.0
            }
        
        summary["by_api"][api]["calls"] += 1
        if record.get("cached"):
            summary["by_api"][api]["cached"] += 1
        summary["by_api"][api]["cost_eur"] += cost
        summary["total_cost_eur"] += cost
    
    return summary


def render_usage_badge() -> None:
    """Renderiza badge de uso de APIs en la sesión"""
    summary = get_session_usage_summary()
    
    if summary["total_calls"] == 0:
        return
    
    total_cost = summary["total_cost_eur"]
    
    # Mostrar badge compacto
    st.sidebar.markdown("---")
    st.sidebar.markdown("##### 📊 Uso APIs (sesión)")
    
    for api, data in summary["by_api"].items():
        icon = {
            "serpapi": "🔍",
            "claude": "🤖",
            "openai": "💚",
            "perplexity": "🌐"
        }.get(api, "📡")
        
        cached_text = f" ({data['cached']} cache)" if data['cached'] > 0 else ""
        st.sidebar.caption(
            f"{icon} {api}: {data['calls']} calls{cached_text} · €{data['cost_eur']:.4f}"
        )
    
    st.sidebar.markdown(f"**Total: €{total_cost:.4f}**")


def get_monthly_costs(client: Optional[Client] = None) -> Optional[Dict[str, Any]]:
    """
    Obtiene costes del mes actual desde Supabase
    
    Returns:
        Dict con costes por API o None si no hay datos
    """
    if client is None:
        client = _get_supabase_client()
    
    if not client:
        return None
    
    try:
        result = client.rpc("get_current_month_cost").execute()
        
        if result.data:
            costs = {}
            total = 0.0
            
            for row in result.data:
                api = row.get("api_name", "unknown")
                cost = float(row.get("cost", 0))
                calls = int(row.get("calls", 0))
                
                costs[api] = {"calls": calls, "cost_eur": cost}
                total += cost
            
            return {
                "by_api": costs,
                "total_cost_eur": total,
                "month": datetime.now().strftime("%Y-%m")
            }
    except Exception as e:
        print(f"Error getting monthly costs: {e}")
    
    return None
