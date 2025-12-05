"""
AI Provider Selector
Selector unificado de proveedor de IA para toda la aplicación

Soporta:
- Claude (Anthropic)
- GPT-4 (OpenAI)
- Perplexity (con búsqueda web)
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import requests


@dataclass
class AIProviderInfo:
    """Información de un proveedor de IA"""
    id: str
    name: str
    icon: str
    color: str
    model: str
    description: str
    strengths: List[str]
    weaknesses: List[str]
    best_for: List[str]
    cost_tier: str  # "low", "medium", "high"


# Configuración de proveedores
AI_PROVIDERS = {
    "claude": AIProviderInfo(
        id="claude",
        name="Claude",
        icon="🟣",
        color="#8B5CF6",
        model="claude-sonnet-4-20250514",
        description="Modelo de Anthropic, excelente para análisis detallado y razonamiento",
        strengths=[
            "Análisis profundo y matizado",
            "Excelente seguimiento de instrucciones",
            "Respuestas bien estructuradas",
            "Bueno con contexto largo"
        ],
        weaknesses=[
            "Sin acceso a internet en tiempo real",
            "Puede ser más lento que otros modelos",
            "Knowledge cutoff mayo 2025"
        ],
        best_for=[
            "Análisis estratégico",
            "Documentación detallada",
            "Razonamiento complejo"
        ],
        cost_tier="medium"
    ),
    "openai": AIProviderInfo(
        id="openai",
        name="GPT-4o",
        icon="🟢",
        color="#10B981",
        model="gpt-4o",
        description="Modelo de OpenAI, rápido y versátil",
        strengths=[
            "Muy rápido",
            "Buena calidad general",
            "Amplio conocimiento",
            "Bueno con código"
        ],
        weaknesses=[
            "Sin acceso a internet en tiempo real",
            "Puede ser menos preciso en detalles",
            "Tendencia a respuestas genéricas"
        ],
        best_for=[
            "Respuestas rápidas",
            "Tareas generales",
            "Generación de contenido"
        ],
        cost_tier="medium"
    ),
    "perplexity": AIProviderInfo(
        id="perplexity",
        name="Perplexity",
        icon="🔵",
        color="#3B82F6",
        model="sonar-pro",
        description="IA con búsqueda web en tiempo real, ideal para información actual",
        strengths=[
            "Acceso a internet en tiempo real",
            "Información actualizada",
            "Proporciona fuentes/citas",
            "Ideal para datos de mercado"
        ],
        weaknesses=[
            "Depende de calidad de resultados web",
            "Puede ser más caro por búsquedas",
            "Menos control sobre el razonamiento"
        ],
        best_for=[
            "Análisis de mercado actual",
            "Información de productos",
            "Datos en tiempo real",
            "Verificación de hechos"
        ],
        cost_tier="medium"
    )
}


class AIProviderManager:
    """
    Gestor centralizado de proveedores de IA
    """
    
    def __init__(self):
        self._current_provider = None
        self._available_providers = []
        self._check_availability()
    
    def _check_availability(self):
        """Verifica qué proveedores están disponibles"""
        self._available_providers = []
        
        if st.secrets.get("ANTHROPIC_API_KEY"):
            self._available_providers.append("claude")
        
        if st.secrets.get("OPENAI_API_KEY"):
            self._available_providers.append("openai")
        
        if st.secrets.get("PERPLEXITY_API_KEY"):
            self._available_providers.append("perplexity")
        
        # Establecer proveedor por defecto
        if self._available_providers and not self._current_provider:
            # Prioridad: perplexity > claude > openai
            if "perplexity" in self._available_providers:
                self._current_provider = "perplexity"
            elif "claude" in self._available_providers:
                self._current_provider = "claude"
            elif "openai" in self._available_providers:
                self._current_provider = "openai"
    
    @property
    def available_providers(self) -> List[str]:
        return self._available_providers
    
    @property
    def current_provider(self) -> str:
        return self._current_provider or ""
    
    @current_provider.setter
    def current_provider(self, value: str):
        if value in self._available_providers:
            self._current_provider = value
    
    @property
    def current_provider_info(self) -> Optional[AIProviderInfo]:
        if self._current_provider:
            return AI_PROVIDERS.get(self._current_provider)
        return None
    
    def get_provider_info(self, provider_id: str) -> Optional[AIProviderInfo]:
        return AI_PROVIDERS.get(provider_id)
    
    def call(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 2000,
        temperature: float = 0.3,
        provider: str = None
    ) -> Dict[str, Any]:
        """
        Llama al proveedor de IA seleccionado
        
        Args:
            prompt: Mensaje del usuario
            system_prompt: Instrucciones del sistema
            max_tokens: Máximo de tokens en respuesta
            temperature: Creatividad (0-1)
            provider: Forzar proveedor específico (opcional)
        
        Returns:
            Dict con success, content, provider, citations (si aplica)
        """
        provider_id = provider or self._current_provider
        
        if not provider_id or provider_id not in self._available_providers:
            return {
                "success": False,
                "error": "No hay proveedor de IA disponible",
                "content": ""
            }
        
        try:
            if provider_id == "claude":
                return self._call_claude(prompt, system_prompt, max_tokens, temperature)
            elif provider_id == "openai":
                return self._call_openai(prompt, system_prompt, max_tokens, temperature)
            elif provider_id == "perplexity":
                return self._call_perplexity(prompt, system_prompt, max_tokens, temperature)
            else:
                return {"success": False, "error": f"Proveedor desconocido: {provider_id}", "content": ""}
        except Exception as e:
            return {"success": False, "error": str(e), "content": ""}
    
    def _call_claude(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Llama a Claude API"""
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        
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
            return {
                "success": True,
                "content": content,
                "provider": "claude",
                "model": "claude-sonnet-4-20250514"
            }
        else:
            return {
                "success": False,
                "error": f"Claude API error: {response.status_code} - {response.text[:200]}",
                "content": ""
            }
    
    def _call_openai(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Llama a OpenAI API"""
        api_key = st.secrets.get("OPENAI_API_KEY", "")
        
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
            return {
                "success": True,
                "content": content,
                "provider": "openai",
                "model": "gpt-4o"
            }
        else:
            return {
                "success": False,
                "error": f"OpenAI API error: {response.status_code} - {response.text[:200]}",
                "content": ""
            }
    
    def _call_perplexity(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Llama a Perplexity API"""
        api_key = st.secrets.get("PERPLEXITY_API_KEY", "")
        
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
                "model": "sonar-pro",
                "citations": citations
            }
        else:
            return {
                "success": False,
                "error": f"Perplexity API error: {response.status_code} - {response.text[:200]}",
                "content": ""
            }


# =============================================================================
# FUNCIONES DE UI
# =============================================================================

_ai_manager = None

def get_ai_manager() -> AIProviderManager:
    """Obtiene instancia singleton del gestor de IA"""
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = AIProviderManager()
    return _ai_manager


def render_ai_provider_selector(
    key: str = "global_ai_provider",
    show_details: bool = True,
    compact: bool = False
) -> str:
    """
    Renderiza el selector de proveedor de IA
    
    Args:
        key: Key para el widget de Streamlit
        show_details: Si mostrar detalles del proveedor
        compact: Si usar vista compacta
    
    Returns:
        ID del proveedor seleccionado
    """
    manager = get_ai_manager()
    
    if not manager.available_providers:
        st.warning("⚠️ No hay APIs de IA configuradas. Añade al menos una en secrets.toml")
        return ""
    
    # Crear opciones
    options = []
    for provider_id in manager.available_providers:
        info = AI_PROVIDERS.get(provider_id)
        if info:
            options.append((provider_id, f"{info.icon} {info.name}"))
    
    # Valor actual
    current_idx = 0
    current = st.session_state.get(key, manager.current_provider)
    for i, (pid, _) in enumerate(options):
        if pid == current:
            current_idx = i
            break
    
    if compact:
        # Vista compacta (solo selectbox)
        selected = st.selectbox(
            "🤖 IA",
            options=[opt[1] for opt in options],
            index=current_idx,
            key=key,
            label_visibility="collapsed"
        )
        
        # Obtener ID del seleccionado
        for pid, label in options:
            if label == selected:
                manager.current_provider = pid
                st.session_state[key] = pid
                return pid
    else:
        # Vista completa con radio buttons
        selected_label = st.radio(
            "Proveedor de IA",
            options=[opt[1] for opt in options],
            index=current_idx,
            key=key,
            horizontal=True,
            label_visibility="collapsed"
        )
        
        # Obtener ID del seleccionado
        selected_id = ""
        for pid, label in options:
            if label == selected_label:
                selected_id = pid
                manager.current_provider = pid
                st.session_state[key] = pid
                break
        
        # Mostrar detalles si está habilitado
        if show_details and selected_id:
            info = AI_PROVIDERS.get(selected_id)
            if info:
                with st.expander(f"ℹ️ Sobre {info.name}", expanded=False):
                    st.markdown(f"**{info.description}**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**✅ Fortalezas:**")
                        for s in info.strengths[:3]:
                            st.markdown(f"- {s}")
                    
                    with col2:
                        st.markdown("**⚠️ Limitaciones:**")
                        for w in info.weaknesses[:3]:
                            st.markdown(f"- {w}")
                    
                    st.markdown("**🎯 Mejor para:**")
                    st.markdown(", ".join(info.best_for))
        
        return selected_id
    
    return ""


def render_ai_selector_inline(label: str = "IA:", key: str = "inline_ai") -> str:
    """
    Renderiza selector de IA inline (para usar en botones)
    
    Args:
        label: Etiqueta
        key: Key única
    
    Returns:
        ID del proveedor seleccionado
    """
    manager = get_ai_manager()
    
    if not manager.available_providers:
        return ""
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        options = []
        for provider_id in manager.available_providers:
            info = AI_PROVIDERS.get(provider_id)
            if info:
                options.append(f"{info.icon} {info.name}")
        
        current_idx = 0
        current = st.session_state.get(key, manager.current_provider)
        for i, pid in enumerate(manager.available_providers):
            if pid == current:
                current_idx = i
                break
        
        selected = st.selectbox(
            label,
            options=options,
            index=current_idx,
            key=key,
            label_visibility="collapsed"
        )
        
        # Devolver ID
        for i, opt in enumerate(options):
            if opt == selected:
                return manager.available_providers[i]
    
    return manager.current_provider


def render_provider_comparison():
    """Renderiza tabla comparativa de proveedores"""
    
    st.markdown("### 🤖 Comparación de Proveedores de IA")
    
    manager = get_ai_manager()
    
    # Tabla de comparación
    data = []
    for provider_id, info in AI_PROVIDERS.items():
        available = "✅" if provider_id in manager.available_providers else "❌"
        
        data.append({
            "Proveedor": f"{info.icon} {info.name}",
            "Disponible": available,
            "Modelo": info.model,
            "Internet": "✅" if provider_id == "perplexity" else "❌",
            "Coste": {"low": "💰", "medium": "💰💰", "high": "💰💰💰"}.get(info.cost_tier, "💰💰"),
            "Mejor para": ", ".join(info.best_for[:2])
        })
    
    st.table(data)
    
    # Recomendación
    st.info("""
    **💡 Recomendación:**
    - **Análisis de mercado actual** → Perplexity (tiene acceso a internet)
    - **Análisis estratégico detallado** → Claude
    - **Respuestas rápidas** → GPT-4o
    """)


def call_ai(
    prompt: str,
    system_prompt: str = "",
    provider: str = None,
    max_tokens: int = 2000
) -> Dict[str, Any]:
    """
    Función de conveniencia para llamar a la IA
    
    Args:
        prompt: Mensaje
        system_prompt: Instrucciones del sistema
        provider: Proveedor específico (o usa el seleccionado globalmente)
        max_tokens: Máximo de tokens
    
    Returns:
        Dict con success, content, provider
    """
    manager = get_ai_manager()
    return manager.call(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        provider=provider
    )
