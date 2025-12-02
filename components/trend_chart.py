"""
Trend Chart Component
Gráfico principal de tendencia temporal con trayectoria
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st


def render_trend_chart(
    timeline_data: list,
    keyword: str,
    show_trajectory: bool = True,
    show_seasonality: bool = False,
    height: int = 400
) -> None:
    """
    Renderiza el gráfico principal de tendencia
    
    Args:
        timeline_data: Lista de datos de Google Trends
        keyword: Palabra clave buscada
        show_trajectory: Mostrar línea de tendencia suavizada
        show_seasonality: Mostrar/ocultar efecto estacional
    """
    if not timeline_data:
        st.warning("No hay datos para mostrar")
        return
    
    # Preparar datos
    dates = []
    values = []
    
    for point in timeline_data:
        if "date" in point and "values" in point and len(point["values"]) > 0:
            # Parsear fecha
            date_str = point["date"]
            
            # Limpiar rangos de fecha (tomar inicio)
            if " – " in date_str:
                date_str = date_str.split(" – ")[0]
            if " - " in date_str:
                date_str = date_str.split(" - ")[0]
            
            date_str = date_str.strip()
            date = None
            
            # Intentar múltiples formatos
            formats_to_try = [
                "%b %d, %Y",      # Nov 3, 2024
                "%B %d, %Y",      # November 3, 2024
                "%b %Y",          # Nov 2024
                "%B %Y",          # November 2024
                "%Y-%m-%d",       # 2024-11-03
                "%d/%m/%Y",       # 03/11/2024
                "%m/%d/%Y",       # 11/03/2024
                "%d %b %Y",       # 03 Nov 2024
                "%d %B %Y",       # 03 November 2024
            ]
            
            for fmt in formats_to_try:
                try:
                    date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if date is None:
                # Intentar extraer año y mes con regex como fallback
                import re
                match = re.search(r'(\w+)\s+(\d{4})', date_str)
                if match:
                    month_str, year = match.groups()
                    month_map = {
                        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
                        'ene': 1, 'abr': 4, 'ago': 8, 'dic': 12
                    }
                    month_num = month_map.get(month_str[:3].lower())
                    if month_num:
                        date = datetime(int(year), month_num, 1)
            
            if date:
                dates.append(date)
                val = point["values"][0].get("extracted_value", 0)
                values.append(float(val) if val else 0)
    
    if not dates or not values:
        st.warning("No se pudieron procesar los datos")
        return
    
    df = pd.DataFrame({"date": dates, "value": values})
    df = df.sort_values("date")
    
    # Calcular métricas
    current_value = df["value"].iloc[-1]
    avg_value = df["value"].mean()
    
    # Calcular crecimiento
    if len(df) >= 6:
        recent_avg = df["value"].tail(3).mean()
        previous_avg = df["value"].head(len(df) - 3).mean()
        if previous_avg > 0:
            growth = ((recent_avg - previous_avg) / previous_avg) * 100
        else:
            growth = 0
    else:
        growth = 0
    
    # Crear figura
    fig = go.Figure()
    
    # Área con gradiente
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["value"],
        mode='lines',
        name='Búsquedas',
        line=dict(color='#7C3AED', width=2),
        fill='tozeroy',
        fillcolor='rgba(124, 58, 237, 0.1)',
        hovertemplate='<b>%{x|%b %Y}</b><br>Índice: %{y}<extra></extra>'
    ))
    
    # Línea de trayectoria (media móvil)
    if show_trajectory and len(df) >= 6:
        window = min(6, len(df) // 3)
        df["trajectory"] = df["value"].rolling(window=window, center=True).mean()
        
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["trajectory"],
            mode='lines',
            name='Trayectoria',
            line=dict(color='#1A1A2E', width=3, dash='solid'),
            hovertemplate='<b>%{x|%b %Y}</b><br>Trayectoria: %{y:.0f}<extra></extra>'
        ))
    
    # Línea de promedio
    fig.add_hline(
        y=avg_value,
        line_dash="dash",
        line_color="#94A3B8",
        annotation_text=f"Media: {avg_value:.0f}",
        annotation_position="right"
    )
    
    # Layout
    fig.update_layout(
        title=None,
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title=None,
            tickformat='%b %Y'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title=None,
            range=[0, max(values) * 1.1]
        ),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=40, t=40, b=40),
        height=height,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Métricas en header
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Valor actual",
            value=f"{current_value:.0f}",
            delta=None
        )
    
    with col2:
        delta_color = "normal" if growth >= 0 else "inverse"
        st.metric(
            label="Crecimiento",
            value=f"{growth:+.1f}%",
            delta=f"vs período anterior",
            delta_color=delta_color
        )
    
    with col3:
        st.metric(
            label="Promedio",
            value=f"{avg_value:.0f}"
        )
    
    with col4:
        peak = df["value"].max()
        st.metric(
            label="Pico máximo",
            value=f"{peak:.0f}"
        )
    
    # Controles
    col_traj, col_export = st.columns([3, 1])
    
    with col_traj:
        show_traj = st.checkbox("Mostrar trayectoria", value=show_trajectory, key=f"traj_{keyword}")
    
    with col_export:
        # Preparar CSV para descarga
        csv_data = df[["date", "value"]].to_csv(index=False)
        st.download_button(
            label="📥 Exportar",
            data=csv_data,
            file_name=f"trend_{keyword}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # Mostrar gráfico
    st.plotly_chart(fig, use_container_width=True)


def render_mini_sparkline(
    values: list,
    color: str = "#7C3AED",
    height: int = 40,
    width: int = 120
) -> go.Figure:
    """
    Crea un mini sparkline para usar en cards
    
    Returns:
        Figura de Plotly
    """
    if not values or len(values) < 2:
        return None
    
    fig = go.Figure()
    
    # Determinar color basado en tendencia
    if values[-1] > values[0]:
        line_color = "#10B981"  # Verde - subiendo
    elif values[-1] < values[0]:
        line_color = "#EF4444"  # Rojo - bajando
    else:
        line_color = color
    
    fig.add_trace(go.Scatter(
        y=values,
        mode='lines',
        line=dict(color=line_color, width=2),
        fill='tozeroy',
        fillcolor=f'rgba({int(line_color[1:3], 16)}, {int(line_color[3:5], 16)}, {int(line_color[5:7], 16)}, 0.1)',
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        width=width,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def render_comparison_chart(
    data_by_country: dict,
    keyword: str,
    height: int = 400
) -> None:
    """
    Renderiza comparativa de tendencias por país
    
    Args:
        data_by_country: Dict con país -> timeline_data
    """
    if not data_by_country:
        st.warning("No hay datos para comparar")
        return
    
    colors = {
        "ES": "#F5C518",  # Amarillo - España
        "PT": "#10B981",  # Verde - Portugal
        "FR": "#3B82F6",  # Azul - Francia
        "IT": "#EF4444",  # Rojo - Italia
        "DE": "#8B5CF6"   # Púrpura - Alemania
    }
    
    country_names = {
        "ES": "España",
        "PT": "Portugal",
        "FR": "Francia",
        "IT": "Italia",
        "DE": "Alemania"
    }
    
    fig = go.Figure()
    
    for country, data in data_by_country.items():
        if not data.get("success") or not data.get("timeline_data"):
            continue
        
        timeline = data["timeline_data"]
        
        dates = []
        values = []
        
        for point in timeline:
            if "date" in point and "values" in point and len(point["values"]) > 0:
                date_str = point["date"]
                if " – " in date_str:
                    date_str = date_str.split(" – ")[0]
                
                try:
                    for fmt in ["%b %d, %Y", "%b %Y", "%Y-%m-%d"]:
                        try:
                            date = datetime.strptime(date_str, fmt)
                            break
                        except:
                            continue
                    else:
                        continue
                        
                    dates.append(date)
                    val = point["values"][0].get("extracted_value", 0)
                    values.append(float(val) if val else 0)
                except:
                    continue
        
        if dates and values:
            fig.add_trace(go.Scatter(
                x=dates,
                y=values,
                mode='lines',
                name=f"{country_names.get(country, country)}",
                line=dict(color=colors.get(country, "#666"), width=2),
                hovertemplate=f'<b>{country_names.get(country, country)}</b><br>%{{x|%b %Y}}: %{{y}}<extra></extra>'
            ))
    
    fig.update_layout(
        title=f"Comparativa por país: {keyword}",
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title=None
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title="Índice de interés"
        ),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        height=height,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
