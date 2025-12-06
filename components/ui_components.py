"""
UI Components - Componentes de interfaz reutilizables
"""

import streamlit as st
from typing import List, Optional, Callable
import html


def render_empty_state(
    title: str,
    message: str,
    icon: str = "📭",
    suggestions: List[str] = None,
    action_label: str = None,
    action_key: str = None,
    compact: bool = False
) -> bool:
    """
    Renderiza un estado vacío con estilo consistente.
    
    Args:
        title: Título del estado vacío
        message: Mensaje descriptivo
        icon: Emoji para el icono
        suggestions: Lista de sugerencias opcionales
        action_label: Texto del botón de acción (opcional)
        action_key: Key único para el botón (requerido si hay action_label)
        compact: Si True, usa versión compacta
    
    Returns:
        True si se hizo clic en el botón de acción, False en caso contrario
    """
    title_escaped = html.escape(str(title))
    message_escaped = html.escape(str(message))
    
    if compact:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #F9FAFB; 
             border-radius: 8px; border: 1px dashed #E5E7EB;">
            <span style="font-size: 1.5rem;">{icon}</span>
            <p style="color: #6B7280; margin: 8px 0 0; font-size: 0.9rem;">{message_escaped}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="text-align: center; padding: 40px 20px; background: #F9FAFB; 
             border-radius: 12px; border: 2px dashed #E5E7EB; margin: 16px 0;">
            <div style="font-size: 3rem; margin-bottom: 12px;">{icon}</div>
            <h3 style="margin: 0 0 8px; color: #374151; font-weight: 600;">{title_escaped}</h3>
            <p style="color: #6B7280; margin: 0; font-size: 0.95rem;">{message_escaped}</p>
        </div>
        """, unsafe_allow_html=True)
    
    if suggestions:
        st.markdown("**💡 Sugerencias:**")
        for s in suggestions:
            st.markdown(f"- {html.escape(str(s))}")
    
    if action_label and action_key:
        return st.button(action_label, key=action_key, type="primary")
    
    return False


def render_info_card(
    title: str,
    value: str,
    subtitle: str = "",
    icon: str = "",
    color: str = "#6366F1",
    delta: str = None,
    delta_color: str = None
):
    """
    Renderiza una tarjeta de información con estilo.
    
    Args:
        title: Título de la tarjeta
        value: Valor principal
        subtitle: Texto secundario opcional
        icon: Emoji para el icono
        color: Color de acento
        delta: Cambio/delta opcional (ej: "+15%")
        delta_color: Color del delta (verde/rojo)
    """
    title_escaped = html.escape(str(title))
    value_escaped = html.escape(str(value))
    subtitle_escaped = html.escape(str(subtitle)) if subtitle else ""
    
    delta_html = ""
    if delta:
        delta_escaped = html.escape(str(delta))
        d_color = delta_color or ("#10B981" if delta.startswith("+") else "#EF4444")
        delta_html = f'<span style="font-size: 0.8rem; color: {d_color}; margin-left: 8px;">{delta_escaped}</span>'
    
    st.markdown(f"""
    <div style="background: white; border-radius: 12px; padding: 16px;
         box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid {color};">
        <div style="display: flex; align-items: center; gap: 8px;">
            {f'<span style="font-size: 1.2rem;">{icon}</span>' if icon else ''}
            <span style="font-size: 0.85rem; color: #6B7280;">{title_escaped}</span>
        </div>
        <div style="font-size: 1.5rem; font-weight: 700; color: #1F2937; margin: 4px 0;">
            {value_escaped}{delta_html}
        </div>
        {f'<div style="font-size: 0.75rem; color: #9CA3AF;">{subtitle_escaped}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def render_status_badge(
    text: str,
    status: str = "info",  # "success", "warning", "error", "info"
    icon: str = None
):
    """
    Renderiza un badge de estado.
    
    Args:
        text: Texto del badge
        status: Tipo de estado
        icon: Icono opcional
    """
    colors = {
        "success": {"bg": "#D1FAE5", "text": "#065F46", "icon": "✅"},
        "warning": {"bg": "#FEF3C7", "text": "#92400E", "icon": "⚠️"},
        "error": {"bg": "#FEE2E2", "text": "#991B1B", "icon": "❌"},
        "info": {"bg": "#DBEAFE", "text": "#1E40AF", "icon": "ℹ️"}
    }
    
    style = colors.get(status, colors["info"])
    display_icon = icon or style["icon"]
    text_escaped = html.escape(str(text))
    
    st.markdown(f"""
    <span style="display: inline-flex; align-items: center; gap: 4px;
         background: {style['bg']}; color: {style['text']}; 
         padding: 4px 12px; border-radius: 9999px; font-size: 0.85rem; font-weight: 500;">
        {display_icon} {text_escaped}
    </span>
    """, unsafe_allow_html=True)


def render_progress_steps(
    steps: List[str],
    current_step: int,
    show_labels: bool = True
):
    """
    Renderiza un indicador de progreso con pasos.
    
    Args:
        steps: Lista de nombres de pasos
        current_step: Índice del paso actual (0-based)
        show_labels: Si mostrar etiquetas de pasos
    """
    total = len(steps)
    progress = (current_step + 1) / total
    
    # Barra de progreso
    st.progress(progress)
    
    if show_labels:
        cols = st.columns(total)
        for i, (col, step) in enumerate(zip(cols, steps)):
            with col:
                if i < current_step:
                    st.markdown(f"<div style='text-align:center; color:#10B981; font-size:0.75rem;'>✅ {step}</div>", unsafe_allow_html=True)
                elif i == current_step:
                    st.markdown(f"<div style='text-align:center; color:#6366F1; font-size:0.75rem; font-weight:600;'>⏳ {step}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align:center; color:#9CA3AF; font-size:0.75rem;'>○ {step}</div>", unsafe_allow_html=True)


def render_feature_coming_soon(feature_name: str, description: str = ""):
    """
    Placeholder para características próximas.
    
    Args:
        feature_name: Nombre de la característica
        description: Descripción opcional
    """
    render_empty_state(
        title=f"{feature_name}",
        message=description or "Esta característica estará disponible próximamente.",
        icon="🚧",
        compact=True
    )


def render_api_required(
    api_name: str,
    secret_key: str,
    feature_description: str = ""
):
    """
    Muestra mensaje cuando falta una API.
    
    Args:
        api_name: Nombre de la API
        secret_key: Nombre del secret a configurar
        feature_description: Qué hace esta característica
    """
    render_empty_state(
        title=f"{api_name} no configurada",
        message=feature_description or f"Configura {api_name} para habilitar esta función.",
        icon="🔑",
        suggestions=[
            f"Ve a Settings > Secrets",
            f"Añade: {secret_key} = 'tu_api_key'",
            "Recarga la página"
        ]
    )


def render_loading_placeholder(message: str = "Cargando...", height: int = 200):
    """
    Placeholder de carga.
    
    Args:
        message: Mensaje de carga
        height: Altura del placeholder
    """
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; 
         justify-content: center; height: {height}px; background: #F9FAFB;
         border-radius: 8px; border: 1px solid #E5E7EB;">
        <div class="loading-spinner" style="width: 40px; height: 40px; 
             border: 3px solid #E5E7EB; border-top-color: #6366F1;
             border-radius: 50%; animation: spin 1s linear infinite;"></div>
        <p style="color: #6B7280; margin-top: 12px; font-size: 0.9rem;">{html.escape(message)}</p>
    </div>
    <style>
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
    </style>
    """, unsafe_allow_html=True)
