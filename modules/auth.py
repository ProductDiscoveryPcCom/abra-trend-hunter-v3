"""
Autenticación simple para Abra Trend Hunter
Sistema de login con contraseña y protección contra brute force
"""

import streamlit as st
import hashlib
import hmac
import time
from typing import Optional
from datetime import datetime, timedelta


# Rate limiting para prevenir brute force
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME_SECONDS = 300  # 5 minutos


def hash_password(password: str) -> str:
    """Genera hash SHA-256 de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()


def _secure_compare(a: str, b: str) -> bool:
    """
    Comparación en tiempo constante para prevenir timing attacks
    """
    return hmac.compare_digest(a.encode(), b.encode())


def _check_rate_limit() -> bool:
    """
    Verifica si el usuario puede intentar login
    Returns: True si puede intentar, False si está bloqueado
    """
    attempts = st.session_state.get("login_attempts", 0)
    last_attempt = st.session_state.get("last_login_attempt", datetime.min)
    
    # Si está bloqueado, verificar si pasó el tiempo
    if attempts >= MAX_LOGIN_ATTEMPTS:
        if isinstance(last_attempt, datetime):
            lockout_until = last_attempt + timedelta(seconds=LOCKOUT_TIME_SECONDS)
            if datetime.now() < lockout_until:
                remaining = (lockout_until - datetime.now()).seconds
                st.error(f"⏳ Demasiados intentos fallidos. Espera {remaining} segundos.")
                return False
            else:
                # Reset después del lockout
                st.session_state["login_attempts"] = 0
    
    return True


def _record_failed_attempt():
    """Registra un intento fallido"""
    attempts = st.session_state.get("login_attempts", 0)
    st.session_state["login_attempts"] = attempts + 1
    st.session_state["last_login_attempt"] = datetime.now()


def check_password() -> bool:
    """
    Verifica si el usuario está autenticado.
    
    Muestra formulario de login si no está autenticado.
    Devuelve True si el acceso está permitido.
    
    Configuración en secrets.toml:
        APP_PASSWORD = "tu_contraseña"
        # O usar hash:
        APP_PASSWORD_HASH = "hash_sha256_de_la_contraseña"
    """
    
    # Verificar si la autenticación está habilitada
    password_plain = st.secrets.get("APP_PASSWORD", "")
    password_hash = st.secrets.get("APP_PASSWORD_HASH", "")
    
    # Si no hay contraseña configurada, permitir acceso
    if not password_plain and not password_hash:
        return True
    
    # Calcular el hash esperado
    if password_plain:
        expected_hash = hash_password(password_plain)
    else:
        expected_hash = password_hash
    
    # Verificar si ya está autenticado en esta sesión
    if st.session_state.get("authenticated", False):
        return True
    
    # Mostrar formulario de login
    _show_login_form(expected_hash)
    
    return st.session_state.get("authenticated", False)


def _show_login_form(expected_hash: str) -> None:
    """Muestra el formulario de login"""
    
    # Verificar rate limit
    if not _check_rate_limit():
        return
    
    # Centrar el formulario
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 60px 0 30px 0;">
            <span style="font-size: 4rem;">🔐</span>
            <h1 style="margin: 20px 0 10px 0; color: #1F2937;">Abra Trend Hunter</h1>
            <p style="color: #6B7280; font-size: 1.1rem;">Introduce la contraseña para acceder</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Formulario
        with st.form("login_form", clear_on_submit=True):
            password = st.text_input(
                "Contraseña",
                type="password",
                placeholder="••••••••",
                label_visibility="collapsed"
            )
            
            submitted = st.form_submit_button(
                "🚀 Entrar",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                # Usar comparación en tiempo constante
                if _secure_compare(hash_password(password), expected_hash):
                    st.session_state["authenticated"] = True
                    st.session_state["login_attempts"] = 0  # Reset
                    st.rerun()
                else:
                    _record_failed_attempt()
                    attempts_left = MAX_LOGIN_ATTEMPTS - st.session_state.get("login_attempts", 0)
                    if attempts_left > 0:
                        st.error(f"❌ Contraseña incorrecta. {attempts_left} intentos restantes.")
                    else:
                        st.error(f"❌ Demasiados intentos. Bloqueado por {LOCKOUT_TIME_SECONDS // 60} minutos.")
        
        # Mensaje de ayuda
        st.markdown("""
        <div style="text-align: center; margin-top: 30px; padding: 20px; 
                    background: #F9FAFB; border-radius: 8px;">
            <p style="color: #9CA3AF; font-size: 0.85rem; margin: 0;">
                ¿No tienes acceso? Contacta al administrador.
            </p>
        </div>
        """, unsafe_allow_html=True)


def logout() -> None:
    """Cierra la sesión actual"""
    st.session_state["authenticated"] = False
    st.rerun()


def render_logout_button() -> None:
    """Renderiza un botón de logout en la barra lateral"""
    
    # Solo mostrar si hay autenticación habilitada
    password_plain = st.secrets.get("APP_PASSWORD", "")
    password_hash = st.secrets.get("APP_PASSWORD_HASH", "")
    
    if not password_plain and not password_hash:
        return
    
    if st.session_state.get("authenticated", False):
        with st.sidebar:
            st.markdown("---")
            if st.button("🚪 Cerrar sesión", use_container_width=True):
                logout()


def require_auth(func):
    """
    Decorador para proteger funciones con autenticación.
    
    Uso:
        @require_auth
        def mi_funcion():
            # código protegido
    """
    def wrapper(*args, **kwargs):
        if check_password():
            return func(*args, **kwargs)
        else:
            st.stop()
    return wrapper


# Utilidad para generar hash de contraseña
def generate_password_hash(password: str) -> str:
    """
    Genera el hash SHA-256 de una contraseña.
    
    Uso desde terminal:
        python -c "from modules.auth import generate_password_hash; print(generate_password_hash('mi_contraseña'))"
    
    Luego añadir a secrets.toml:
        APP_PASSWORD_HASH = "el_hash_generado"
    """
    return hash_password(password)


if __name__ == "__main__":
    # Utilidad de línea de comandos para generar hash
    import sys
    if len(sys.argv) > 1:
        password = sys.argv[1]
        print(f"Hash SHA-256 de '{password}':")
        print(generate_password_hash(password))
    else:
        print("Uso: python auth.py <contraseña>")
        print("Genera el hash SHA-256 para usar en secrets.toml")
