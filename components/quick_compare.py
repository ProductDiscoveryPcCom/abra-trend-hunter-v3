"""
Quick Compare Component
Comparador rápido de keywords en el sidebar
"""

import streamlit as st
import plotly.graph_objects as go
from typing import List, Dict, Optional


def render_quick_compare(
    trends_module,
    geo: str = "ES",
    timeframe: str = "today 12-m"
) -> Optional[Dict]:
    """
    Renderiza un comparador rápido de 2-3 keywords
    
    Args:
        trends_module: Módulo de Google Trends inicializado
        geo: Código de país
        timeframe: Período de tiempo
    
    Returns:
        Dict con datos de comparación o None
    """
    st.markdown("#### ⚡ Comparar Rápido")
    
    col1, col2 = st.columns(2)
    
    with col1:
        kw1 = st.text_input(
            "Keyword 1",
            placeholder="Ej: Beelink",
            key="quick_cmp_1",
            max_chars=50
        )
    
    with col2:
        kw2 = st.text_input(
            "Keyword 2", 
            placeholder="Ej: Minisforum",
            key="quick_cmp_2",
            max_chars=50
        )
    
    kw3 = st.text_input(
        "Keyword 3 (opcional)",
        placeholder="Ej: Geekom",
        key="quick_cmp_3",
        max_chars=50
    )
    
    if st.button("🔍 Comparar", key="btn_quick_compare", use_container_width=True):
        keywords = [k.strip() for k in [kw1, kw2, kw3] if k and k.strip()]
        
        if len(keywords) < 2:
            st.warning("Introduce al menos 2 keywords")
            return None
        
        with st.spinner("Comparando..."):
            try:
                # Obtener datos de comparación
                comparison_data = _fetch_comparison(
                    trends_module, 
                    keywords, 
                    geo, 
                    timeframe
                )
                
                if comparison_data:
                    # Renderizar mini chart
                    _render_comparison_sparkline(comparison_data)
                    
                    # Mostrar resumen
                    _render_comparison_summary(comparison_data)
                    
                    return comparison_data
                else:
                    st.error("No se pudieron obtener datos")
                    
            except Exception as e:
                st.error(f"Error: {str(e)[:50]}")
    
    return None


def _fetch_comparison(
    trends_module,
    keywords: List[str],
    geo: str,
    timeframe: str
) -> Optional[Dict]:
    """Obtiene datos de comparación de Google Trends"""
    try:
        # Usar la función de comparación del módulo de trends
        result = trends_module.compare_keywords(
            keywords=keywords,
            geo=geo,
            timeframe=timeframe
        )
        
        if result.get("success"):
            return {
                "keywords": keywords,
                "timeline": result.get("timeline_data", []),
                "averages": result.get("averages", {}),
                "winner": result.get("winner", keywords[0])
            }
        return None
        
    except Exception:
        return None


def _render_comparison_sparkline(data: Dict) -> None:
    """Renderiza un mini gráfico de comparación"""
    timeline = data.get("timeline", [])
    keywords = data.get("keywords", [])
    
    if not timeline or not keywords:
        return
    
    # Colores para cada keyword
    colors = ["#7C3AED", "#F59E0B", "#10B981"]
    
    fig = go.Figure()
    
    for idx, kw in enumerate(keywords):
        values = []
        for point in timeline:
            point_values = point.get("values", [])
            if len(point_values) > idx:
                val = point_values[idx].get("extracted_value", 0)
                values.append(float(val) if val else 0)
        
        if values:
            fig.add_trace(go.Scatter(
                y=values[-12:],  # Últimos 12 puntos
                mode='lines',
                name=kw[:15],
                line=dict(color=colors[idx % len(colors)], width=2),
                hoverinfo='name+y'
            ))
    
    fig.update_layout(
        height=120,
        margin=dict(l=0, r=0, t=10, b=10),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=10)
        ),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_comparison_summary(data: Dict) -> None:
    """Renderiza resumen de comparación"""
    averages = data.get("averages", {})
    winner = data.get("winner", "")
    
    if not averages:
        return
    
    # Ordenar por promedio
    sorted_kws = sorted(averages.items(), key=lambda x: x[1], reverse=True)
    
    for idx, (kw, avg) in enumerate(sorted_kws):
        medal = ["🥇", "🥈", "🥉"][idx] if idx < 3 else "  "
        bar_width = min(100, (avg / max(averages.values())) * 100) if averages.values() else 0
        
        st.markdown(
            f'<div style="display: flex; align-items: center; margin: 4px 0;">'
            f'<span style="width: 20px;">{medal}</span>'
            f'<span style="flex: 1; font-size: 0.85rem;">{kw[:15]}</span>'
            f'<span style="font-weight: 600; font-size: 0.85rem;">{avg:.0f}</span>'
            f'</div>'
            f'<div style="height: 4px; background: #E5E7EB; border-radius: 2px; margin-bottom: 8px;">'
            f'<div style="height: 100%; width: {bar_width:.0f}%; background: #7C3AED; border-radius: 2px;"></div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    if winner:
        st.success(f"🏆 **Líder:** {winner}")


def render_quick_compare_standalone() -> None:
    """
    Versión standalone del comparador (sin módulo de trends)
    Usa session_state para almacenar datos
    """
    st.markdown("#### ⚡ Comparar Rápido")
    st.caption("Compara hasta 3 keywords lado a lado")
    
    # Inputs
    keywords = []
    for i in range(3):
        label = f"Keyword {i+1}" if i < 2 else "Keyword 3 (opcional)"
        kw = st.text_input(
            label,
            key=f"standalone_cmp_{i}",
            max_chars=50,
            label_visibility="collapsed" if i < 2 else "visible",
            placeholder=["Beelink", "Minisforum", "Geekom"][i]
        )
        if kw and kw.strip():
            keywords.append(kw.strip())
    
    if len(keywords) >= 2:
        st.info(f"✓ {len(keywords)} keywords listas para comparar")
        
        # Botón que dispara la comparación en el main
        if st.button("🔍 Comparar en detalle", use_container_width=True):
            st.session_state["compare_keywords"] = keywords
            st.session_state["trigger_comparison"] = True
    else:
        st.caption("Introduce al menos 2 keywords")
