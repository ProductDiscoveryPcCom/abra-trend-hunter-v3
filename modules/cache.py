"""
Cache Module - Persistencia de datos con Supabase
Reduce llamadas a APIs guardando resultados por 30 días

Configuración en secrets.toml:
    SUPABASE_URL = "https://xxxxx.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
"""

import json
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Versión del formato de datos
# Incrementar si cambiamos estructura de los datos cacheados
DATA_VERSION = 1

# TTL por defecto: 30 días
DEFAULT_TTL_DAYS = 30


@dataclass
class CacheResult:
    """Resultado de una consulta de caché"""
    hit: bool                    # True si encontró datos válidos
    data: Optional[Dict] = None  # Datos cacheados
    age_hours: float = 0         # Antigüedad en horas
    keyword: str = ""
    country: str = ""
    
    @property
    def age_formatted(self) -> str:
        """Devuelve la antigüedad formateada"""
        if self.age_hours < 1:
            return "hace menos de 1 hora"
        elif self.age_hours < 24:
            return f"hace {int(self.age_hours)} horas"
        else:
            days = int(self.age_hours / 24)
            return f"hace {days} día{'s' if days > 1 else ''}"


class TrendCache:
    """
    Gestor de caché con Supabase.
    
    Guarda resultados de búsquedas para evitar llamadas repetidas a APIs.
    Cada combinación keyword+country+timeframe se guarda como una fila.
    """
    
    def __init__(self):
        self._client = None
        self._available = False
        self._error = ""
        self.ttl_days = DEFAULT_TTL_DAYS
        self._init_client()
    
    def _init_client(self):
        """Inicializa cliente de Supabase"""
        try:
            url = st.secrets.get("SUPABASE_URL", "")
            key = st.secrets.get("SUPABASE_KEY", "")
            
            if not url or not key:
                self._error = "No configurado"
                return
            
            from supabase import create_client
            self._client = create_client(url, key)
            self._available = True
            
        except ImportError:
            self._error = "supabase no instalado"
        except Exception as e:
            self._error = str(e)[:50]
    
    @property
    def is_available(self) -> bool:
        """Indica si el caché está disponible"""
        return self._available
    
    @property
    def last_error(self) -> str:
        """Último error si lo hay"""
        return self._error
    
    def get(
        self, 
        keyword: str, 
        country: str, 
        timeframe: str = "today 5-y"
    ) -> CacheResult:
        """
        Busca datos en caché.
        Primero busca en memoria (session_state), luego en Supabase.
        
        Args:
            keyword: Término buscado
            country: Código de país (ES, FR, etc.)
            timeframe: Período de tiempo
            
        Returns:
            CacheResult con hit=True si encontró datos válidos
        """
        # Normalizar keyword
        keyword_lower = keyword.lower().strip()
        cache_key = f"{keyword_lower}_{country.upper()}_{timeframe}"
        
        # 1. Buscar en memoria primero (instantáneo)
        if "memory_cache" in st.session_state:
            if cache_key in st.session_state.memory_cache:
                cached = st.session_state.memory_cache[cache_key]
                # Verificar que no esté expirado en memoria (1 hora)
                cached_time = cached.get("_cached_at", 0)
                if (datetime.now().timestamp() - cached_time) < 3600:
                    return CacheResult(
                        hit=True,
                        data=cached.get("data"),
                        age_hours=cached.get("age_hours", 0),
                        keyword=keyword_lower,
                        country=country
                    )
        
        if not self._available:
            return CacheResult(hit=False)
        
        try:
            # 2. Buscar en Supabase
            result = self._client.table("trend_cache")\
                .select("*")\
                .eq("keyword", keyword_lower)\
                .eq("country", country.upper())\
                .eq("timeframe", timeframe)\
                .maybe_single()\
                .execute()
            
            if not result.data:
                return CacheResult(hit=False, keyword=keyword_lower, country=country)
            
            row = result.data
            
            # Verificar versión de datos
            if row.get("data_version", 0) != DATA_VERSION:
                # Datos con formato antiguo, ignorar
                return CacheResult(hit=False, keyword=keyword_lower, country=country)
            
            # Verificar TTL
            updated_at = datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))
            now = datetime.now(updated_at.tzinfo) if updated_at.tzinfo else datetime.now()
            age = now - updated_at
            age_hours = age.total_seconds() / 3600
            
            if age > timedelta(days=self.ttl_days):
                # Expirado
                return CacheResult(
                    hit=False, 
                    keyword=keyword_lower, 
                    country=country,
                    age_hours=age_hours
                )
            
            # Datos válidos - guardar en memoria para esta sesión
            result = CacheResult(
                hit=True,
                data=row,
                age_hours=age_hours,
                keyword=keyword_lower,
                country=country
            )
            
            # Guardar en memoria para evitar llamadas repetidas a Supabase
            if "memory_cache" not in st.session_state:
                st.session_state.memory_cache = {}
            st.session_state.memory_cache[cache_key] = {
                "data": row,
                "age_hours": age_hours,
                "_cached_at": datetime.now().timestamp()
            }
            
            return result
            
        except Exception as e:
            self._error = str(e)[:50]
            return CacheResult(hit=False)
    
    def save(
        self,
        keyword: str,
        country: str,
        timeframe: str,
        timeline_data: Any = None,
        related_data: Any = None,
        google_ads_data: Any = None,
        youtube_data: Any = None,
        news_data: Any = None,
        ai_analysis: Any = None,
        trend_score: int = 0,
        potential_score: int = 0,
        extra_data: Dict = None
    ) -> bool:
        """
        Guarda datos en caché.
        
        Args:
            keyword: Término buscado
            country: Código de país
            timeframe: Período
            timeline_data: Datos de Google Trends
            related_data: Queries relacionadas
            google_ads_data: Volúmenes de Google Ads
            youtube_data: Métricas de YouTube
            news_data: Noticias
            ai_analysis: Análisis de IA
            trend_score: Score de tendencia calculado
            potential_score: Score de potencial calculado
            extra_data: Datos adicionales
            
        Returns:
            True si se guardó correctamente
        """
        if not self._available:
            return False
        
        try:
            keyword_lower = keyword.lower().strip()
            now = datetime.utcnow().isoformat()
            
            # Preparar datos para guardar
            row = {
                "keyword": keyword_lower,
                "country": country.upper(),
                "timeframe": timeframe,
                "data_version": DATA_VERSION,
                "updated_at": now,
                "trend_score": trend_score,
                "potential_score": potential_score,
            }
            
            # Serializar datos complejos a JSON
            if timeline_data is not None:
                row["timeline_data"] = self._serialize(timeline_data)
            
            if related_data is not None:
                row["related_data"] = self._serialize(related_data)
            
            if google_ads_data is not None:
                row["google_ads_data"] = self._serialize(google_ads_data)
            
            if youtube_data is not None:
                row["youtube_data"] = self._serialize(youtube_data)
            
            if news_data is not None:
                row["news_data"] = self._serialize(news_data)
            
            if ai_analysis is not None:
                row["ai_analysis"] = self._serialize(ai_analysis)
            
            if extra_data is not None:
                row["extra_data"] = self._serialize(extra_data)
            
            # Upsert (insert or update)
            self._client.table("trend_cache")\
                .upsert(row, on_conflict="keyword,country,timeframe")\
                .execute()
            
            return True
            
        except Exception as e:
            self._error = str(e)[:50]
            return False
    
    def delete(self, keyword: str, country: str, timeframe: str = "today 5-y") -> bool:
        """Elimina una entrada del caché"""
        if not self._available:
            return False
        
        try:
            self._client.table("trend_cache")\
                .delete()\
                .eq("keyword", keyword.lower().strip())\
                .eq("country", country.upper())\
                .eq("timeframe", timeframe)\
                .execute()
            return True
        except Exception:
            return False
    
    def clear_expired(self) -> int:
        """
        Elimina entradas expiradas.
        
        Returns:
            Número de filas eliminadas
        """
        if not self._available:
            return 0
        
        try:
            cutoff = (datetime.utcnow() - timedelta(days=self.ttl_days)).isoformat()
            
            result = self._client.table("trend_cache")\
                .delete()\
                .lt("updated_at", cutoff)\
                .execute()
            
            return len(result.data) if result.data else 0
        except Exception:
            return 0
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del caché.
        
        Returns:
            Dict con estadísticas
        """
        if not self._available:
            return {"available": False, "error": self._error}
        
        try:
            # Contar total
            result = self._client.table("trend_cache")\
                .select("keyword", count="exact")\
                .execute()
            
            total = result.count if hasattr(result, 'count') else 0
            
            # Contar por país
            countries = {}
            for code in ["ES", "PT", "FR", "IT", "DE"]:
                r = self._client.table("trend_cache")\
                    .select("keyword", count="exact")\
                    .eq("country", code)\
                    .execute()
                countries[code] = r.count if hasattr(r, 'count') else 0
            
            return {
                "available": True,
                "total_entries": total,
                "by_country": countries,
                "ttl_days": self.ttl_days,
                "data_version": DATA_VERSION
            }
        except Exception as e:
            return {"available": True, "error": str(e)[:50]}
    
    def _serialize(self, data: Any) -> Any:
        """Serializa datos para guardar en JSONB"""
        if data is None:
            return None
        
        # Si ya es serializable, devolverlo
        if isinstance(data, (dict, list, str, int, float, bool)):
            return data
        
        # Si es dataclass, convertir a dict
        if hasattr(data, '__dataclass_fields__'):
            return self._dataclass_to_dict(data)
        
        # Intentar convertir a dict
        if hasattr(data, '__dict__'):
            return self._clean_dict(data.__dict__)
        
        # Último recurso: str
        return str(data)
    
    def _dataclass_to_dict(self, obj) -> Dict:
        """Convierte dataclass a dict recursivamente"""
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name)
            if hasattr(value, '__dataclass_fields__'):
                result[field_name] = self._dataclass_to_dict(value)
            elif isinstance(value, list):
                result[field_name] = [
                    self._dataclass_to_dict(v) if hasattr(v, '__dataclass_fields__') else v
                    for v in value
                ]
            elif isinstance(value, datetime):
                result[field_name] = value.isoformat()
            else:
                result[field_name] = value
        return result
    
    def _clean_dict(self, d: Dict) -> Dict:
        """Limpia un dict para serialización"""
        result = {}
        for k, v in d.items():
            if k.startswith('_'):
                continue
            if isinstance(v, datetime):
                result[k] = v.isoformat()
            elif isinstance(v, (dict, list, str, int, float, bool, type(None))):
                result[k] = v
            elif hasattr(v, '__dict__'):
                result[k] = self._clean_dict(v.__dict__)
            else:
                result[k] = str(v)
        return result


# =============================================================================
# SINGLETON Y FUNCIONES DE CONVENIENCIA
# =============================================================================

_cache_instance: Optional[TrendCache] = None


def get_cache() -> Optional[TrendCache]:
    """Obtiene instancia singleton del caché"""
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = TrendCache()
    
    return _cache_instance if _cache_instance.is_available else None


def check_cache_config() -> Dict[str, Any]:
    """Verifica configuración del caché"""
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    
    configured = bool(url and key)
    
    result = {
        "configured": configured,
        "has_url": bool(url),
        "has_key": bool(key),
    }
    
    if configured:
        cache = get_cache()
        if cache:
            result["available"] = True
            result["stats"] = cache.get_stats()
        else:
            result["available"] = False
            result["error"] = "Error conectando"
    
    return result


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_cache_indicator(cache_result: CacheResult) -> None:
    """
    Renderiza indicador de caché en la UI.
    
    Args:
        cache_result: Resultado de get_cache()
    """
    if cache_result.hit:
        st.caption(f"📦 Datos en caché ({cache_result.age_formatted})")
    else:
        st.caption("🔄 Datos actualizados")


def render_cache_status_sidebar() -> None:
    """Renderiza estado del caché en sidebar"""
    config = check_cache_config()
    
    if not config["configured"]:
        st.caption("💾 Caché: No configurado")
        return
    
    if not config.get("available"):
        st.caption(f"💾 Caché: ❌ {config.get('error', 'Error')}")
        return
    
    stats = config.get("stats", {})
    total = stats.get("total_entries", 0)
    st.caption(f"💾 Caché: ✅ {total} búsquedas guardadas")
