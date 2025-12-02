"""
Product Matrix Component
Visualizaciones para análisis de productos de marca:
- Matriz de oportunidad (BCG adaptada)
- Ranking con sparklines
- Ciclo de vida
- Comparativas
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import List, Dict, Optional
import html

# Import seguro de los tipos
try:
    from modules.product_analysis import ProductData, ProductCategory, LifecycleStage
except ImportError:
    # Fallback si no está disponible
    ProductData = dict
    ProductCategory = None
    LifecycleStage = None


# Configuración visual por categoría
CATEGORY_CONFIG = {
    "emergente": {
        "icon": "🚀",
        "label": "Emergente",
        "color": "#8B5CF6",
        "bg_color": "#EDE9FE",
        "action": "Apostar"
    },
    "estrella": {
        "icon": "⭐",
        "label": "Estrella", 
        "color": "#F59E0B",
        "bg_color": "#FEF3C7",
        "action": "Potenciar"
    },
    "consolidado": {
        "icon": "💎",
        "label": "Consolidado",
        "color": "#3B82F6",
        "bg_color": "#DBEAFE",
        "action": "Mantener"
    },
    "nicho": {
        "icon": "👀",
        "label": "Nicho",
        "color": "#6B7280",
        "bg_color": "#F3F4F6",
        "action": "Observar"
    }
}

LIFECYCLE_CONFIG = {
    "lanzamiento": {"icon": "🌱", "color": "#10B981"},
    "crecimiento": {"icon": "📈", "color": "#F59E0B"},
    "madurez": {"icon": "🏔️", "color": "#3B82F6"},
    "declive": {"icon": "📉", "color": "#EF4444"}
}


def render_product_section(
    analysis_result: Dict,
    brand: str
) -> None:
    """
    Renderiza la sección completa de análisis de productos
    
    Args:
        analysis_result: Resultado de ProductAnalyzer.full_analysis()
        brand: Nombre de la marca
    """
    products = analysis_result.get("products", [])
    classified = analysis_result.get("classified", {})
    insights = analysis_result.get("insights", {})
    
    # Escapar el nombre de la marca para HTML
    brand_safe = html.escape(brand)
    
    total_products = len(products)
    
    st.markdown(f"### 🏷️ Productos de {brand_safe}")
    
    if total_products == 0:
        st.info(
            f"No se detectaron productos específicos para '{brand_safe}'. "
            "Esto puede ocurrir si es una marca nueva o si las búsquedas son muy genéricas."
        )
        
        # Mostrar recomendaciones
        if insights.get("recommendations"):
            for rec in insights["recommendations"]:
                st.markdown(f"💡 {html.escape(str(rec))}")
        return
    
    st.markdown(f"Se detectaron **{total_products} productos**")
    
    # Tabs para diferentes vistas
    tab_matrix, tab_ranking, tab_lifecycle, tab_compare = st.tabs([
        "📊 Matriz", "📈 Ranking", "🔄 Ciclo de Vida", "⚔️ Comparar"
    ])
    
    with tab_matrix:
        render_opportunity_matrix(products, classified, brand)
    
    with tab_ranking:
        render_product_ranking(products)
    
    with tab_lifecycle:
        render_lifecycle_chart(products)
    
    with tab_compare:
        render_product_comparison(products, brand)
    
    # Insights y recomendaciones
    st.markdown("---")
    render_product_insights(insights, brand)


def render_opportunity_matrix(
    products: List,
    classified: Dict,
    brand: str
) -> None:
    """Renderiza la matriz de oportunidad interactiva"""
    
    if not products:
        st.info("No hay suficientes datos para generar la matriz")
        return
    
    # Preparar datos para el scatter plot
    x_values = []  # Volumen
    y_values = []  # Crecimiento
    names = []
    colors = []
    sizes = []
    
    for product in products:
        # Manejar diferentes tipos de datos
        if hasattr(product, 'name'):
            name = product.name
            volume = product.volume if product.volume else 0
            growth = product.growth if product.growth else 0
            category = product.category.value if hasattr(product.category, 'value') else str(product.category)
        else:
            name = product.get('name', 'Unknown')
            volume = product.get('volume', 0) or 0
            growth = product.get('growth', 0) or 0
            category = product.get('category', 'nicho')
        
        x_values.append(max(0, volume))  # Evitar valores negativos
        y_values.append(growth)
        names.append(name)
        colors.append(CATEGORY_CONFIG.get(category, CATEGORY_CONFIG["nicho"])["color"])
        sizes.append(max(15, min(50, volume / 2 + 15)))  # Tamaño proporcional al volumen
    
    # Crear figura
    fig = go.Figure()
    
    # Añadir cuadrantes de fondo
    max_x = max(x_values) if x_values else 100
    max_y = max(y_values) if y_values else 100
    min_y = min(y_values) if y_values else -50
    
    # Calcular centro de la matriz
    mid_x = max_x / 2 if max_x > 0 else 50
    mid_y = (max_y + min_y) / 2 if max_y != min_y else 15
    
    # Cuadrantes
    fig.add_shape(type="rect", x0=0, y0=mid_y, x1=mid_x, y1=max_y + 10,
                  fillcolor="rgba(139, 92, 246, 0.1)", line_width=0)  # Emergente
    fig.add_shape(type="rect", x0=mid_x, y0=mid_y, x1=max_x + 10, y1=max_y + 10,
                  fillcolor="rgba(245, 158, 11, 0.1)", line_width=0)  # Estrella
    fig.add_shape(type="rect", x0=mid_x, y0=min_y - 10, x1=max_x + 10, y1=mid_y,
                  fillcolor="rgba(59, 130, 246, 0.1)", line_width=0)  # Consolidado
    fig.add_shape(type="rect", x0=0, y0=min_y - 10, x1=mid_x, y1=mid_y,
                  fillcolor="rgba(107, 114, 128, 0.1)", line_width=0)  # Nicho
    
    # Añadir líneas de referencia
    fig.add_hline(y=mid_y, line_dash="dash", line_color="#9CA3AF", line_width=1)
    fig.add_vline(x=mid_x, line_dash="dash", line_color="#9CA3AF", line_width=1)
    
    # Añadir puntos
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='markers+text',
        marker=dict(
            size=sizes,
            color=colors,
            line=dict(width=2, color='white')
        ),
        text=names,
        textposition="top center",
        textfont=dict(size=10),
        hovertemplate="<b>%{text}</b><br>Volumen: %{x:.0f}<br>Crecimiento: %{y:.1f}%<extra></extra>"
    ))
    
    # Etiquetas de cuadrantes
    fig.add_annotation(x=mid_x/2, y=max_y, text="🚀 EMERGENTE", showarrow=False,
                       font=dict(size=12, color="#8B5CF6"))
    fig.add_annotation(x=mid_x + (max_x - mid_x)/2, y=max_y, text="⭐ ESTRELLA", showarrow=False,
                       font=dict(size=12, color="#F59E0B"))
    fig.add_annotation(x=mid_x + (max_x - mid_x)/2, y=min_y, text="💎 CONSOLIDADO", showarrow=False,
                       font=dict(size=12, color="#3B82F6"))
    fig.add_annotation(x=mid_x/2, y=min_y, text="👀 NICHO", showarrow=False,
                       font=dict(size=12, color="#6B7280"))
    
    fig.update_layout(
        title=dict(text="Matriz de Oportunidad de Productos", font=dict(size=16)),
        xaxis=dict(
            title="Volumen de búsqueda (índice)",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            range=[-5, max_x + 15]
        ),
        yaxis=dict(
            title="Crecimiento (%)",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            range=[min_y - 15, max_y + 15]
        ),
        showlegend=False,
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Leyenda
    col1, col2, col3, col4 = st.columns(4)
    for col, (cat_key, config) in zip([col1, col2, col3, col4], CATEGORY_CONFIG.items()):
        count = len([p for p in products if _get_category(p) == cat_key])
        with col:
            st.markdown(
                f'<div style="background: {config["bg_color"]}; padding: 8px; '
                f'border-radius: 8px; text-align: center;">'
                f'{config["icon"]} **{config["label"]}** ({count})<br>'
                f'<span style="font-size: 0.8rem; color: #6B7280;">{config["action"]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )


def render_product_ranking(products: List) -> None:
    """Renderiza el ranking de productos con sparklines"""
    
    if not products:
        st.info("No hay productos para mostrar")
        return
    
    # Ordenar por crecimiento
    sorted_products = sorted(
        products,
        key=lambda p: _safe_get(p, 'growth', 0),
        reverse=True
    )
    
    for i, product in enumerate(sorted_products[:10]):
        name = _safe_get(product, 'name', 'Unknown')
        volume = _safe_get(product, 'volume', 0)
        growth = _safe_get(product, 'growth', 0)
        category = _get_category(product)
        values = _safe_get(product, 'trend_values', [])
        
        config = CATEGORY_CONFIG.get(category, CATEGORY_CONFIG["nicho"])
        
        # Determinar color del crecimiento
        if growth > 20:
            growth_color = "#10B981"
            growth_icon = "📈"
        elif growth < -10:
            growth_color = "#EF4444"
            growth_icon = "📉"
        else:
            growth_color = "#6B7280"
            growth_icon = "➡️"
        
        # Crear mini sparkline
        sparkline_html = ""
        if values and len(values) >= 3:
            sparkline_fig = _create_sparkline(values, growth_color)
            sparkline_html = f'<div id="spark_{i}"></div>'
        
        # Card del producto
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            st.markdown(
                f'<div style="display: flex; align-items: center; gap: 8px;">'
                f'<span style="color: #9CA3AF; font-weight: 600;">{i+1}.</span>'
                f'<span style="font-weight: 600; color: #1A1A2E;">{html.escape(name)}</span>'
                f'<span style="background: {config["bg_color"]}; color: {config["color"]}; '
                f'padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">'
                f'{config["icon"]} {config["label"]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        
        with col2:
            # Barra de volumen
            max_vol = max(_safe_get(p, 'volume', 0) for p in products) or 1
            vol_pct = (volume / max_vol) * 100
            st.markdown(
                f'<div style="font-size: 0.8rem; color: #6B7280;">Volumen</div>'
                f'<div style="display: flex; align-items: center; gap: 8px;">'
                f'<div style="flex: 1; height: 8px; background: #F3F4F6; border-radius: 4px;">'
                f'<div style="height: 100%; width: {vol_pct:.0f}%; background: #7C3AED; border-radius: 4px;"></div>'
                f'</div>'
                f'<span style="font-weight: 600; min-width: 40px;">{volume:.0f}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        
        with col3:
            st.markdown(
                f'<div style="font-size: 0.8rem; color: #6B7280;">Crecimiento</div>'
                f'<div style="font-size: 1.1rem; font-weight: 600; color: {growth_color};">'
                f'{growth_icon} {growth:+.1f}%</div>',
                unsafe_allow_html=True
            )
        
        with col4:
            # Mini sparkline con Plotly
            if values and len(values) >= 3:
                fig = _create_sparkline(values, growth_color)
                st.plotly_chart(fig, use_container_width=True, key=f"spark_{name}_{i}")
        
        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #F3F4F6;'>", 
                   unsafe_allow_html=True)


def render_lifecycle_chart(products: List) -> None:
    """Renderiza el diagrama de ciclo de vida"""
    
    if not products:
        st.info("No hay productos para mostrar")
        return
    
    # Agrupar por etapa
    stages = {
        "lanzamiento": [],
        "crecimiento": [],
        "madurez": [],
        "declive": []
    }
    
    for product in products:
        lifecycle = _get_lifecycle(product)
        if lifecycle in stages:
            stages[lifecycle].append(product)
    
    # Crear visualización
    fig = go.Figure()
    
    # Curva del ciclo de vida
    x_curve = list(range(100))
    y_curve = [
        (x * 2) if x < 20 else  # Lanzamiento
        (40 + (x - 20) * 2) if x < 40 else  # Crecimiento
        (80 - (x - 40) * 0.5) if x < 70 else  # Madurez
        (65 - (x - 70) * 2)  # Declive
        for x in x_curve
    ]
    
    fig.add_trace(go.Scatter(
        x=x_curve,
        y=y_curve,
        mode='lines',
        line=dict(color='#E5E7EB', width=3),
        hoverinfo='skip',
        showlegend=False
    ))
    
    # Zonas de color
    zones = [
        (0, 20, "#10B98120", "🌱 Lanzamiento"),
        (20, 40, "#F59E0B20", "📈 Crecimiento"),
        (40, 70, "#3B82F620", "🏔️ Madurez"),
        (70, 100, "#EF444420", "📉 Declive")
    ]
    
    for x0, x1, color, label in zones:
        fig.add_vrect(x0=x0, x1=x1, fillcolor=color, line_width=0)
        fig.add_annotation(
            x=(x0 + x1) / 2,
            y=90,
            text=label,
            showarrow=False,
            font=dict(size=11)
        )
    
    # Posicionar productos
    stage_positions = {
        "lanzamiento": (10, 20),
        "crecimiento": (30, 70),
        "madurez": (55, 75),
        "declive": (85, 35)
    }
    
    for stage, stage_products in stages.items():
        if not stage_products:
            continue
        
        base_x, base_y = stage_positions[stage]
        
        for j, product in enumerate(stage_products[:5]):
            name = _safe_get(product, 'name', '?')
            # Distribuir verticalmente
            y_offset = (j - len(stage_products) / 2) * 8
            
            fig.add_trace(go.Scatter(
                x=[base_x],
                y=[base_y + y_offset],
                mode='markers+text',
                marker=dict(
                    size=20,
                    color=LIFECYCLE_CONFIG.get(stage, {}).get("color", "#6B7280"),
                    line=dict(width=2, color='white')
                ),
                text=[name],
                textposition="middle right",
                textfont=dict(size=10),
                hovertemplate=f"<b>{html.escape(name)}</b><br>Etapa: {stage}<extra></extra>",
                showlegend=False
            ))
    
    fig.update_layout(
        title="Ciclo de Vida de Productos",
        xaxis=dict(visible=False, range=[-5, 105]),
        yaxis=dict(visible=False, range=[0, 100]),
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Resumen por etapa
    cols = st.columns(4)
    for col, (stage, config) in zip(cols, LIFECYCLE_CONFIG.items()):
        count = len(stages.get(stage, []))
        with col:
            st.markdown(
                f'<div style="text-align: center; padding: 8px;">'
                f'<span style="font-size: 1.5rem;">{config["icon"]}</span><br>'
                f'<span style="font-weight: 600; color: {config["color"]};">{count}</span><br>'
                f'<span style="font-size: 0.8rem; color: #6B7280;">{stage.title()}</span>'
                f'</div>',
                unsafe_allow_html=True
            )


def render_product_comparison(products: List, brand: str) -> None:
    """Renderiza comparativa visual de productos"""
    
    if not products or len(products) < 2:
        st.info("Se necesitan al menos 2 productos para comparar")
        return
    
    # Seleccionar productos a comparar
    product_names = [_safe_get(p, 'name', f'Producto {i}') for i, p in enumerate(products)]
    
    selected = st.multiselect(
        "Selecciona productos a comparar (máx. 5)",
        product_names,
        default=product_names[:min(3, len(product_names))],
        max_selections=5
    )
    
    if len(selected) < 2:
        st.info("Selecciona al menos 2 productos")
        return
    
    # Filtrar productos seleccionados
    selected_products = [p for p in products if _safe_get(p, 'name', '') in selected]
    
    # Gráfico de barras comparativo
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Volumen de búsqueda", "Crecimiento (%)"),
        horizontal_spacing=0.15
    )
    
    names = [_safe_get(p, 'name', '?') for p in selected_products]
    volumes = [_safe_get(p, 'volume', 0) for p in selected_products]
    growths = [_safe_get(p, 'growth', 0) for p in selected_products]
    
    # Colores por categoría
    colors = [CATEGORY_CONFIG.get(_get_category(p), CATEGORY_CONFIG["nicho"])["color"] 
              for p in selected_products]
    
    # Barras de volumen
    fig.add_trace(
        go.Bar(x=names, y=volumes, marker_color=colors, name="Volumen"),
        row=1, col=1
    )
    
    # Barras de crecimiento
    growth_colors = ["#10B981" if g > 0 else "#EF4444" for g in growths]
    fig.add_trace(
        go.Bar(x=names, y=growths, marker_color=growth_colors, name="Crecimiento"),
        row=1, col=2
    )
    
    fig.update_layout(
        height=350,
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla comparativa
    st.markdown("#### Detalle comparativo")
    
    cols = st.columns(len(selected_products))
    for col, product in zip(cols, selected_products):
        name = _safe_get(product, 'name', '?')
        volume = _safe_get(product, 'volume', 0)
        growth = _safe_get(product, 'growth', 0)
        category = _get_category(product)
        config = CATEGORY_CONFIG.get(category, CATEGORY_CONFIG["nicho"])
        
        with col:
            st.markdown(
                f'<div style="background: {config["bg_color"]}; padding: 16px; '
                f'border-radius: 12px; text-align: center;">'
                f'<div style="font-size: 1.25rem; font-weight: 700; color: #1A1A2E; '
                f'margin-bottom: 8px;">{html.escape(name)}</div>'
                f'<div style="margin-bottom: 12px;">'
                f'<span style="background: {config["color"]}; color: white; '
                f'padding: 4px 8px; border-radius: 4px; font-size: 0.75rem;">'
                f'{config["icon"]} {config["label"]}</span></div>'
                f'<div style="font-size: 0.85rem; color: #4B5563;">'
                f'Volumen: <b>{volume:.0f}</b></div>'
                f'<div style="font-size: 0.85rem; color: #4B5563;">'
                f'Crecimiento: <b style="color: {"#10B981" if growth > 0 else "#EF4444"}">'
                f'{growth:+.1f}%</b></div>'
                f'</div>',
                unsafe_allow_html=True
            )


def render_product_insights(insights: Dict, brand: str) -> None:
    """Renderiza insights y recomendaciones"""
    
    brand_safe = html.escape(brand)
    
    st.markdown("### 💡 Insights de Productos")
    
    # Resumen
    summary = insights.get("summary", "")
    if summary:
        st.markdown(
            f'<div style="background: linear-gradient(135deg, #EDE9FE, #FEF3C7); '
            f'padding: 16px; border-radius: 12px; margin-bottom: 16px;">'
            f'<p style="margin: 0; color: #374151;">{html.escape(summary)}</p>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    # Top oportunidades
    top_opportunities = insights.get("top_opportunities", [])
    if top_opportunities:
        st.markdown("#### 🔥 Top Oportunidades")
        
        for i, product in enumerate(top_opportunities[:3]):
            name = _safe_get(product, 'name', '?')
            growth = _safe_get(product, 'growth', 0)
            category = _get_category(product)
            config = CATEGORY_CONFIG.get(category, CATEGORY_CONFIG["nicho"])
            
            st.markdown(
                f'<div style="display: flex; align-items: center; gap: 12px; '
                f'padding: 12px; background: white; border-radius: 8px; '
                f'border-left: 4px solid {config["color"]}; margin-bottom: 8px;">'
                f'<span style="font-size: 1.25rem; font-weight: 700; color: #9CA3AF;">{i+1}</span>'
                f'<div style="flex: 1;">'
                f'<span style="font-weight: 600; color: #1A1A2E;">{html.escape(name)}</span>'
                f'<span style="margin-left: 8px; color: #10B981; font-weight: 500;">'
                f'+{growth:.0f}%</span>'
                f'</div>'
                f'<span style="background: {config["bg_color"]}; color: {config["color"]}; '
                f'padding: 4px 8px; border-radius: 4px; font-size: 0.75rem;">'
                f'{config["icon"]} {config["label"]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    
    # Recomendaciones y warnings
    col1, col2 = st.columns(2)
    
    with col1:
        recommendations = insights.get("recommendations", [])
        if recommendations:
            st.markdown("#### ✅ Recomendaciones")
            for rec in recommendations:
                st.markdown(f"- {html.escape(str(rec))}")
    
    with col2:
        warnings = insights.get("warnings", [])
        if warnings:
            st.markdown("#### ⚠️ Alertas")
            for warn in warnings:
                st.warning(html.escape(str(warn)))


def _create_sparkline(values: List[float], color: str = "#7C3AED") -> go.Figure:
    """Crea un mini sparkline"""
    if not values:
        values = [0]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=values,
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=f'{color}20',
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
    
    return fig


def _safe_get(obj, key: str, default=None):
    """Obtiene valor de forma segura de objeto o dict"""
    if obj is None:
        return default
    
    if hasattr(obj, key):
        val = getattr(obj, key, default)
        return val if val is not None else default
    
    if isinstance(obj, dict):
        val = obj.get(key, default)
        return val if val is not None else default
    
    return default


def _get_category(product) -> str:
    """Obtiene categoría de forma segura"""
    if product is None:
        return "nicho"
    
    if hasattr(product, 'category'):
        cat = product.category
        if hasattr(cat, 'value'):
            return cat.value
        return str(cat)
    
    if isinstance(product, dict):
        return product.get('category', 'nicho')
    
    return "nicho"


def _get_lifecycle(product) -> str:
    """Obtiene etapa de ciclo de vida de forma segura"""
    if product is None:
        return "lanzamiento"
    
    if hasattr(product, 'lifecycle'):
        lc = product.lifecycle
        if hasattr(lc, 'value'):
            return lc.value
        return str(lc)
    
    if isinstance(product, dict):
        return product.get('lifecycle', 'lanzamiento')
    
    return "lanzamiento"
