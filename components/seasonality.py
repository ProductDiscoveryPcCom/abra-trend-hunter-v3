"""
Seasonality Panel Component
Panel de estacionalidad con gráfico de barras mensual
"""

import plotly.graph_objects as go
import streamlit as st


MONTH_NAMES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
}


def render_seasonality_panel(
    seasonality_data: dict,
    ai_explanation: str = None,
    height: int = 200
) -> None:
    """
    Renderiza el panel de estacionalidad con gráfico y explicación

    Args:
        seasonality_data: Dict con monthly_pattern, is_seasonal, etc.
        ai_explanation: Explicación generada por IA (opcional)
    """
    is_seasonal = seasonality_data.get("is_seasonal", False)
    monthly_pattern = seasonality_data.get("monthly_pattern", {})
    seasonality_score = seasonality_data.get("seasonality_score", 0)

    # Header con badge
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 📅 Estacionalidad")

    with col2:
        if is_seasonal:
            st.success("🔥 Altamente estacional")
        else:
            st.info("📊 Poco estacional")

    if not monthly_pattern:
        st.info("No hay suficientes datos para analizar estacionalidad")
        return

    # Preparar datos para el gráfico
    months = list(range(1, 13))
    values = [monthly_pattern.get(m, 0) for m in months]

    # Colores: verde para positivo, rojo para negativo
    colors = ['#10B981' if v >= 0 else '#FCA5A5' for v in values]

    # Crear gráfico
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=[MONTH_NAMES[m] for m in months],
        y=values,
        marker_color=colors,
        hovertemplate='<b>%{x}</b><br>%{y:+.0%} vs media<extra></extra>'
    ))

    # Línea de referencia en 0
    fig.add_hline(y=0, line_color='#94A3B8', line_width=1)

    fig.update_layout(
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            title=None
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title=None,
            tickformat='+.0%',
            zeroline=False
        ),
        margin=dict(l=40, r=20, t=20, b=40),
        height=height,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Explicación IA
    if ai_explanation:
        st.markdown(
            f'<div style="background-color: #F3F4F6; padding: 12px 16px; '
            f'border-radius: 8px; font-size: 0.875rem; color: #4B5563;">'
            f'💡 {ai_explanation}</div>',
            unsafe_allow_html=True
        )

    # Mostrar meses pico y valle
    if monthly_pattern:
        peak_month = max(monthly_pattern, key=monthly_pattern.get)
        low_month = min(monthly_pattern, key=monthly_pattern.get)

        col_peak, col_low = st.columns(2)

        with col_peak:
            peak_value = monthly_pattern[peak_month]
            st.markdown(
                f'<div style="text-align: center;">'
                f'<span style="color: #10B981; font-size: 1.5rem;">▲</span><br>'
                f'<span style="font-weight: 600;">Pico: {MONTH_NAMES[peak_month]}</span><br>'
                f'<span style="color: #10B981; font-size: 0.875rem;">{peak_value:+.0%}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_low:
            low_value = monthly_pattern[low_month]
            st.markdown(
                f'<div style="text-align: center;">'
                f'<span style="color: #EF4444; font-size: 1.5rem;">▼</span><br>'
                f'<span style="font-weight: 600;">Valle: {MONTH_NAMES[low_month]}</span><br>'
                f'<span style="color: #EF4444; font-size: 0.875rem;">{low_value:+.0%}</span>'
                f'</div>',
                unsafe_allow_html=True
            )


def render_seasonality_badge(is_seasonal: bool) -> str:
    """Retorna HTML del badge de estacionalidad"""
    if is_seasonal:
        return (
            '<span style="background-color: #FEF3C7; color: #D97706; '
            'padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; '
            'font-weight: 500;">Estacional</span>'
        )
    else:
        return (
            '<span style="background-color: #D1FAE5; color: #059669; '
            'padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; '
            'font-weight: 500;">Estable</span>'
        )


def render_seasonality_heatmap(
    timeline_data: list,
    height: int = 250
) -> None:
    """
    Renderiza un heatmap de estacionalidad (mes x año)
    
    Args:
        timeline_data: Lista de puntos de timeline con 'date' y valores
        height: Altura del gráfico
    """
    from collections import defaultdict
    import numpy as np
    
    if not timeline_data:
        st.info("No hay datos suficientes para el heatmap")
        return
    
    # Organizar datos por año y mes
    year_month_data = defaultdict(lambda: defaultdict(list))
    
    for point in timeline_data:
        date_str = point.get("date", "")
        values = point.get("values", [])
        
        if date_str and values:
            try:
                # Parsear fecha (formato: "Dec 2024" o "2024-12-01")
                if "-" in date_str:
                    parts = date_str.split("-")
                    year = int(parts[0])
                    month = int(parts[1])
                else:
                    # Formato "Dec 2024"
                    month_map = {
                        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
                        "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
                        "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
                    }
                    parts = date_str.split()
                    if len(parts) >= 2:
                        month = month_map.get(parts[0][:3], 1)
                        year = int(parts[-1])
                    else:
                        continue
                
                value = values[0].get("extracted_value", 0)
                if value:
                    year_month_data[year][month].append(float(value))
            except (ValueError, IndexError, KeyError):
                continue
    
    if not year_month_data:
        st.info("No se pudo procesar datos para el heatmap")
        return
    
    # Crear matriz para heatmap
    years = sorted(year_month_data.keys())
    months = list(range(1, 13))
    
    # Matriz de valores (promedios)
    z_values = []
    for year in years:
        row = []
        for month in months:
            values = year_month_data[year][month]
            avg = sum(values) / len(values) if values else 0
            row.append(avg)
        z_values.append(row)
    
    # Crear heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=[MONTH_NAMES[m] for m in months],
        y=[str(y) for y in years],
        colorscale=[
            [0, '#F3F4F6'],
            [0.25, '#FDE68A'],
            [0.5, '#FBBF24'],
            [0.75, '#F59E0B'],
            [1, '#D97706']
        ],
        hovertemplate='%{y} - %{x}<br>Índice: %{z:.0f}<extra></extra>',
        showscale=True,
        colorbar=dict(
            title="Índice",
            titleside="right",
            thickness=15,
            len=0.8
        )
    ))
    
    fig.update_layout(
        title=dict(
            text="📊 Heatmap de Estacionalidad",
            font=dict(size=14)
        ),
        height=height,
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis=dict(
            title="Mes",
            tickangle=0,
            side="bottom"
        ),
        yaxis=dict(
            title="Año",
            autorange="reversed"  # Años más recientes arriba
        ),
        plot_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Insights automáticos
    if z_values:
        all_values = [v for row in z_values for v in row if v > 0]
        if all_values:
            max_val = max(all_values)
            min_val = min(all_values) if min(all_values) > 0 else 0
            
            # Encontrar mes con mayor actividad
            month_avgs = {}
            for m_idx, month in enumerate(months):
                month_vals = [row[m_idx] for row in z_values if row[m_idx] > 0]
                if month_vals:
                    month_avgs[month] = sum(month_vals) / len(month_vals)
            
            if month_avgs:
                best_month = max(month_avgs, key=month_avgs.get)
                worst_month = min(month_avgs, key=month_avgs.get)
                
                st.caption(
                    f"📈 **Mejor mes histórico:** {MONTH_NAMES[best_month]} | "
                    f"📉 **Mes más bajo:** {MONTH_NAMES[worst_month]}"
                )


