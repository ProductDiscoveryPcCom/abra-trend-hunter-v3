"""
Email Authentication Module
Autenticación basada en lista de emails autorizados en Supabase
"""

import streamlit as st
from typing import Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# Lista de emails autorizados (fallback si Supabase no está disponible)
AUTHORIZED_EMAILS_FALLBACK = [
    "pablo.gonzalez@pccomponentes.com",
    "product.discovery@pccomponentes.com",
    "paula.ferriz@pccomponentes.com",
    "minerva.sanchez@pccomponentes.com",
    "claudia.vidal@pccomponentes.com",
    "araceli.rodriguez@pccomponentes.com",
    "maximo.sanchez@pccomponentes.com",
    "ja.montesinos@pccomponentes.com",
]


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
    
    # Fallback: verificar en lista local
    return email in [e.lower() for e in AUTHORIZED_EMAILS_FALLBACK]


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
    Renderiza el formulario de login por email
    
    Returns:
        True si el usuario está autenticado
    """
    # Verificar si ya está autenticado
    if st.session_state.get("authenticated") and st.session_state.get("user_email"):
        return True
    
    # Centrar contenido
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Mostrar imagen de Abra
        try:
            st.image("assets/images/abra_mascot.png", width=150, use_container_width=False)
        except:
            st.markdown('<span style="font-size: 4rem;">🔮</span>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="margin: 0 0 8px 0; font-size: 1.75rem;">Abra Trend Hunter</h1>
            <p style="color: #6B7280;">PCComponentes - Product Discovery</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 📧 Acceso con email corporativo")
        
        email = st.text_input(
            "Email",
            placeholder="tu.nombre@pccomponentes.com",
            key="login_email",
            label_visibility="collapsed"
        )
        
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
            if is_email_authorized(email):
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = email
                st.session_state["user_info"] = get_user_info(email)
                st.success("✅ Acceso concedido")
                st.rerun()
            else:
                st.error("❌ Email no autorizado")
                st.info("Contacta con el administrador si necesitas acceso.")
                return False
        
        st.markdown("---")
        st.caption("Solo usuarios autorizados de PCComponentes pueden acceder.")
    
    return False


def render_user_badge() -> None:
    """Muestra badge del usuario logueado en el sidebar"""
    if not st.session_state.get("authenticated"):
        return
    
    user_info = st.session_state.get("user_info", {})
    email = st.session_state.get("user_email", "")
    name = user_info.get("name", email.split("@")[0].replace(".", " ").title())
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%);
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 16px;
    ">
        <div style="color: white; font-weight: 600; font-size: 0.9rem;">
            👤 {name}
        </div>
        <div style="color: rgba(255,255,255,0.7); font-size: 0.75rem;">
            {email}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_logout_button() -> None:
    """Renderiza botón de cerrar sesión"""
    if st.session_state.get("authenticated"):
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["user_email"] = None
            st.session_state["user_info"] = None
            st.rerun()


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
