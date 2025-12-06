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

# Importar utilidad centralizada
from utils.validation import hex_to_rgba

# Import seguro de los tipos
try:
    from modules.product_analysis import ProductData, OpportunityCategory, LifecycleStage
except ImportError:
    # Fallback si no está disponible
    ProductData = dict
    OpportunityCategory = None
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
    thresholds = analysis_result.get("thresholds", {})  # Umbrales de clasificación
    insights = analysis_result.get("insights", {})
    shopping_products = analysis_result.get("shopping_products", [])
    sources = analysis_result.get("sources", {})

    # Escapar el nombre de la marca para HTML
    brand_safe = html.escape(brand)

    total_products = len(products)
    total_shopping = len(shopping_products)

    st.markdown(f"### 🏷️ Productos de {brand_safe}")

    # Métricas de fuentes
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Productos detectados", total_products)
    with col2:
        st.metric("Google Shopping", total_shopping)
    with col3:
        st.metric("Desde Trends", sources.get("trends", 0))
    with col4:
        st.metric("Autocomplete", sources.get("autocomplete", 0))

    if total_products == 0 and total_shopping == 0:
        st.info(
            f"No se detectaron productos específicos para '{brand_safe}'. "
            "Esto puede ocurrir si es una marca nueva o si las búsquedas son muy genéricas."
        )

        # Mostrar recomendaciones
        if insights.get("recommendations"):
            for rec in insights["recommendations"]:
                st.markdown(f"💡 {html.escape(str(rec))}")
        return

    # Tabs para diferentes vistas
    tabs = ["📊 Matriz", "📈 Ranking", "🔄 Ciclo de Vida", "⚔️ Comparar"]
    if shopping_products:
        tabs.append("🛒 Shopping")

    tab_list = st.tabs(tabs)

    with tab_list[0]:  # Matriz
        render_opportunity_matrix(products, classified, brand, thresholds)

    with tab_list[1]:  # Ranking
        render_product_ranking(products, paginate=True)

    with tab_list[2]:  # Ciclo de Vida
        render_lifecycle_chart(products)

    with tab_list[3]:  # Comparar
        render_product_comparison(products, brand)

    if shopping_products and len(tab_list) > 4:
        with tab_list[4]:  # Shopping
            render_shopping_products(shopping_products, brand)

    # Insights y recomendaciones
    st.markdown("---")
    render_product_insights(insights, brand)
    
    # Análisis con IA (si hay suficientes productos)
    if len(products) >= 3:
        try:
            from modules.ai_product_intelligence import render_ai_product_analysis
            render_ai_product_analysis(products, brand)
        except ImportError:
            pass  # Módulo no disponible


def render_shopping_products(
    products: List[Dict],
    brand: str,
    items_per_page: int = 12
) -> None:
    """
    Renderiza productos de Google Shopping con paginación

    Args:
        products: Lista de productos de Shopping
        brand: Nombre de la marca
        items_per_page: Productos por página
    """
    if not products:
        st.info("No se encontraron productos en Google Shopping")
        return

    st.markdown(f"**{len(products)} productos encontrados en Google Shopping**")

    # Paginación
    total_pages = (len(products) + items_per_page - 1) // items_per_page

    if total_pages > 1:
        page = st.selectbox(
            "Página",
            options=list(range(1, total_pages + 1)),
            format_func=lambda x: f"Página {x} de {total_pages}",
            key=f"shopping_page_{brand}"
        )
    else:
        page = 1

    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_products = products[start_idx:end_idx]

    # Grid de productos
    cols = st.columns(4)

    for i, product in enumerate(page_products):
        with cols[i % 4]:
            _render_shopping_card(product)


def _render_shopping_card(product: Dict) -> None:
    """Renderiza tarjeta de producto de Shopping"""
    with st.container():
        # Thumbnail
        thumbnail = product.get("thumbnail", "")
        if thumbnail:
            st.image(thumbnail, width=150)

        # Título (truncado)
        title = product.get("title", "Sin título")
        title_short = title[:50] + "..." if len(title) > 50 else title
        st.markdown(f"**{html.escape(title_short)}**")

        # Precio
        price = product.get("price", "")
        if price:
            st.markdown(f"💰 **{html.escape(price)}**")

        # Rating
        rating = product.get("rating", 0)
        reviews = product.get("reviews", 0)
        if rating > 0:
            stars = "⭐" * int(rating)
            st.caption(f"{stars} ({reviews} reviews)")

        # Fuente
        source = product.get("source", "")
        if source:
            st.caption(f"📍 {html.escape(source)}")

        # Link
        link = product.get("link", "")
        if link:
            st.markdown(f"[Ver producto]({link})")

        st.markdown("---")


def render_opportunity_matrix(
    products: List,
    classified: Dict,
    brand: str,
    thresholds: Dict = None
) -> None:
    """
    Renderiza la matriz de oportunidad interactiva.
    
    IMPORTANTE: Usa los mismos umbrales que la clasificación para que
    la posición visual coincida con la categoría asignada.
    
    Args:
        products: Lista de productos
        classified: Dict con productos clasificados
        brand: Nombre de la marca
        thresholds: Dict con umbrales {"volume": X, "growth": Y} de la clasificación
    """

    if not products:
        st.info("No hay suficientes datos para generar la matriz")
        return

    # Preparar datos para el scatter plot
    x_values = []  # Volumen
    y_values = []  # Crecimiento
    names = []
    colors = []

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

    if not x_values or all(v == 0 for v in x_values):
        st.warning("No hay datos de volumen suficientes para la matriz")
        return

    # Crear figura
    fig = go.Figure()

    # Calcular rangos de los ejes con padding
    x_min = min(x_values)
    x_max = max(x_values)
    y_min = min(y_values)
    y_max = max(y_values)
    
    # Asegurar rangos mínimos
    if x_max == x_min:
        x_max = x_min + 100
    if y_max == y_min:
        y_max = y_min + 50
        y_min = y_min - 50
    
    x_range = x_max - x_min
    y_range = y_max - y_min
    x_padding = x_range * 0.15
    y_padding = y_range * 0.15

    # CRÍTICO: Usar los mismos umbrales que la clasificación
    # Esto garantiza que la posición visual coincide con la categoría
    if thresholds:
        mid_x = thresholds.get("volume", (x_max + x_min) / 2)
        mid_y = thresholds.get("growth", 0)
    else:
        # Fallback: calcular si no se pasaron (compatibilidad)
        mid_x = (x_max + x_min) / 2
        mid_y = 0  # Crecimiento 0 como línea divisoria

    # Extender rangos si los umbrales están fuera
    x_min_plot = min(x_min - x_padding, mid_x - x_range * 0.3)
    x_max_plot = max(x_max + x_padding, mid_x + x_range * 0.3)
    y_min_plot = min(y_min - y_padding, mid_y - y_range * 0.3)
    y_max_plot = max(y_max + y_padding, mid_y + y_range * 0.3)

    # Cuadrantes con colores claros
    # EMERGENTE: Bajo volumen (izquierda), Alto crecimiento (arriba)
    fig.add_shape(
        type="rect", x0=x_min_plot, y0=mid_y, x1=mid_x, y1=y_max_plot,
        fillcolor="rgba(139, 92, 246, 0.1)", line_width=0
    )
    # ESTRELLA: Alto volumen (derecha), Alto crecimiento (arriba)
    fig.add_shape(
        type="rect", x0=mid_x, y0=mid_y, x1=x_max_plot, y1=y_max_plot,
        fillcolor="rgba(245, 158, 11, 0.1)", line_width=0
    )
    # CONSOLIDADO: Alto volumen (derecha), Bajo crecimiento (abajo)
    fig.add_shape(
        type="rect", x0=mid_x, y0=y_min_plot, x1=x_max_plot, y1=mid_y,
        fillcolor="rgba(59, 130, 246, 0.1)", line_width=0
    )
    # NICHO: Bajo volumen (izquierda), Bajo crecimiento (abajo)
    fig.add_shape(
        type="rect", x0=x_min_plot, y0=y_min_plot, x1=mid_x, y1=mid_y,
        fillcolor="rgba(107, 114, 128, 0.1)", line_width=0
    )

    # Líneas de umbral (las mismas que se usaron para clasificar)
    fig.add_hline(
        y=mid_y, line_dash="dash", line_color="#6B7280", line_width=1.5,
        annotation_text=f"Umbral crecimiento: {mid_y:.1f}%",
        annotation_position="right"
    )
    fig.add_vline(
        x=mid_x, line_dash="dash", line_color="#6B7280", line_width=1.5,
        annotation_text=f"Umbral volumen: {mid_x:.0f}",
        annotation_position="top"
    )

    # Calcular tamaños proporcionales al volumen
    if max(x_values) > min(x_values):
        size_range = max(x_values) - min(x_values)
        sizes = [max(20, min(50, 20 + (v - min(x_values)) / size_range * 30)) for v in x_values]
    else:
        sizes = [30] * len(x_values)

    # Añadir puntos
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='markers+text',
        marker=dict(
            size=sizes,
            color=colors,
            line=dict(width=2, color='white'),
            opacity=0.85
        ),
        text=names,
        textposition="top center",
        textfont=dict(size=10, color="#374151"),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Volumen: %{x:.0f}<br>"
            "Crecimiento: %{y:+.1f}%<br>"
            "<extra></extra>"
        )
    ))

    # Etiquetas de cuadrantes
    label_offset_x = x_range * 0.02
    label_offset_y = y_range * 0.05
    
    fig.add_annotation(
        x=x_min_plot + label_offset_x, y=y_max_plot - label_offset_y, 
        text="🚀 EMERGENTE",
        showarrow=False, font=dict(size=12, color="#8B5CF6", weight="bold"),
        xanchor="left", yanchor="top"
    )
    fig.add_annotation(
        x=x_max_plot - label_offset_x, y=y_max_plot - label_offset_y, 
        text="⭐ ESTRELLA",
        showarrow=False, font=dict(size=12, color="#F59E0B", weight="bold"),
        xanchor="right", yanchor="top"
    )
    fig.add_annotation(
        x=x_max_plot - label_offset_x, y=y_min_plot + label_offset_y, 
        text="💎 CONSOLIDADO",
        showarrow=False, font=dict(size=12, color="#3B82F6", weight="bold"),
        xanchor="right", yanchor="bottom"
    )
    fig.add_annotation(
        x=x_min_plot + label_offset_x, y=y_min_plot + label_offset_y, 
        text="👀 NICHO",
        showarrow=False, font=dict(size=12, color="#6B7280", weight="bold"),
        xanchor="left", yanchor="bottom"
    )

    fig.update_layout(
        title=dict(
            text="Matriz de Oportunidad de Productos",
            font=dict(size=16),
            x=0.5
        ),
        xaxis=dict(
            title="Volumen de búsqueda (índice Google Trends)",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            range=[x_min_plot, x_max_plot],
            zeroline=False
        ),
        yaxis=dict(
            title="Crecimiento (%)",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            range=[y_min_plot, y_max_plot],
            zeroline=True,
            zerolinecolor='rgba(0,0,0,0.2)'
        ),
        showlegend=False,
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Leyenda con conteo por categoría
    col1, col2, col3, col4 = st.columns(4)
    for col, (cat_key, config) in zip([col1, col2, col3, col4], CATEGORY_CONFIG.items()):
        count = len([p for p in products if _get_category(p) == cat_key])
        with col:
            st.markdown(
                f'<div style="background: {config["bg_color"]}; padding: 12px; '
                f'border-radius: 8px; text-align: center; border: 2px solid {config["color"]}20;">'
                f'<div style="font-size: 1.5rem; margin-bottom: 4px;">{config["icon"]}</div>'
                f'<div style="font-weight: 600; color: {config["color"]};">{config["label"]}</div>'
                f'<div style="font-size: 1.25rem; font-weight: 700; color: #1A1A2E;">{count}</div>'
                f'<div style="font-size: 0.75rem; color: #6B7280;">{config["action"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    
    # Mostrar umbrales usados
    if thresholds:
        st.caption(
            f"📊 Umbrales de clasificación: Volumen ≥ {thresholds.get('volume', 0):.0f} | "
            f"Crecimiento ≥ {thresholds.get('growth', 0):.1f}%"
        )


def render_product_ranking(products: List, paginate: bool = False) -> None:
    """Renderiza el ranking de productos con sparklines y paginación opcional"""

    if not products:
        st.info("No hay productos para mostrar")
        return

    # Ordenar por crecimiento
    sorted_products = sorted(
        products,
        key=lambda p: _safe_get(p, 'growth', 0),
        reverse=True
    )

    total = len(sorted_products)
    items_per_page = 10

    # Paginación si hay más de 10 productos y está activada
    if paginate and total > items_per_page:
        total_pages = (total + items_per_page - 1) // items_per_page

        col_info, col_page = st.columns([2, 1])
        with col_info:
            st.caption(f"Mostrando {total} productos ordenados por crecimiento")
        with col_page:
            page = st.selectbox(
                "Página",
                options=list(range(1, total_pages + 1)),
                format_func=lambda x: f"Página {x}/{total_pages}",
                key="product_ranking_page",
                label_visibility="collapsed"
            )

        start_idx = (page - 1) * items_per_page
        display_products = sorted_products[start_idx:start_idx + items_per_page]
        start_rank = start_idx
    else:
        display_products = sorted_products[:items_per_page]
        start_rank = 0
        if total > items_per_page:
            st.caption(f"Mostrando top {items_per_page} de {total} productos")

    for i, product in enumerate(display_products):
        rank = start_rank + i + 1
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

        # Card del producto
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.markdown(
                f'<div style="display: flex; align-items: center; gap: 8px;">'
                f'<span style="color: #9CA3AF; font-weight: 600;">{rank}.</span>'
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
                st.plotly_chart(fig, use_container_width=True, key=f"spark_{name}_{rank}")

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

    # Zonas de color (usando rgba para compatibilidad)
    zones = [
        (0, 20, "rgba(16, 185, 129, 0.12)", "🌱 Lanzamiento"),
        (20, 40, "rgba(245, 158, 11, 0.12)", "📈 Crecimiento"),
        (40, 70, "rgba(59, 130, 246, 0.12)", "🏔️ Madurez"),
        (70, 100, "rgba(239, 68, 68, 0.12)", "📉 Declive")
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

    fill_color = hex_to_rgba(color, 0.2)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=values,
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=fill_color,
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

