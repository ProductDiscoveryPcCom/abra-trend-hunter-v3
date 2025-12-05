"""
Selector de IA Unificado
Permite elegir el proveedor de IA para cualquier análisis
"""

import streamlit as st
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
import requests


@dataclass
class AIProvider:
    """Configuración de un proveedor de IA"""
    key: str
    name: str
    icon: str
    model: str
    api_key_name: str
    enabled: bool = False


# Proveedores disponibles
AI_PROVIDERS = {
    "claude": AIProvider(
        key="claude",
        name="Claude",
        icon="🟣",
        model="claude-sonnet-4-20250514",
        api_key_name="ANTHROPIC_API_KEY"
    ),
    "openai": AIProvider(
        key="openai", 
        name="GPT-4",
        icon="🟢",
        model="gpt-4o",
        api_key_name="OPENAI_API_KEY"
    ),
    "perplexity": AIProvider(
        key="perplexity",
        name="Perplexity",
        icon="🔵",
        model="sonar-pro",
        api_key_name="PERPLEXITY_API_KEY"
    )
}


def get_available_providers() -> Dict[str, AIProvider]:
    """
    Devuelve los proveedores de IA disponibles (con API key configurada)
    """
    available = {}
    
    for key, provider in AI_PROVIDERS.items():
        api_key = st.secrets.get(provider.api_key_name, "")
        if api_key:
            provider.enabled = True
            available[key] = provider
    
    return available


def get_current_provider() -> Optional[str]:
    """Obtiene el proveedor actual seleccionado"""
    return st.session_state.get("selected_ai_provider", None)


def set_current_provider(provider_key: str) -> None:
    """Establece el proveedor actual"""
    st.session_state["selected_ai_provider"] = provider_key


def render_ai_provider_selector(
    key: str = "ai_selector",
    label: str = "🤖 Proveedor IA",
    show_status: bool = True,
    compact: bool = False
) -> Optional[str]:
    """
    Renderiza un selector de proveedor de IA.
    
    Args:
        key: Key único para el widget
        label: Etiqueta del selector
        show_status: Mostrar estado de conexión
        compact: Modo compacto (solo iconos)
    
    Returns:
        Key del proveedor seleccionado o None si no hay ninguno disponible
    """
    available = get_available_providers()
    
    if not available:
        st.warning("⚠️ No hay APIs de IA configuradas. Añade al menos una en secrets.toml")
        return None
    
    # Obtener proveedor actual o usar el primero disponible
    current = get_current_provider()
    if current not in available:
        current = list(available.keys())[0]
        set_current_provider(current)
    
    if compact:
        # Modo compacto: botones con iconos
        cols = st.columns(len(available))
        for i, (pkey, provider) in enumerate(available.items()):
            with cols[i]:
                is_selected = pkey == current
                button_type = "primary" if is_selected else "secondary"
                if st.button(
                    f"{provider.icon}",
                    key=f"{key}_{pkey}",
                    type=button_type,
                    help=provider.name,
                    use_container_width=True
                ):
                    set_current_provider(pkey)
                    st.rerun()
    else:
        # Modo normal: selectbox
        options = list(available.keys())
        format_func = lambda x: f"{available[x].icon} {available[x].name}"
        
        selected = st.selectbox(
            label,
            options=options,
            index=options.index(current) if current in options else 0,
            format_func=format_func,
            key=key
        )
        
        if selected != current:
            set_current_provider(selected)
    
    # Mostrar estado
    if show_status and current:
        provider = available[current]
        st.caption(f"Modelo: `{provider.model}`")
    
    return current


def render_inline_ai_selector(key: str = "inline_ai") -> Optional[str]:
    """
    Renderiza un selector de IA en línea (horizontal, compacto)
    Para usar junto a botones de análisis
    
    Returns:
        Key del proveedor seleccionado
    """
    available = get_available_providers()
    
    if not available:
        return None
    
    current = get_current_provider()
    if current not in available:
        current = list(available.keys())[0]
        set_current_provider(current)
    
    # Radio horizontal
    options = list(available.keys())
    format_func = lambda x: f"{available[x].icon} {available[x].name}"
    
    selected = st.radio(
        "IA",
        options=options,
        index=options.index(current) if current in options else 0,
        format_func=format_func,
        horizontal=True,
        key=key,
        label_visibility="collapsed"
    )
    
    if selected != current:
        set_current_provider(selected)
    
    return selected


def call_ai(
    prompt: str,
    system_prompt: str = "",
    provider: str = None,
    max_tokens: int = 2000,
    temperature: float = 0.3
) -> Dict[str, Any]:
    """
    Llama a la IA seleccionada con el prompt dado.
    
    Args:
        prompt: Prompt del usuario
        system_prompt: Prompt del sistema (opcional)
        provider: Proveedor específico (o usa el seleccionado)
        max_tokens: Máximo de tokens en respuesta
        temperature: Temperatura (creatividad)
    
    Returns:
        Dict con 'success', 'content', 'provider', 'error'
    """
    # Determinar proveedor
    if provider is None:
        provider = get_current_provider()
    
    if provider is None:
        available = get_available_providers()
        if available:
            provider = list(available.keys())[0]
        else:
            return {
                "success": False,
                "error": "No hay proveedores de IA disponibles",
                "content": ""
            }
    
    # Llamar al proveedor correspondiente
    if provider == "claude":
        return _call_claude(prompt, system_prompt, max_tokens, temperature)
    elif provider == "openai":
        return _call_openai(prompt, system_prompt, max_tokens, temperature)
    elif provider == "perplexity":
        return _call_perplexity(prompt, system_prompt, max_tokens, temperature)
    else:
        return {
            "success": False,
            "error": f"Proveedor desconocido: {provider}",
            "content": ""
        }


def _call_claude(
    prompt: str,
    system_prompt: str,
    max_tokens: int,
    temperature: float
) -> Dict[str, Any]:
    """Llama a Claude API"""
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "ANTHROPIC_API_KEY no configurada", "content": ""}
    
    try:
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", [{}])[0].get("text", "")
            return {"success": True, "content": content, "provider": "claude"}
        else:
            return {
                "success": False,
                "error": f"Claude API error: {response.status_code}",
                "content": ""
            }
    except Exception as e:
        return {"success": False, "error": str(e), "content": ""}


def _call_openai(
    prompt: str,
    system_prompt: str,
    max_tokens: int,
    temperature: float
) -> Dict[str, Any]:
    """Llama a OpenAI API"""
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "OPENAI_API_KEY no configurada", "content": ""}
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "gpt-4o",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"success": True, "content": content, "provider": "openai"}
        else:
            return {
                "success": False,
                "error": f"OpenAI API error: {response.status_code}",
                "content": ""
            }
    except Exception as e:
        return {"success": False, "error": str(e), "content": ""}


def _call_perplexity(
    prompt: str,
    system_prompt: str,
    max_tokens: int,
    temperature: float
) -> Dict[str, Any]:
    """Llama a Perplexity API"""
    api_key = st.secrets.get("PERPLEXITY_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "PERPLEXITY_API_KEY no configurada", "content": ""}
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "sonar-pro",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = data.get("citations", [])
            return {
                "success": True,
                "content": content,
                "provider": "perplexity",
                "citations": citations
            }
        else:
            return {
                "success": False,
                "error": f"Perplexity API error: {response.status_code}",
                "content": ""
            }
    except Exception as e:
        return {"success": False, "error": str(e), "content": ""}


def render_ai_analysis_button(
    label: str = "🧠 Analizar con IA",
    key: str = "ai_analysis_btn",
    show_provider_selector: bool = True,
    help_text: str = None
) -> tuple:
    """
    Renderiza un botón de análisis con selector de IA integrado.
    
    Args:
        label: Texto del botón
        key: Key único
        show_provider_selector: Mostrar selector de proveedor
        help_text: Texto de ayuda
    
    Returns:
        Tuple (clicked: bool, provider: str)
    """
    available = get_available_providers()
    
    if not available:
        st.warning("⚠️ Configura al menos una API de IA en secrets.toml")
        return False, None
    
    col1, col2 = st.columns([2, 1]) if show_provider_selector else (st.container(), None)
    
    with col1:
        clicked = st.button(
            label,
            key=key,
            type="primary",
            use_container_width=True,
            help=help_text
        )
    
    if show_provider_selector and col2:
        with col2:
            provider = render_inline_ai_selector(key=f"{key}_provider")
    else:
        provider = get_current_provider()
    
    return clicked, provider


# Widget compacto para sidebar
def render_sidebar_ai_selector() -> Optional[str]:
    """Renderiza el selector de IA en el sidebar"""
    st.markdown("#### 🤖 Proveedor IA")
    
    available = get_available_providers()
    
    if not available:
        st.caption("No hay APIs configuradas")
        return None
    
    current = get_current_provider()
    if current not in available:
        current = list(available.keys())[0]
        set_current_provider(current)
    
    # Lista de proveedores con estado
    for pkey, provider in available.items():
        is_selected = pkey == current
        
        if is_selected:
            st.markdown(
                f'<div style="padding: 8px; background: #6366F120; '
                f'border-radius: 8px; border-left: 3px solid #6366F1;">'
                f'{provider.icon} <b>{provider.name}</b></div>',
                unsafe_allow_html=True
            )
        else:
            if st.button(
                f"{provider.icon} {provider.name}",
                key=f"sidebar_ai_{pkey}",
                use_container_width=True
            ):
                set_current_provider(pkey)
                st.rerun()
    
    return current
