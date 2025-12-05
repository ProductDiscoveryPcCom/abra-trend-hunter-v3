"""
Google Ads Keyword Planner Integration
Obtiene volúmenes de búsqueda REALES de Google Ads API

Requisitos:
- Cuenta de Google Ads con historial de gasto
- Developer Token aprobado
- OAuth 2.0 credentials configurados
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class KeywordMetrics:
    """Métricas de una keyword de Google Ads"""
    keyword: str
    avg_monthly_searches: int = 0
    competition: str = "UNKNOWN"  # LOW, MEDIUM, HIGH
    competition_index: int = 0  # 0-100
    low_cpc_micros: int = 0
    high_cpc_micros: int = 0
    monthly_volumes: List[Dict] = field(default_factory=list)
    
    @property
    def low_cpc(self) -> float:
        """CPC bajo en euros"""
        return self.low_cpc_micros / 1_000_000
    
    @property
    def high_cpc(self) -> float:
        """CPC alto en euros"""
        return self.high_cpc_micros / 1_000_000
    
    @property
    def avg_cpc(self) -> float:
        """CPC promedio"""
        return (self.low_cpc + self.high_cpc) / 2
    
    def get_volume_change(self, months: int = 3) -> float:
        """
        Calcula el cambio de volumen en los últimos N meses
        
        Args:
            months: Número de meses a comparar (3 o 12)
        
        Returns:
            Porcentaje de cambio
        """
        if len(self.monthly_volumes) < months * 2:
            return 0.0
        
        recent = self.monthly_volumes[-months:]
        previous = self.monthly_volumes[-(months*2):-months]
        
        recent_avg = sum(v.get("searches", 0) for v in recent) / len(recent)
        previous_avg = sum(v.get("searches", 0) for v in previous) / len(previous)
        
        if previous_avg == 0:
            return 0.0
        
        return ((recent_avg - previous_avg) / previous_avg) * 100
    
    @property
    def change_3m(self) -> float:
        """Cambio en 3 meses"""
        return self.get_volume_change(3)
    
    @property
    def change_12m(self) -> float:
        """Cambio interanual"""
        return self.get_volume_change(12)


# Mapeo de países a location IDs de Google Ads
LOCATION_IDS = {
    "ES": "2724",   # España
    "PT": "2620",   # Portugal
    "FR": "2250",   # Francia
    "IT": "2380",   # Italia
    "DE": "2276",   # Alemania
    "US": "2840",   # Estados Unidos
    "UK": "2826",   # Reino Unido
    "MX": "2484",   # México
}

# Mapeo de idiomas
LANGUAGE_IDS = {
    "ES": "1003",   # Español
    "PT": "1014",   # Portugués
    "FR": "1002",   # Francés
    "IT": "1004",   # Italiano
    "DE": "1001",   # Alemán
    "EN": "1000",   # Inglés
}


class GoogleAdsKeywordPlanner:
    """
    Cliente para Google Ads Keyword Planner API
    
    Obtiene volúmenes de búsqueda REALES, no estimaciones.
    """
    
    def __init__(self):
        """Inicializa el cliente de Google Ads"""
        self._client = None
        self._customer_id = None
        self._last_error = ""
        self._initialized = False
        
        self._init_client()
    
    def _init_client(self):
        """Inicializa el cliente de Google Ads"""
        try:
            # Verificar que tenemos las credenciales necesarias
            developer_token = st.secrets.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")
            client_id = st.secrets.get("GOOGLE_ADS_CLIENT_ID", "")
            client_secret = st.secrets.get("GOOGLE_ADS_CLIENT_SECRET", "")
            refresh_token = st.secrets.get("GOOGLE_ADS_REFRESH_TOKEN", "")
            customer_id = st.secrets.get("GOOGLE_ADS_CUSTOMER_ID", "")
            
            if not all([developer_token, client_id, client_secret, refresh_token, customer_id]):
                self._last_error = "Faltan credenciales de Google Ads"
                return
            
            # Limpiar customer_id (quitar guiones)
            self._customer_id = customer_id.replace("-", "")
            
            # Importar librería de Google Ads
            from google.ads.googleads.client import GoogleAdsClient
            
            # Crear configuración
            config = {
                "developer_token": developer_token,
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "use_proto_plus": True
            }
            
            self._client = GoogleAdsClient.load_from_dict(config)
            self._initialized = True
            
        except ImportError:
            self._last_error = "google-ads no instalado. Ejecutar: pip install google-ads"
        except Exception as e:
            self._last_error = f"Error inicializando Google Ads: {str(e)}"
    
    @property
    def is_available(self) -> bool:
        """Verifica si el cliente está disponible"""
        return self._initialized and self._client is not None
    
    @property
    def last_error(self) -> str:
        return self._last_error
    
    def get_keyword_volumes(
        self,
        keywords: List[str],
        geo: str = "ES",
        language: str = None
    ) -> Dict[str, KeywordMetrics]:
        """
        Obtiene volúmenes de búsqueda reales para una lista de keywords
        
        Args:
            keywords: Lista de keywords a consultar
            geo: Código de país (ES, PT, FR, IT, DE)
            language: Código de idioma (opcional, se deduce del país)
        
        Returns:
            Dict con keyword -> KeywordMetrics
        """
        if not self.is_available:
            return {}
        
        try:
            # Obtener servicios
            keyword_plan_idea_service = self._client.get_service("KeywordPlanIdeaService")
            googleads_service = self._client.get_service("GoogleAdsService")
            
            # Preparar request
            request = self._client.get_type("GenerateKeywordIdeasRequest")
            request.customer_id = self._customer_id
            
            # Configurar ubicación
            location_id = LOCATION_IDS.get(geo, LOCATION_IDS["ES"])
            request.geo_target_constants.append(
                googleads_service.geo_target_constant_path(location_id)
            )
            
            # Configurar idioma
            lang_code = language or geo
            language_id = LANGUAGE_IDS.get(lang_code, LANGUAGE_IDS["ES"])
            request.language = googleads_service.language_constant_path(language_id)
            
            # Añadir keywords
            request.keyword_seed.keywords.extend(keywords)
            
            # Incluir datos históricos mensuales
            request.historical_metrics_options.include_average_cpc = True
            
            # Ejecutar request
            response = keyword_plan_idea_service.generate_keyword_ideas(request=request)
            
            # Procesar resultados
            results = {}
            
            for idea in response:
                keyword = idea.text
                metrics = idea.keyword_idea_metrics
                
                # Extraer volúmenes mensuales
                monthly_volumes = []
                if metrics.monthly_search_volumes:
                    for vol in metrics.monthly_search_volumes:
                        monthly_volumes.append({
                            "month": vol.month.name if hasattr(vol.month, 'name') else str(vol.month),
                            "year": vol.year,
                            "searches": vol.monthly_searches
                        })
                
                results[keyword] = KeywordMetrics(
                    keyword=keyword,
                    avg_monthly_searches=metrics.avg_monthly_searches or 0,
                    competition=metrics.competition.name if hasattr(metrics.competition, 'name') else "UNKNOWN",
                    competition_index=metrics.competition_index or 0,
                    low_cpc_micros=metrics.low_top_of_page_bid_micros or 0,
                    high_cpc_micros=metrics.high_top_of_page_bid_micros or 0,
                    monthly_volumes=monthly_volumes
                )
            
            return results
            
        except Exception as e:
            self._last_error = f"Error obteniendo volúmenes: {str(e)}"
            return {}
    
    def get_single_keyword_volume(
        self,
        keyword: str,
        geo: str = "ES"
    ) -> Optional[KeywordMetrics]:
        """
        Obtiene volumen para una sola keyword
        
        Args:
            keyword: Keyword a consultar
            geo: Código de país
        
        Returns:
            KeywordMetrics o None si hay error
        """
        results = self.get_keyword_volumes([keyword], geo)
        
        # La API puede devolver la keyword normalizada
        if keyword in results:
            return results[keyword]
        
        # Buscar por coincidencia parcial
        keyword_lower = keyword.lower()
        for k, v in results.items():
            if k.lower() == keyword_lower:
                return v
        
        # Devolver el primer resultado si existe
        if results:
            return list(results.values())[0]
        
        return None
    
    def enrich_related_queries(
        self,
        queries: List[Dict],
        geo: str = "ES"
    ) -> List[Dict]:
        """
        Enriquece una lista de related queries con volúmenes reales
        
        Args:
            queries: Lista de queries (con 'query' key)
            geo: Código de país
        
        Returns:
            Lista enriquecida con 'real_volume', 'change_3m', 'change_12m'
        """
        if not queries or not self.is_available:
            return queries
        
        # Extraer keywords
        keywords = [q.get("query", "") for q in queries if q.get("query")]
        
        if not keywords:
            return queries
        
        # Obtener volúmenes (máximo 200 por llamada)
        volumes = {}
        for i in range(0, len(keywords), 200):
            batch = keywords[i:i+200]
            batch_volumes = self.get_keyword_volumes(batch, geo)
            volumes.update(batch_volumes)
        
        # Enriquecer queries
        enriched = []
        for q in queries:
            query_text = q.get("query", "").lower()
            
            # Buscar en resultados
            metrics = None
            for k, v in volumes.items():
                if k.lower() == query_text:
                    metrics = v
                    break
            
            enriched_query = q.copy()
            
            if metrics:
                enriched_query["real_volume"] = metrics.avg_monthly_searches
                enriched_query["change_3m"] = metrics.change_3m
                enriched_query["change_12m"] = metrics.change_12m
                enriched_query["competition"] = metrics.competition
                enriched_query["cpc"] = metrics.avg_cpc
            else:
                enriched_query["real_volume"] = None
                enriched_query["change_3m"] = None
                enriched_query["change_12m"] = None
            
            enriched.append(enriched_query)
        
        return enriched


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

_google_ads_instance = None

def get_google_ads() -> Optional[GoogleAdsKeywordPlanner]:
    """Obtiene instancia singleton de Google Ads"""
    global _google_ads_instance
    
    if _google_ads_instance is None:
        _google_ads_instance = GoogleAdsKeywordPlanner()
    
    return _google_ads_instance if _google_ads_instance.is_available else None


def check_google_ads_config() -> Dict[str, Any]:
    """Verifica la configuración de Google Ads"""
    return {
        "has_developer_token": bool(st.secrets.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")),
        "has_client_id": bool(st.secrets.get("GOOGLE_ADS_CLIENT_ID", "")),
        "has_client_secret": bool(st.secrets.get("GOOGLE_ADS_CLIENT_SECRET", "")),
        "has_refresh_token": bool(st.secrets.get("GOOGLE_ADS_REFRESH_TOKEN", "")),
        "has_customer_id": bool(st.secrets.get("GOOGLE_ADS_CUSTOMER_ID", "")),
        "configured": all([
            st.secrets.get("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
            st.secrets.get("GOOGLE_ADS_CLIENT_ID", ""),
            st.secrets.get("GOOGLE_ADS_CLIENT_SECRET", ""),
            st.secrets.get("GOOGLE_ADS_REFRESH_TOKEN", ""),
            st.secrets.get("GOOGLE_ADS_CUSTOMER_ID", "")
        ])
    }


def format_volume(volume: int) -> str:
    """Formatea volumen de búsqueda para mostrar"""
    if volume is None:
        return "—"
    if volume >= 1_000_000:
        return f"{volume/1_000_000:.1f}M"
    if volume >= 1_000:
        return f"{volume/1_000:.1f}K"
    return str(volume)


def format_change(change: float) -> str:
    """Formatea cambio porcentual"""
    if change is None:
        return "—"
    sign = "+" if change > 0 else ""
    return f"{sign}{change:.1f}%"


def render_volume_badge(volume: int, change: float = None) -> str:
    """
    Renderiza badge HTML con volumen y cambio
    
    Args:
        volume: Volumen de búsqueda
        change: Cambio porcentual (opcional)
    
    Returns:
        HTML string
    """
    vol_str = format_volume(volume)
    
    if change is not None:
        if change > 10:
            color = "#10B981"
            arrow = "↑"
        elif change < -10:
            color = "#EF4444"
            arrow = "↓"
        else:
            color = "#6B7280"
            arrow = "→"
        
        change_str = f'<span style="color: {color}; font-size: 0.8em;"> {arrow}{abs(change):.0f}%</span>'
    else:
        change_str = ""
    
    return f'<span style="font-weight: 600;">{vol_str}</span>{change_str}'
