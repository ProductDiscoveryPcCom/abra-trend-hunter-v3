"""
Módulo centralizado de países, idiomas y mapeos
Evita duplicación y asegura consistencia en toda la aplicación
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class CountryInfo:
    """Información completa de un país"""
    code: str           # ES, PT, FR, IT, DE
    name: str           # España, Portugal, etc.
    name_local: str     # España, Portugal, France, Italia, Deutschland
    language_code: str  # es, pt, fr, it, de
    language_name: str  # Español, Português, Français, etc.
    flag: str           # 🇪🇸, 🇵🇹, etc.
    google_gl: str      # Para Google (gl parameter)
    google_hl: str      # Para Google (hl parameter)
    google_ads_location: str    # ID de ubicación para Google Ads
    google_ads_language: str    # ID de idioma para Google Ads
    currency: str       # EUR para todos
    timezone: str       # Europe/Madrid, etc.


# Base de datos de países soportados
COUNTRIES: Dict[str, CountryInfo] = {
    "ES": CountryInfo(
        code="ES",
        name="España",
        name_local="España",
        language_code="es",
        language_name="Español",
        flag="🇪🇸",
        google_gl="es",
        google_hl="es",
        google_ads_location="2724",
        google_ads_language="1003",
        currency="EUR",
        timezone="Europe/Madrid"
    ),
    "PT": CountryInfo(
        code="PT",
        name="Portugal",
        name_local="Portugal",
        language_code="pt",
        language_name="Português",
        flag="🇵🇹",
        google_gl="pt",
        google_hl="pt",
        google_ads_location="2620",
        google_ads_language="1014",
        currency="EUR",
        timezone="Europe/Lisbon"
    ),
    "FR": CountryInfo(
        code="FR",
        name="Francia",
        name_local="France",
        language_code="fr",
        language_name="Français",
        flag="🇫🇷",
        google_gl="fr",
        google_hl="fr",
        google_ads_location="2250",
        google_ads_language="1002",
        currency="EUR",
        timezone="Europe/Paris"
    ),
    "IT": CountryInfo(
        code="IT",
        name="Italia",
        name_local="Italia",
        language_code="it",
        language_name="Italiano",
        flag="🇮🇹",
        google_gl="it",
        google_hl="it",
        google_ads_location="2380",
        google_ads_language="1004",
        currency="EUR",
        timezone="Europe/Rome"
    ),
    "DE": CountryInfo(
        code="DE",
        name="Alemania",
        name_local="Deutschland",
        language_code="de",
        language_name="Deutsch",
        flag="🇩🇪",
        google_gl="de",
        google_hl="de",
        google_ads_location="2276",
        google_ads_language="1001",
        currency="EUR",
        timezone="Europe/Berlin"
    ),
    # Países adicionales (para expansión futura)
    "UK": CountryInfo(
        code="UK",
        name="Reino Unido",
        name_local="United Kingdom",
        language_code="en",
        language_name="English",
        flag="🇬🇧",
        google_gl="uk",
        google_hl="en",
        google_ads_location="2826",
        google_ads_language="1000",
        currency="GBP",
        timezone="Europe/London"
    ),
    "US": CountryInfo(
        code="US",
        name="Estados Unidos",
        name_local="United States",
        language_code="en",
        language_name="English",
        flag="🇺🇸",
        google_gl="us",
        google_hl="en",
        google_ads_location="2840",
        google_ads_language="1000",
        currency="USD",
        timezone="America/New_York"
    ),
}

# Países activos en la aplicación (UI)
ACTIVE_COUNTRIES: List[str] = ["ES", "PT", "FR", "IT", "DE"]


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def get_country(code: str) -> Optional[CountryInfo]:
    """Obtiene información de un país por código"""
    return COUNTRIES.get(code.upper())


def get_country_name(code: str) -> str:
    """Obtiene el nombre del país en español"""
    country = COUNTRIES.get(code.upper())
    return country.name if country else code


def get_country_flag(code: str) -> str:
    """Obtiene el emoji de bandera"""
    country = COUNTRIES.get(code.upper())
    return country.flag if country else "🏳️"


def get_language_code(country_code: str) -> str:
    """Obtiene el código de idioma para un país"""
    country = COUNTRIES.get(country_code.upper())
    return country.language_code if country else "en"


def get_language_name(country_code: str) -> str:
    """Obtiene el nombre del idioma para un país"""
    country = COUNTRIES.get(country_code.upper())
    return country.language_name if country else "English"


def get_google_hl(country_code: str) -> str:
    """Obtiene el parámetro hl para Google APIs"""
    country = COUNTRIES.get(country_code.upper())
    return country.google_hl if country else "en"


def get_google_gl(country_code: str) -> str:
    """Obtiene el parámetro gl para Google APIs"""
    country = COUNTRIES.get(country_code.upper())
    return country.google_gl if country else "us"


def get_google_ads_location(country_code: str) -> str:
    """Obtiene el ID de ubicación para Google Ads"""
    country = COUNTRIES.get(country_code.upper())
    return country.google_ads_location if country else "2840"  # US default


def get_google_ads_language(country_code: str) -> str:
    """Obtiene el ID de idioma para Google Ads"""
    country = COUNTRIES.get(country_code.upper())
    return country.google_ads_language if country else "1000"  # English default


# =============================================================================
# MAPEOS PARA COMPATIBILIDAD
# =============================================================================

# Mapeo simple código → nombre (para UI)
COUNTRY_NAMES = {code: info.name for code, info in COUNTRIES.items()}

# Mapeo código → bandera
COUNTRY_FLAGS = {code: info.flag for code, info in COUNTRIES.items()}

# Mapeo código país → código idioma
COUNTRY_TO_LANGUAGE = {code: info.language_code for code, info in COUNTRIES.items()}

# Mapeo código país → nombre de idioma
LANGUAGE_NAMES = {code: info.language_name for code, info in COUNTRIES.items()}

# Para Google Ads
GOOGLE_ADS_LOCATIONS = {code: info.google_ads_location for code, info in COUNTRIES.items()}
GOOGLE_ADS_LANGUAGES = {code: info.google_ads_language for code, info in COUNTRIES.items()}


# =============================================================================
# PROMPTS POR IDIOMA (para IA)
# =============================================================================

AI_LANGUAGE_INSTRUCTIONS = {
    "ES": "Responde en español.",
    "PT": "Responde em português.",
    "FR": "Réponds en français.",
    "IT": "Rispondi in italiano.",
    "DE": "Antworte auf Deutsch.",
    "UK": "Respond in English.",
    "US": "Respond in English.",
}


def get_ai_language_instruction(country_code: str) -> str:
    """Obtiene la instrucción de idioma para prompts de IA"""
    return AI_LANGUAGE_INSTRUCTIONS.get(
        country_code.upper(), 
        "Respond in the user's language."
    )


# =============================================================================
# BÚSQUEDA DUAL (Idioma local + Inglés)
# =============================================================================

def get_search_languages(country_code: str) -> List[str]:
    """
    Obtiene los idiomas de búsqueda para un país.
    Devuelve [idioma_local, "en"] para buscar en ambos.
    
    Args:
        country_code: Código de país (ES, PT, FR, IT, DE)
        
    Returns:
        Lista de códigos de idioma, ej: ["es", "en"]
    """
    country = COUNTRIES.get(country_code.upper())
    if not country:
        return ["en"]  # Fallback solo inglés
    
    local_lang = country.language_code
    
    # Si el idioma local ya es inglés, no duplicar
    if local_lang == "en":
        return ["en"]
    
    return [local_lang, "en"]


def get_language_flag(lang_code: str) -> str:
    """
    Obtiene bandera/emoji para un código de idioma
    
    Args:
        lang_code: Código de idioma (es, en, pt, fr, it, de)
        
    Returns:
        Emoji de bandera
    """
    flags = {
        "es": "🇪🇸",
        "pt": "🇵🇹",
        "fr": "🇫🇷",
        "it": "🇮🇹",
        "de": "🇩🇪",
        "en": "🇬🇧",
    }
    return flags.get(lang_code.lower(), "🌐")


def get_language_name(lang_code: str) -> str:
    """
    Obtiene nombre del idioma
    
    Args:
        lang_code: Código de idioma (es, en, pt, fr, it, de)
        
    Returns:
        Nombre del idioma
    """
    names = {
        "es": "Español",
        "pt": "Português", 
        "fr": "Français",
        "it": "Italiano",
        "de": "Deutsch",
        "en": "English",
    }
    return names.get(lang_code.lower(), lang_code)


# =============================================================================
# SELECTOR UI
# =============================================================================

def get_country_selector_options() -> List[str]:
    """Opciones para selector de país en UI"""
    return ACTIVE_COUNTRIES


def format_country_option(code: str) -> str:
    """Formatea opción de país para selectbox"""
    country = COUNTRIES.get(code)
    if country:
        return f"{country.flag} {country.name}"
    return code


# =============================================================================
# VALIDACIÓN
# =============================================================================

def is_valid_country(code: str) -> bool:
    """Verifica si un código de país es válido"""
    return code.upper() in COUNTRIES


def is_active_country(code: str) -> bool:
    """Verifica si un país está activo en la UI"""
    return code.upper() in ACTIVE_COUNTRIES
