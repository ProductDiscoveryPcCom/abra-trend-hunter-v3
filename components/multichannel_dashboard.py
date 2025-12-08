"""
Dashboard Multi-Canal
Visualización modular de datos por fuente y agregada

Permite ver cada canal de datos por separado:
- Google Trends
- YouTube  
- Google News
- People Also Ask
- Shopping
- Related Queries

Y luego ver una vista agregada/comparativa
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import html as html_module


@dataclass
class ChannelData:
    """Datos de un canal específico"""
    name: str
    icon: str
    color: str
    enabled: bool = False
    
    # Métricas principales
    score: float = 0  # Score normalizado 0-100
    trend: str = ""  # "up", "down", "stable"
    
    # Datos crudos (varían por canal)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    # Insights específicos del canal
    insights: List[str] = field(default_factory=list)
    
    # Timestamp de última actualización
    updated_at: Optional[datetime] = None


@dataclass
class MultiChannelAnalysis:
    """Análisis multi-canal completo"""
    keyword: str
    channels: Dict[str, ChannelData] = field(default_factory=dict)
    
    # Score agregado
    overall_score: float = 0
    overall_trend: str = ""
    
    # Insights combinados
    combined_insights: List[str] = field(default_factory=list)
    
    def add_channel(self, channel: ChannelData):
        self.channels[channel.name] = channel
        self._recalculate_overall()
    
    def _recalculate_overall(self):
        """Recalcula el score agregado"""
        enabled = [c for c in self.channels.values() if c.enabled and c.score > 0]
        if enabled:
            self.overall_score = sum(c.score for c in enabled) / len(enabled)
            
            # Tendencia agregada
            ups = sum(1 for c in enabled if c.trend == "up")
            downs = sum(1 for c in enabled if c.trend == "down")
            if ups > downs:
                self.overall_trend = "up"
            elif downs > ups:
                self.overall_trend = "down"
            else:
                self.overall_trend = "stable"


class MultiChannelDashboard:
    """
    Dashboard para visualizar datos por canal y agregados.
    """
    
    # Configuración de canales
    CHANNELS = {
        "trends": {"name": "Google Trends", "icon": "📈", "color": "#4285F4"},
        "youtube": {"name": "YouTube", "icon": "📺", "color": "#FF0000"},
        "news": {"name": "Google News", "icon": "📰", "color": "#34A853"},
        "paa": {"name": "People Also Ask", "icon": "❓", "color": "#FBBC05"},
        "shopping": {"name": "Shopping", "icon": "🛒", "color": "#EA4335"},
        "related": {"name": "Related Queries", "icon": "🔗", "color": "#9333EA"},
        "perplexity": {"name": "Market Intel", "icon": "🧠", "color": "#6366F1"}
    }
    
    def __init__(self):
        self.analysis = None
    
    def create_analysis(self, keyword: str) -> MultiChannelAnalysis:
        """Crea un nuevo análisis multi-canal"""
        self.analysis = MultiChannelAnalysis(keyword=keyword)
        return self.analysis
    
    def add_trends_data(
        self,
        timeline_data: List[Dict],
        growth: float,
        current_volume: int,
        seasonality: Dict = None
    ):
        """Añade datos de Google Trends"""
        channel = ChannelData(
            name="trends",
            icon="📈",
            color="#4285F4",
            enabled=True
        )
        
        # Calcular score (0-100 basado en volumen y crecimiento)
        volume_score = min(current_volume, 100)
        growth_score = min(max(growth + 50, 0), 100)  # Normalizar crecimiento
        channel.score = (volume_score * 0.6 + growth_score * 0.4)
        
        # Tendencia
        if growth > 10:
            channel.trend = "up"
        elif growth < -10:
            channel.trend = "down"
        else:
            channel.trend = "stable"
        
        # Datos crudos
        channel.raw_data = {
            "timeline": timeline_data,
            "growth": growth,
            "current_volume": current_volume,
            "seasonality": seasonality or {}
        }
        
        # Insights
        if growth > 50:
            channel.insights.append(f"🚀 Crecimiento explosivo: +{growth:.0f}%")
        elif growth > 20:
            channel.insights.append(f"📈 Tendencia alcista: +{growth:.0f}%")
        elif growth < -20:
            channel.insights.append(f"📉 Tendencia bajista: {growth:.0f}%")
        
        if seasonality and seasonality.get("has_seasonality"):
            peak = seasonality.get("peak_month", "")
            channel.insights.append(f"📅 Estacionalidad detectada (pico: {peak})")
        
        self.analysis.add_channel(channel)
    
    def add_youtube_data(
        self,
        total_videos: int,
        total_views: int,
        avg_views: float,
        recent_videos: int,
        hype_score: float,
        language_distribution: Dict[str, int] = None
    ):
        """Añade datos de YouTube"""
        channel = ChannelData(
            name="youtube",
            icon="📺",
            color="#FF0000",
            enabled=True
        )
        
        # Score basado en hype_score (ya normalizado 0-100)
        channel.score = hype_score
        
        # Tendencia basada en ratio de videos recientes
        if total_videos > 0:
            recent_ratio = recent_videos / total_videos
            if recent_ratio > 0.3:
                channel.trend = "up"
            elif recent_ratio < 0.1:
                channel.trend = "down"
            else:
                channel.trend = "stable"
        
        channel.raw_data = {
            "total_videos": total_videos,
            "total_views": total_views,
            "avg_views": avg_views,
            "recent_videos": recent_videos,
            "hype_score": hype_score,
            "languages": language_distribution or {}
        }
        
        # Insights
        if hype_score >= 80:
            channel.insights.append("🔥 Hype muy alto en YouTube")
        elif hype_score >= 60:
            channel.insights.append("📺 Buena presencia en YouTube")
        
        if recent_videos > 10:
            channel.insights.append(f"📹 {recent_videos} videos recientes (alta actividad)")
        
        if language_distribution:
            top_lang = max(language_distribution.items(), key=lambda x: x[1])[0]
            channel.insights.append(f"🌍 Contenido principalmente en {top_lang}")
        
        self.analysis.add_channel(channel)
    
    def add_news_data(
        self,
        total_articles: int,
        sentiment: str,
        recent_topics: List[str] = None,
        sentiment_breakdown: Dict[str, int] = None
    ):
        """Añade datos de Google News"""
        channel = ChannelData(
            name="news",
            icon="📰",
            color="#34A853",
            enabled=True
        )
        
        # Score basado en cantidad de noticias y sentimiento
        quantity_score = min(total_articles * 5, 50)
        sentiment_scores = {"positive": 50, "neutral": 30, "negative": 10}
        sentiment_score = sentiment_scores.get(sentiment.lower(), 30)
        channel.score = quantity_score + sentiment_score
        
        # Tendencia basada en sentimiento
        if sentiment.lower() == "positive":
            channel.trend = "up"
        elif sentiment.lower() == "negative":
            channel.trend = "down"
        else:
            channel.trend = "stable"
        
        channel.raw_data = {
            "total_articles": total_articles,
            "sentiment": sentiment,
            "topics": recent_topics or [],
            "sentiment_breakdown": sentiment_breakdown or {}
        }
        
        # Insights
        sentiment_icons = {"positive": "😊", "neutral": "😐", "negative": "😟"}
        icon = sentiment_icons.get(sentiment.lower(), "📰")
        channel.insights.append(f"{icon} Sentimiento: {sentiment}")
        
        if total_articles > 10:
            channel.insights.append(f"📰 Alta cobertura mediática ({total_articles} artículos)")
        elif total_articles > 0:
            channel.insights.append(f"📰 Cobertura moderada ({total_articles} artículos)")
        
        self.analysis.add_channel(channel)
    
    def add_paa_data(
        self,
        total_questions: int,
        question_categories: Dict[str, int] = None,
        top_questions: List[str] = None
    ):
        """Añade datos de People Also Ask"""
        channel = ChannelData(
            name="paa",
            icon="❓",
            color="#FBBC05",
            enabled=True
        )
        
        # Score basado en cantidad y variedad de preguntas
        channel.score = min(total_questions * 8, 100)
        channel.trend = "stable"  # PAA no tiene tendencia temporal
        
        channel.raw_data = {
            "total_questions": total_questions,
            "categories": question_categories or {},
            "top_questions": top_questions or []
        }
        
        # Insights
        if question_categories:
            if question_categories.get("compra", 0) > 3:
                channel.insights.append("💰 Alta intención de compra detectada")
                channel.trend = "up"
            if question_categories.get("comparativa", 0) > 2:
                channel.insights.append("⚖️ Muchas comparativas (producto maduro)")
        
        if total_questions > 10:
            channel.insights.append(f"❓ {total_questions} preguntas frecuentes")
        
        self.analysis.add_channel(channel)
    
    def add_shopping_data(
        self,
        total_products: int,
        avg_price: float,
        price_range: tuple,
        retailers: List[str] = None,
        avg_rating: float = None
    ):
        """Añade datos de Shopping"""
        channel = ChannelData(
            name="shopping",
            icon="🛒",
            color="#EA4335",
            enabled=True
        )
        
        # Score basado en disponibilidad y diversidad
        channel.score = min(total_products * 5 + len(retailers or []) * 10, 100)
        channel.trend = "stable"
        
        channel.raw_data = {
            "total_products": total_products,
            "avg_price": avg_price,
            "price_range": price_range,
            "retailers": retailers or [],
            "avg_rating": avg_rating
        }
        
        # Insights
        if total_products > 20:
            channel.insights.append("🛒 Alta disponibilidad en retail")
        
        if avg_rating and avg_rating >= 4.5:
            channel.insights.append(f"⭐ Excelentes valoraciones ({avg_rating:.1f})")
        
        if price_range:
            channel.insights.append(f"💰 Rango: {price_range[0]:.0f}€ - {price_range[1]:.0f}€")
        
        self.analysis.add_channel(channel)
    
    def add_related_data(
        self,
        rising_queries: List[Dict],
        top_queries: List[Dict],
        breakout_count: int = 0
    ):
        """Añade datos de Related Queries"""
        channel = ChannelData(
            name="related",
            icon="🔗",
            color="#9333EA",
            enabled=True
        )
        
        # Score basado en queries rising y breakouts
        channel.score = min(len(rising_queries) * 10 + breakout_count * 20, 100)
        
        if breakout_count > 0:
            channel.trend = "up"
        elif len(rising_queries) > 5:
            channel.trend = "up"
        else:
            channel.trend = "stable"
        
        channel.raw_data = {
            "rising": rising_queries,
            "top": top_queries,
            "breakout_count": breakout_count
        }
        
        # Insights
        if breakout_count > 0:
            channel.insights.append(f"🚀 {breakout_count} queries en breakout!")
        
        if len(rising_queries) > 5:
            channel.insights.append(f"📈 {len(rising_queries)} queries en crecimiento")
        
        self.analysis.add_channel(channel)
    
    def add_perplexity_data(
        self,
        market_trend: str,
        sentiment: str,
        lifecycle_stage: str,
        opportunities: List[str] = None,
        risks: List[str] = None
    ):
        """Añade datos de Perplexity/Market Intelligence"""
        channel = ChannelData(
            name="perplexity",
            icon="🧠",
            color="#6366F1",
            enabled=True
        )
        
        # Score basado en análisis
        trend_scores = {"crecimiento": 80, "estable": 50, "declive": 20}
        sentiment_scores = {"positive": 20, "neutral": 10, "negative": 0}
        channel.score = (
            trend_scores.get(market_trend.lower(), 50) +
            sentiment_scores.get(sentiment.lower(), 10)
        )
        
        if market_trend.lower() == "crecimiento":
            channel.trend = "up"
        elif market_trend.lower() == "declive":
            channel.trend = "down"
        else:
            channel.trend = "stable"
        
        channel.raw_data = {
            "market_trend": market_trend,
            "sentiment": sentiment,
            "lifecycle": lifecycle_stage,
            "opportunities": opportunities or [],
            "risks": risks or []
        }
        
        # Insights
        channel.insights.append(f"📊 Tendencia de mercado: {market_trend}")
        channel.insights.append(f"🔄 Ciclo de vida: {lifecycle_stage}")
        
        if opportunities:
            channel.insights.append(f"💡 {len(opportunities)} oportunidades identificadas")
        if risks:
            channel.insights.append(f"⚠️ {len(risks)} riesgos detectados")
        
        self.analysis.add_channel(channel)


# =============================================================================
# FUNCIONES DE RENDERIZADO
# =============================================================================

def render_channel_selector() -> List[str]:
    """Renderiza selector de canales a mostrar"""
    st.markdown("#### 📊 Canales de Datos")
    
    all_channels = MultiChannelDashboard.CHANNELS
    
    cols = st.columns(len(all_channels))
    selected = []
    
    for i, (key, config) in enumerate(all_channels.items()):
        with cols[i]:
            if st.checkbox(
                f"{config['icon']}", 
                value=True, 
                key=f"channel_{key}",
                help=config['name']
            ):
                selected.append(key)
    
    return selected


def render_channel_cards(analysis: MultiChannelAnalysis, selected_channels: List[str] = None):
    """Renderiza tarjetas resumen por canal"""
    
    if not analysis or not analysis.channels:
        st.info("No hay datos de canales disponibles")
        return
    
    channels_to_show = selected_channels or list(analysis.channels.keys())
    enabled_channels = [
        analysis.channels[k] for k in channels_to_show 
        if k in analysis.channels and analysis.channels[k].enabled
    ]
    
    if not enabled_channels:
        st.info("No hay canales activos")
        return
    
    # Tarjetas en grid
    cols = st.columns(min(4, len(enabled_channels)))
    
    for i, channel in enumerate(enabled_channels):
        with cols[i % 4]:
            trend_icon = {"up": "📈", "down": "📉", "stable": "➡️"}.get(channel.trend, "")
            
            # Color de borde basado en score
            if channel.score >= 70:
                border_color = "#10B981"
            elif channel.score >= 40:
                border_color = "#F59E0B"
            else:
                border_color = "#EF4444"
            
            st.markdown(f"""
            <div style="
                background: white;
                border: 2px solid {border_color};
                border-radius: 12px;
                padding: 16px;
                text-align: center;
                margin-bottom: 12px;
            ">
                <div style="font-size: 2rem;">{channel.icon}</div>
                <div style="font-weight: 600; color: #374151; margin: 8px 0;">
                    {MultiChannelDashboard.CHANNELS.get(channel.name, {}).get('name', channel.name)}
                </div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {channel.color};">
                    {channel.score:.0f} {trend_icon}
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_channel_detail(channel: ChannelData):
    """Renderiza detalle de un canal específico"""
    
    config = MultiChannelDashboard.CHANNELS.get(channel.name, {})
    
    st.markdown(f"### {channel.icon} {config.get('name', channel.name)}")
    
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        trend_icon = {"up": "📈", "down": "📉", "stable": "➡️"}.get(channel.trend, "")
        st.metric("Score", f"{channel.score:.0f}/100", trend_icon)
    
    # Insights
    st.markdown("#### 💡 Insights")
    for insight in channel.insights:
        st.info(insight)
    
    # Datos específicos del canal
    if channel.raw_data:
        with st.expander("📋 Datos Detallados"):
            st.json(channel.raw_data)


def render_aggregate_chart(analysis: MultiChannelAnalysis):
    """Renderiza gráfico agregado de todos los canales"""
    
    if not analysis or not analysis.channels:
        return
    
    enabled = [c for c in analysis.channels.values() if c.enabled]
    if not enabled:
        return
    
    # Gráfico radar
    categories = [MultiChannelDashboard.CHANNELS.get(c.name, {}).get('name', c.name) for c in enabled]
    values = [c.score for c in enabled]
    colors = [c.color for c in enabled]
    
    fig = go.Figure()
    
    # Valores + cerrar el polígono
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]
    
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(99, 102, 241, 0.2)',
        line=dict(color='#6366F1', width=2),
        name='Score por Canal'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        height=400,
        title="Análisis Multi-Canal"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_trend_comparison(analysis: MultiChannelAnalysis):
    """Renderiza comparación de tendencias entre canales"""
    
    if not analysis or not analysis.channels:
        return
    
    enabled = [c for c in analysis.channels.values() if c.enabled]
    if not enabled:
        return
    
    # Gráfico de barras horizontal
    names = [MultiChannelDashboard.CHANNELS.get(c.name, {}).get('name', c.name) for c in enabled]
    scores = [c.score for c in enabled]
    colors = [c.color for c in enabled]
    trends = [c.trend for c in enabled]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=names,
        x=scores,
        orientation='h',
        marker_color=colors,
        text=[f"{s:.0f}" for s in scores],
        textposition='inside',
        hovertemplate='%{y}: %{x:.0f}<extra></extra>'
    ))
    
    # Añadir indicadores de tendencia
    for i, (name, score, trend) in enumerate(zip(names, scores, trends)):
        trend_symbol = {"up": "▲", "down": "▼", "stable": "●"}.get(trend, "")
        trend_color = {"up": "#10B981", "down": "#EF4444", "stable": "#9CA3AF"}.get(trend, "#9CA3AF")
        
        fig.add_annotation(
            x=score + 5,
            y=i,
            text=trend_symbol,
            showarrow=False,
            font=dict(size=16, color=trend_color)
        )
    
    fig.update_layout(
        xaxis=dict(range=[0, 110], title="Score"),
        yaxis=dict(title=""),
        height=50 * len(enabled) + 100,
        margin=dict(l=20, r=20, t=40, b=40),
        title="Comparación de Canales"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_combined_insights(analysis: MultiChannelAnalysis):
    """Renderiza insights combinados de todos los canales"""
    
    if not analysis or not analysis.channels:
        return
    
    st.markdown("### 💡 Insights Combinados")
    
    all_insights = []
    for channel in analysis.channels.values():
        if channel.enabled:
            for insight in channel.insights:
                all_insights.append({
                    "channel": channel.name,
                    "icon": channel.icon,
                    "color": channel.color,
                    "text": insight
                })
    
    if not all_insights:
        st.info("No hay insights disponibles")
        return
    
    # Agrupar por tipo de insight (positivo, negativo, neutro)
    positive_keywords = ["🚀", "📈", "🔥", "⭐", "💰", "💡"]
    negative_keywords = ["📉", "⚠️", "😟"]
    
    for insight in all_insights:
        is_positive = any(k in insight["text"] for k in positive_keywords)
        is_negative = any(k in insight["text"] for k in negative_keywords)
        
        if is_positive:
            bg_color = f"{insight['color']}15"
            border_color = insight['color']
        elif is_negative:
            bg_color = "#FEE2E2"
            border_color = "#EF4444"
        else:
            bg_color = "#F3F4F6"
            border_color = "#9CA3AF"
        
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            background: {bg_color};
            border-left: 4px solid {border_color};
            border-radius: 8px;
            margin-bottom: 8px;
        ">
            <span style="font-size: 1.2rem;">{insight['icon']}</span>
            <span style="color: #374151;">{html_module.escape(insight['text'])}</span>
        </div>
        """, unsafe_allow_html=True)


def render_multichannel_dashboard(analysis: MultiChannelAnalysis):
    """Renderiza el dashboard multi-canal completo"""
    
    if not analysis:
        st.info("No hay análisis disponible")
        return
    
    st.markdown(f"## 📊 Dashboard Multi-Canal: {html_module.escape(analysis.keyword)}")
    
    # Score general
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        trend_icon = {"up": "📈", "down": "📉", "stable": "➡️"}.get(analysis.overall_trend, "")
        
        if analysis.overall_score >= 70:
            color = "#10B981"
            label = "Excelente"
        elif analysis.overall_score >= 50:
            color = "#F59E0B"
            label = "Bueno"
        else:
            color = "#EF4444"
            label = "Bajo"
        
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 30px;
            background: {color}15;
            border: 3px solid {color};
            border-radius: 20px;
            margin-bottom: 30px;
        ">
            <div style="font-size: 0.9rem; color: #6B7280; margin-bottom: 8px;">
                SCORE GENERAL
            </div>
            <div style="font-size: 3rem; font-weight: 700; color: {color};">
                {analysis.overall_score:.0f} {trend_icon}
            </div>
            <div style="font-size: 1.1rem; color: {color}; font-weight: 600;">
                {label}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Tabs para vistas
    tab_overview, tab_channels, tab_compare, tab_insights = st.tabs([
        "📊 Resumen",
        "📡 Por Canal",
        "⚖️ Comparar",
        "💡 Insights"
    ])
    
    with tab_overview:
        render_channel_cards(analysis)
        st.markdown("---")
        render_aggregate_chart(analysis)
    
    with tab_channels:
        # Selector de canal
        channel_names = [
            MultiChannelDashboard.CHANNELS.get(k, {}).get('name', k)
            for k in analysis.channels.keys()
            if analysis.channels[k].enabled
        ]
        
        if channel_names:
            selected_name = st.selectbox("Seleccionar canal", channel_names)
            
            # Encontrar el canal seleccionado
            for key, channel in analysis.channels.items():
                if MultiChannelDashboard.CHANNELS.get(key, {}).get('name', key) == selected_name:
                    render_channel_detail(channel)
                    break
    
    with tab_compare:
        render_trend_comparison(analysis)
    
    with tab_insights:
        render_combined_insights(analysis)
