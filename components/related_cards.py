"""
Related Cards Component
Cards para queries relacionadas, topics y tendencias con sparklines
Incluye volúmenes de búsqueda reales de Google Ads si están disponibles
"""

import streamlit as st
import plotly.graph_objects as go
from typing import List, Optional


def format_volume(volume: int) -> str:
    """Formatea volumen de búsqueda"""
    if volume is None:
        return "—"
    if volume >= 1_000_000:
        return f"{volume/1_000_000:.1f}M"
    if volume >= 1_000:
        return f"{volume/1_000:.1f}K"
    return str(volume)


def format_change(change: float) -> str:
    """Formatea cambio porcentual con color"""
    if change is None:
        return "—"
    sign = "+" if change > 0 else ""
    return f"{sign}{change:.0f}%"


def render_related_queries(
    queries: dict,
    show_type: str = "rising",
    country: str = "ES",
    has_real_volumes: bool = False
) -> None:
    """
    Renderiza la sección de Related Queries

    Args:
        queries: Dict con 'rising' y 'top' lists
        show_type: 'rising' o 'top'
        country: Código de país (ES, PT, FR, etc.)
        has_real_volumes: Si los datos incluyen volúmenes reales de Google Ads
    """
    country_names = {"ES": "España", "PT": "Portugal", "FR": "Francia", "IT": "Italia", "DE": "Alemania"}
    country_name = country_names.get(country, country)

    st.markdown(f"#### 🔍 Búsquedas relacionadas ({country_name})")

    # Info sobre indicadores
    with st.expander("ℹ️ ¿Qué significan los indicadores?"):
        indicators_info = """
        - **🚀 Breakout (XX)**: Crecimiento explosivo (+5000% o más). El número XX es el **Breakout Score** (0-100):
          - **80-100**: Breakout muy fuerte, alta prioridad
          - **60-79**: Breakout notable, prioridad media-alta
          - **40-59**: Breakout moderado, monitorizar
        - **↗ +X%**: Porcentaje de crecimiento respecto al periodo anterior.
        - **📊 Top**: Las búsquedas más populares en volumen absoluto.
        """
        
        if has_real_volumes:
            indicators_info += """
        
        **📊 Datos de Google Ads:**
        - **Vol.**: Volumen de búsquedas mensuales REAL
        - **3M Δ**: Cambio en los últimos 3 meses
        - **YoY Δ**: Cambio interanual (año sobre año)
        """
        
        st.markdown(indicators_info)
        
        if has_real_volumes:
            st.success("✅ Volúmenes REALES de Google Ads disponibles")
        else:
            st.info("💡 Configura Google Ads API para ver volúmenes reales")

    # Tabs para Rising/Top
    tab1, tab2 = st.tabs(["📈 En aumento", "🏆 Más buscados"])

    with tab1:
        _render_query_list(queries.get("rising", []), is_rising=True, has_real_volumes=has_real_volumes)

    with tab2:
        _render_query_list(queries.get("top", []), is_rising=False, has_real_volumes=has_real_volumes)


def render_related_topics(
    topics: dict,
    show_type: str = "rising",
    has_real_volumes: bool = False
) -> None:
    """
    Renderiza la sección de Related Topics

    Args:
        topics: Dict con 'rising' y 'top' lists
        has_real_volumes: Si hay volúmenes reales disponibles
    """
    st.markdown("#### 📑 Related Topics")

    tab1, tab2 = st.tabs(["📈 Rising", "🏆 Top"])

    with tab1:
        _render_topic_list(topics.get("rising", []), is_rising=True, has_real_volumes=has_real_volumes)

    with tab2:
        _render_topic_list(topics.get("top", []), is_rising=False, has_real_volumes=has_real_volumes)


def _render_query_list(queries: list, is_rising: bool = True, has_real_volumes: bool = False) -> None:
    """Renderiza lista de queries con columnas de volumen si están disponibles"""
    if not queries:
        st.info("No hay datos disponibles")
        return
    
    # Determinar si hay datos de volumen real
    sample_query = queries[0] if queries else {}
    show_volumes = has_real_volumes and sample_query.get("real_volume") is not None

    # Cabecera si hay volúmenes
    if show_volumes:
        cols = st.columns([3, 1, 1, 1, 1])
        with cols[0]:
            st.markdown("**Query**")
        with cols[1]:
            st.markdown("**Trend**")
        with cols[2]:
            st.markdown("**Vol.**")
        with cols[3]:
            st.markdown("**3M Δ**")
        with cols[4]:
            st.markdown("**YoY Δ**")
        st.markdown("---")

    for i, query in enumerate(queries[:15]):  # Mostrar hasta 15
        query_text = query.get("query", "")
        
        if show_volumes:
            cols = st.columns([3, 1, 1, 1, 1])
        else:
            cols = st.columns([4, 1])

        with cols[0]:
            st.markdown(f"{i+1}. **{query_text}**")

        with cols[1]:
            if is_rising:
                extracted = query.get("extracted_value", 0)
                breakout_score = query.get("breakout_score")
                
                if extracted == "Breakout" or (isinstance(extracted, int) and extracted > 5000):
                    if breakout_score is not None:
                        st.markdown(f"🚀 **{breakout_score}**")
                    else:
                        st.markdown("🚀 **Breakout**")
                elif isinstance(extracted, int) and extracted > 0:
                    st.success(f"↗ +{extracted}%")
                elif isinstance(extracted, int) and extracted < 0:
                    st.error(f"↘ {extracted}%")
                else:
                    st.info("↗ Rising")
            else:
                value = query.get("value", 0)
                st.caption(f"📊 {value}")
        
        # Columnas de volumen de Google Ads (si disponibles)
        if show_volumes:
            with cols[2]:
                vol = query.get("real_volume")
                st.markdown(f"**{format_volume(vol)}**" if vol else "—")
            
            with cols[3]:
                change_3m = query.get("change_3m")
                if change_3m is not None:
                    color = "green" if change_3m > 0 else "red" if change_3m < 0 else "gray"
                    st.markdown(f":{color}[{format_change(change_3m)}]")
                else:
                    st.markdown("—")
            
            with cols[4]:
                change_12m = query.get("change_12m")
                if change_12m is not None:
                    color = "green" if change_12m > 0 else "red" if change_12m < 0 else "gray"
                    st.markdown(f":{color}[{format_change(change_12m)}]")
                else:
                    st.markdown("—")


def _render_topic_list(topics: list, is_rising: bool = True) -> None:
    """Renderiza lista de topics"""
    if not topics:
        st.info("No hay datos disponibles")
        return

    for i, topic in enumerate(topics[:15]):  # Mostrar hasta 15
        topic_info = topic.get("topic", {})
        title = topic_info.get("title", "Unknown")
        topic_type = topic_info.get("type", "")

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown(f"{i+1}. **{title}**")

        with col2:
            if topic_type:
                st.caption(f"📌 {topic_type}")

        with col3:
            if is_rising:
                extracted = topic.get("extracted_value", 0)
                breakout_score = topic.get("breakout_score")
                
                if extracted == "Breakout" or (isinstance(extracted, int) and extracted > 5000):
                    # Mostrar breakout con score si existe
                    if breakout_score is not None:
                        st.markdown(f"🚀 **{breakout_score}**")
                    else:
                        st.markdown("🚀 **Breakout**")
                elif isinstance(extracted, int) and extracted > 0:
                    st.success(f"↗ +{extracted}%")
                elif isinstance(extracted, int) and extracted < 0:
                    st.error(f"↘ {extracted}%")
                else:
                    st.info("↗ Rising")
            else:
                value = topic.get("value", 0)
                st.caption(f"📊 {value}")


def render_trend_cards(
    trends: list,
    title: str = "Tendencias Relacionadas"
) -> None:
    """
    Renderiza cards de tendencias con mini sparklines

    Args:
        trends: Lista de tendencias con name y values
    """
    st.markdown(f"#### 📊 {title}")

    if not trends:
        st.info("No hay tendencias relacionadas disponibles")
        return

    # Mostrar en grid de 4 columnas
    cols = st.columns(4)

    for i, trend in enumerate(trends[:8]):
        with cols[i % 4]:
            _render_single_trend_card(trend)

    if len(trends) > 8:
        st.markdown(
            f'<a href="#" style="color: #7C3AED; text-decoration: none; font-size: 0.875rem;">'
            f'Ver todas las {len(trends)} tendencias relacionadas →</a>',
            unsafe_allow_html=True
        )


def _render_single_trend_card(trend: dict) -> None:
    """Renderiza una card individual de tendencia"""
    name = trend.get("name", trend.get("query", "Unknown"))
    values = trend.get("values", [])

    # Determinar tendencia
    if values and len(values) >= 2:
        if values[-1] > values[0]:
            trend_icon = "📈"
            trend_color = "#10B981"
        elif values[-1] < values[0]:
            trend_icon = "📉"
            trend_color = "#EF4444"
        else:
            trend_icon = "➡️"
            trend_color = "#6B7280"
    else:
        trend_icon = "📊"
        trend_color = "#6B7280"
        values = [50, 52, 48, 55, 60, 58, 62]  # Datos dummy

    # Crear mini sparkline
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=values,
        mode='lines',
        line=dict(color=trend_color, width=2),
        fill='tozeroy',
        fillcolor=f'{trend_color}15',
        hoverinfo='skip'
    ))

    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
        height=40,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    # Card
    st.markdown(
        f'''
        <div style="background: white; border: 1px solid #E5E7EB; border-radius: 8px;
        padding: 12px; margin-bottom: 12px; transition: all 0.2s;"
        onmouseover="this.style.borderColor='#F5C518'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)';"
        onmouseout="this.style.borderColor='#E5E7EB'; this.style.boxShadow='none';">
            <div style="font-size: 0.875rem; font-weight: 500; color: #1A1A2E;
            margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                {name}
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    st.plotly_chart(fig, width="stretch", key=f"spark_{name[:20]}")


def render_competitor_brands(brands: list) -> None:
    """
    Renderiza cards de marcas competidoras identificadas
    """
    if not brands:
        return

    st.markdown("#### 🏷️ Marcas Relacionadas")

    cols = st.columns(min(4, len(brands)))

    for i, brand in enumerate(brands[:4]):
        with cols[i]:
            name = brand.get("name", "")
            brand_type = brand.get("type", "")
            growth = brand.get("growth", "")

            st.markdown(
                f'''
                <div style="background: linear-gradient(135deg, rgba(245,197,24,0.06), rgba(124,58,237,0.06));
                border: 1px solid #E5E7EB; border-radius: 8px; padding: 16px; text-align: center;">
                    <div style="font-size: 1rem; font-weight: 600; color: #1A1A2E;
                    margin-bottom: 4px;">{name}</div>
                    <div style="font-size: 0.75rem; color: #6B7280; margin-bottom: 8px;">
                        {brand_type}
                    </div>
                    <div style="font-size: 0.8rem; color: #10B981; font-weight: 500;">
                        {growth}
                    </div>
                </div>
                ''',
                unsafe_allow_html=True
            )

