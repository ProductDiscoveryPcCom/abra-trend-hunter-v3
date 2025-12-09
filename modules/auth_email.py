"""
Email Authentication Module
Autenticación basada en lista de emails autorizados en Supabase
"""

import streamlit as st
from typing import Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _get_fallback_emails() -> List[str]:
    """
    Obtiene emails de fallback desde secrets.
    NUNCA hardcodear emails en el código fuente.
    
    En secrets.toml:
    [AUTH]
    FALLBACK_EMAILS = ["email1@domain.com", "email2@domain.com"]
    """
    try:
        # st.secrets puede lanzar excepciones si la key no existe
        if "AUTH" in st.secrets and "FALLBACK_EMAILS" in st.secrets["AUTH"]:
            emails = st.secrets["AUTH"]["FALLBACK_EMAILS"]
            if emails:
                return list(emails)
    except Exception as e:
        logger.debug(f"No se pudieron obtener FALLBACK_EMAILS: {e}")
    
    # Si no hay secrets configurados, retornar lista vacía
    # Los usuarios DEBEN estar en Supabase
    return []


def get_supabase_client():
    """Obtiene cliente de Supabase si está configurado"""
    try:
        from supabase import create_client, Client
        
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        
        if url and key:
            return create_client(url, key)
    except ImportError:
        logger.warning("Supabase no instalado, usando fallback local")
    except Exception as e:
        logger.warning(f"Error conectando a Supabase: {e}")
    
    return None


def is_email_authorized(email: str) -> bool:
    """
    Verifica si un email está autorizado para usar la app
    
    Args:
        email: Email a verificar
    
    Returns:
        True si está autorizado, False si no
    """
    if not email:
        return False
    
    email = email.lower().strip()
    
    # Intentar verificar en Supabase
    client = get_supabase_client()
    
    if client:
        try:
            result = client.table("authorized_users").select("email, is_active").eq("email", email).eq("is_active", True).execute()
            
            if result.data and len(result.data) > 0:
                # Actualizar último login
                client.table("authorized_users").update({"last_login": datetime.now().isoformat()}).eq("email", email).execute()
                return True
            return False
            
        except Exception as e:
            logger.warning(f"Error verificando en Supabase: {e}, usando fallback")
    
    # Fallback: verificar en lista desde secrets
    fallback_emails = _get_fallback_emails()
    return email in [e.lower() for e in fallback_emails]


def get_user_info(email: str) -> Optional[Dict]:
    """
    Obtiene información del usuario autorizado
    
    Args:
        email: Email del usuario
    
    Returns:
        Dict con info del usuario o None
    """
    if not email:
        return None
    
    email = email.lower().strip()
    client = get_supabase_client()
    
    if client:
        try:
            result = client.table("authorized_users").select("*").eq("email", email).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
        except Exception as e:
            logger.warning(f"Error obteniendo info de usuario: {e}")
    
    # Fallback
    if email in [e.lower() for e in AUTHORIZED_EMAILS_FALLBACK]:
        return {
            "email": email,
            "name": email.split("@")[0].replace(".", " ").title(),
            "department": "Product Discovery"
        }
    
    return None


def log_search(
    user_email: str,
    keyword: str,
    country: str = "ES",
    timeframe: str = "today 12-m",
    trend_score: int = None,
    potential_score: int = None
) -> bool:
    """
    Registra una búsqueda en el log
    
    Args:
        user_email: Email del usuario
        keyword: Keyword buscada
        country: País de la búsqueda
        timeframe: Período de tiempo
        trend_score: Score de tendencia (opcional)
        potential_score: Score de potencial (opcional)
    
    Returns:
        True si se registró correctamente
    """
    client = get_supabase_client()
    
    if not client:
        return False
    
    try:
        client.table("search_logs").insert({
            "user_email": user_email.lower().strip(),
            "keyword": keyword,
            "country": country,
            "timeframe": timeframe,
            "trend_score": trend_score,
            "potential_score": potential_score
        }).execute()
        return True
    except Exception as e:
        logger.warning(f"Error registrando búsqueda: {e}")
        return False


def get_user_search_history(email: str, limit: int = 20) -> List[Dict]:
    """
    Obtiene historial de búsquedas de un usuario
    
    Args:
        email: Email del usuario
        limit: Número máximo de resultados
    
    Returns:
        Lista de búsquedas
    """
    client = get_supabase_client()
    
    if not client:
        return []
    
    try:
        result = client.table("search_logs").select("*").eq("user_email", email.lower()).order("searched_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception as e:
        logger.warning(f"Error obteniendo historial: {e}")
        return []


def render_email_login() -> bool:
    """
    Renderiza el formulario de login por email con diseño mejorado
    
    Returns:
        True si el usuario está autenticado
    """
    # Verificar si ya está autenticado
    if st.session_state.get("authenticated") and st.session_state.get("user_email"):
        return True
    
    # CSS personalizado para login
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 40px;
        background: linear-gradient(135deg, #FAFAFA 0%, #F3F4F6 100%);
        border-radius: 24px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        text-align: center;
    }
    .login-logo {
        width: 120px;
        height: 120px;
        margin: 0 auto 24px;
        background: linear-gradient(135deg, #F5C518 0%, #7C3AED 100%);
        border-radius: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3.5rem;
        box-shadow: 0 8px 24px rgba(124, 58, 237, 0.3);
    }
    .login-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1A1A2E;
        margin-bottom: 8px;
    }
    .login-subtitle {
        color: #6B7280;
        font-size: 0.9rem;
        margin-bottom: 32px;
    }
    .login-features {
        display: flex;
        justify-content: center;
        gap: 24px;
        margin: 24px 0;
        flex-wrap: wrap;
    }
    .login-feature {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #4B5563;
        font-size: 0.85rem;
    }
    .login-footer {
        margin-top: 32px;
        padding-top: 24px;
        border-top: 1px solid #E5E7EB;
        color: #9CA3AF;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Centrar contenido
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Logo - cargar imagen de Abra
        from pathlib import Path
        import base64
        import os
        
        logo_loaded = False
        
        # Rutas posibles (incluyendo Streamlit Cloud)
        possible_paths = [
            Path(__file__).parent.parent / "assets" / "images" / "abra_mascot.png",
            Path("assets/images/abra_mascot.png"),
            Path("./assets/images/abra_mascot.png"),
        ]
        
        # Añadir ruta de Streamlit Cloud si existe
        if os.path.exists("/mount/src"):
            for subdir in os.listdir("/mount/src"):
                cloud_path = Path(f"/mount/src/{subdir}/assets/images/abra_mascot.png")
                if cloud_path.exists():
                    possible_paths.insert(0, cloud_path)
                    break
        
        for logo_path in possible_paths:
            if logo_path.exists():
                try:
                    with open(logo_path, "rb") as f:
                        logo_base64 = base64.b64encode(f.read()).decode()
                    st.markdown(f'''
                    <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                        <img src="data:image/png;base64,{logo_base64}" 
                             style="width: 120px; height: 120px; object-fit: contain;">
                    </div>
                    ''', unsafe_allow_html=True)
                    logo_loaded = True
                    break
                except Exception as e:
                    pass
        
        if not logo_loaded:
            # Fallback: emoji con gradiente
            st.markdown('<div class="login-logo">🔮</div>', unsafe_allow_html=True)
        
        # Título
        st.markdown("""
        <div class="login-title">Abra Trend Hunter</div>
        <div class="login-subtitle">Inteligencia de Tendencias para PCComponentes</div>
        """, unsafe_allow_html=True)
        
        # Features
        st.markdown("""
        <div class="login-features">
            <div class="login-feature">📊 Análisis de tendencias</div>
            <div class="login-feature">🎯 Detección de oportunidades</div>
            <div class="login-feature">🤖 Insights con IA</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Campo de email
        email = st.text_input(
            "Email corporativo",
            placeholder="tu.email@empresa.com",
            key="login_email",
            label_visibility="collapsed"
        )
        
        # Botón de acceso
        if st.button("🚀 Acceder", type="primary", use_container_width=True):
            if not email:
                st.error("Por favor, introduce tu email")
                return False
            
            email = email.lower().strip()
            
            # Verificar formato básico
            if "@" not in email:
                st.error("Email no válido")
                return False
            
            # Verificar si está autorizado
            with st.spinner("Verificando acceso..."):
                if is_email_authorized(email):
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = email
                    st.session_state["user_info"] = get_user_info(email)
                    st.success("✅ ¡Bienvenido!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Email no autorizado")
                    st.info("💡 Contacta con Product Discovery si necesitas acceso.")
                    return False
        
        # Footer
        st.markdown("""
        <div class="login-footer">
            🔒 Acceso restringido a usuarios autorizados<br>
            Product Discovery & Content © 2025
        </div>
        </div>
        """, unsafe_allow_html=True)
    
    return False


def render_user_badge() -> None:
    """Muestra badge del usuario logueado en el sidebar con avatar"""
    if not st.session_state.get("authenticated"):
        return
    
    user_info = st.session_state.get("user_info", {})
    email = st.session_state.get("user_email", "")
    name = user_info.get("name", email.split("@")[0].replace(".", " ").title())
    
    # Obtener iniciales para avatar
    parts = name.split()
    if len(parts) >= 2:
        initials = parts[0][0].upper() + parts[-1][0].upper()
    else:
        initials = name[:2].upper()
    
    # Generar color basado en el email (consistente)
    color_index = sum(ord(c) for c in email) % 5
    colors = ["#7C3AED", "#F59E0B", "#10B981", "#3B82F6", "#EF4444"]
    avatar_color = colors[color_index]
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {avatar_color}15 0%, {avatar_color}08 100%);
        padding: 16px;
        border-radius: 16px;
        margin-bottom: 16px;
        border: 1px solid {avatar_color}30;
    ">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="
                width: 44px;
                height: 44px;
                background: linear-gradient(135deg, {avatar_color} 0%, {avatar_color}CC 100%);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 700;
                font-size: 1rem;
                box-shadow: 0 4px 12px {avatar_color}40;
            ">{initials}</div>
            <div style="flex: 1; min-width: 0;">
                <div style="color: #1A1A2E; font-weight: 600; font-size: 0.9rem; 
                            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {name}
                </div>
                <div style="color: #6B7280; font-size: 0.7rem;
                            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {email}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_api_usage_badge() -> None:
    """Muestra el uso de APIs en la sesión actual"""
    try:
        from modules.api_usage import get_session_usage_summary
        summary = get_session_usage_summary()
        
        if summary["total_calls"] == 0:
            return
        
        total_cost = summary["total_cost_eur"]
        
        # Determinar color según coste
        if total_cost < 0.10:
            cost_color = "#10B981"
            cost_icon = "🟢"
        elif total_cost < 0.50:
            cost_color = "#F59E0B"
            cost_icon = "🟡"
        else:
            cost_color = "#EF4444"
            cost_icon = "🔴"
        
        st.markdown(f"""
        <div style="
            background: #F9FAFB;
            padding: 12px;
            border-radius: 12px;
            margin-bottom: 16px;
            border: 1px solid #E5E7EB;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #6B7280; font-size: 0.75rem; font-weight: 500;">
                    📊 Uso APIs (sesión)
                </span>
                <span style="color: {cost_color}; font-weight: 700; font-size: 0.85rem;">
                    {cost_icon} €{total_cost:.4f}
                </span>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        """, unsafe_allow_html=True)
        
        api_icons = {
            "serpapi": "🔍",
            "claude": "🤖",
            "openai": "💚",
            "perplexity": "🌐"
        }
        
        badges_html = []
        for api, data in summary["by_api"].items():
            icon = api_icons.get(api, "📡")
            cached = f" ({data['cached']}💾)" if data['cached'] > 0 else ""
            badges_html.append(
                f'<span style="background: #E5E7EB; padding: 2px 8px; border-radius: 6px; '
                f'font-size: 0.7rem; color: #4B5563;">'
                f'{icon} {data["calls"]}{cached}</span>'
            )
        
        st.markdown(" ".join(badges_html) + "</div></div>", unsafe_allow_html=True)
    except Exception:
        pass  # Silenciar errores de logging


def render_logout_button() -> None:
    """Renderiza botón de cerrar sesión con estilo mejorado"""
    if st.session_state.get("authenticated"):
        if st.button("🚪 Cerrar sesión", use_container_width=True, type="secondary"):
            st.session_state["authenticated"] = False
            st.session_state["user_email"] = None
            st.session_state["user_info"] = None
            # Limpiar historial de búsquedas de la sesión
            if "search_history" in st.session_state:
                del st.session_state["search_history"]
            if "api_usage_session" in st.session_state:
                del st.session_state["api_usage_session"]
            st.rerun()


def render_search_history() -> Optional[str]:
    """
    Muestra historial de búsquedas recientes en el sidebar
    
    Returns:
        Keyword seleccionado del historial o None
    """
    history = st.session_state.get("search_history", [])
    
    if not history:
        return None
    
    # Mostrar solo las últimas 5 búsquedas únicas
    unique_history = []
    seen = set()
    for item in reversed(history):
        # Manejar diferentes formatos de historial
        if isinstance(item, str):
            # Formato antiguo: solo string
            key = item.lower().strip()
            item = {"keyword": item, "country": "ES", "trend_score": 0}
        elif isinstance(item, dict):
            # Formato nuevo: diccionario
            keyword_val = item.get("keyword")
            if keyword_val is None:
                continue
            key = str(keyword_val).lower().strip()
        else:
            continue
        
        if key and key not in seen:
            seen.add(key)
            unique_history.append(item)
            if len(unique_history) >= 5:
                break
    
    if not unique_history:
        return None
    
    st.markdown("""
    <div style="
        background: #F9FAFB;
        padding: 12px;
        border-radius: 12px;
        margin-bottom: 16px;
        border: 1px solid #E5E7EB;
    ">
        <div style="color: #6B7280; font-size: 0.75rem; font-weight: 500; margin-bottom: 8px;">
            🕐 Búsquedas recientes
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    selected = None
    for item in unique_history:
        keyword = str(item.get("keyword", ""))
        country = str(item.get("country", "ES"))
        trend_score = item.get("trend_score", 0) or 0
        
        # Determinar icono según score
        if trend_score >= 70:
            score_icon = "🔥"
        elif trend_score >= 40:
            score_icon = "📈"
        else:
            score_icon = "📊"
        
        # Botón compacto con texto truncado y tooltip
        col1, col2 = st.columns([4, 1])
        with col1:
            display_text = keyword[:18] + "..." if len(keyword) > 18 else keyword
            if st.button(
                f"{score_icon} {display_text}",
                key=f"history_{keyword}_{country}",
                use_container_width=True,
                help=keyword  # Tooltip con texto completo
            ):
                selected = keyword
        with col2:
            st.caption(country)
    
    return selected


def add_to_search_history(keyword: str, country: str, trend_score: int = 0, potential_score: int = 0) -> None:
    """
    Añade una búsqueda al historial de la sesión
    
    Args:
        keyword: Keyword buscado
        country: País de la búsqueda
        trend_score: Score de tendencia
        potential_score: Score de potencial
    """
    if "search_history" not in st.session_state:
        st.session_state["search_history"] = []
    
    # Añadir al historial
    st.session_state["search_history"].append({
        "keyword": keyword,
        "country": country,
        "trend_score": trend_score,
        "potential_score": potential_score,
        "timestamp": datetime.now().isoformat()
    })
    
    # Limitar a 20 búsquedas
    if len(st.session_state["search_history"]) > 20:
        st.session_state["search_history"] = st.session_state["search_history"][-20:]


def get_current_user_email() -> Optional[str]:
    """Obtiene el email del usuario actual"""
    return st.session_state.get("user_email")


def require_auth(func):
    """
    Decorador para requerir autenticación
    
    Usage:
        @require_auth
        def my_protected_function():
            ...
    """
    def wrapper(*args, **kwargs):
        if not st.session_state.get("authenticated"):
            st.warning("Debes iniciar sesión para acceder a esta función")
            return None
        return func(*args, **kwargs)
    return wrapper
