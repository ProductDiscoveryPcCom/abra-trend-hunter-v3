# Mejoras Propuestas para Abra Trend Hunter v2.0

## 📊 Estado Actual del Proyecto

| Métrica | Valor |
|---------|-------|
| Archivos Python | 56 |
| Líneas de código | 26,370 |
| Módulos backend | 22 |
| Componentes UI | 15 |
| APIs integradas | 8 |
| Errores de compilación | 0 ✅ |

---

## 🎯 MEJORAS DE ALTA PRIORIDAD

### 1. Dashboard de Estado de APIs (Implementar)
**Problema:** El usuario no sabe qué APIs están configuradas hasta que falla algo.
**Solución:** Panel visual en sidebar mostrando estado de cada API.

```python
# En utils/__init__.py - añadir función
def render_api_status_panel():
    """Muestra estado visual de todas las APIs"""
    status = check_api_status()
    
    st.sidebar.markdown("### 🔌 Estado de APIs")
    
    apis = [
        ("SerpAPI", "serpapi", "🔍 Trends/PAA"),
        ("YouTube", "youtube", "📺 Videos"),
        ("Perplexity", "perplexity", "🧠 Market Intel"),
        ("Claude", "anthropic", "🤖 Análisis IA"),
        ("OpenAI", "openai", "🤖 Análisis IA"),
        ("AliExpress", "aliexpress", "🛒 Productos"),
        ("Google Ads", "google_ads", "💰 Volúmenes"),
        ("Supabase", "supabase", "💾 Caché")
    ]
    
    for name, key, desc in apis:
        is_active = status.get(key, False)
        icon = "✅" if is_active else "⚪"
        st.sidebar.caption(f"{icon} {name} - {desc}")
```

### 2. Onboarding para Nuevos Usuarios (Implementar)
**Problema:** Usuarios nuevos no saben por dónde empezar.
**Solución:** Tutorial interactivo en primera visita.

```python
def show_onboarding():
    """Muestra tutorial para nuevos usuarios"""
    if "onboarding_complete" not in st.session_state:
        with st.expander("👋 **¡Bienvenido a Abra Trend Hunter!**", expanded=True):
            st.markdown("""
            ### Cómo empezar:
            
            1. **Busca una marca** - Escribe el nombre en la barra de búsqueda
            2. **Analiza los scores** - Trend Score (popularidad actual) y Potential (crecimiento futuro)
            3. **Explora los datos** - YouTube, noticias, queries relacionadas
            4. **Exporta el informe** - PDF o Excel para compartir
            
            ### 💡 Ejemplos de búsqueda:
            - `Beelink` - Mini PCs chinos
            - `Minisforum` - Competidor directo
            - `"AMD Ryzen"` - Búsqueda exacta con comillas
            """)
            
            if st.button("✅ Entendido, empezar"):
                st.session_state.onboarding_complete = True
                st.rerun()
```

### 3. Comparador de Marcas Side-by-Side (Implementar)
**Problema:** No se pueden comparar marcas fácilmente.
**Solución:** Nueva pestaña para comparar 2-3 marcas.

```python
# Nuevo archivo: components/brand_comparator.py
def render_brand_comparator():
    """Compara múltiples marcas lado a lado"""
    st.markdown("### ⚔️ Comparador de Marcas")
    
    col1, col2 = st.columns(2)
    with col1:
        brand1 = st.text_input("Marca 1", placeholder="ej: Beelink")
    with col2:
        brand2 = st.text_input("Marca 2", placeholder="ej: Minisforum")
    
    if st.button("Comparar", type="primary") and brand1 and brand2:
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown(f"#### {brand1}")
            data1 = fetch_brand_summary(brand1)
            render_brand_card(data1)
        
        with col_b:
            st.markdown(f"#### {brand2}")
            data2 = fetch_brand_summary(brand2)
            render_brand_card(data2)
        
        # Gráfico comparativo
        render_comparison_chart(data1, data2)
```

### 4. Historial de Búsquedas Mejorado (Implementar)
**Problema:** El historial actual es básico.
**Solución:** Historial con preview de scores y filtros.

```python
def render_enhanced_history():
    """Historial con preview y filtros"""
    history = st.session_state.get("search_history", [])
    
    if not history:
        st.info("🔍 Tu historial aparecerá aquí")
        return
    
    # Filtros
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_text = st.text_input("🔎 Filtrar", placeholder="Buscar en historial...")
    with col2:
        sort_by = st.selectbox("Ordenar", ["Reciente", "Trend Score", "Potential"])
    
    # Aplicar filtros
    filtered = [h for h in history if filter_text.lower() in h['keyword'].lower()] if filter_text else history
    
    # Ordenar
    if sort_by == "Trend Score":
        filtered = sorted(filtered, key=lambda x: x.get('trend_score', 0), reverse=True)
    elif sort_by == "Potential":
        filtered = sorted(filtered, key=lambda x: x.get('potential_score', 0), reverse=True)
    
    # Mostrar
    for item in filtered[-15:]:
        col_a, col_b, col_c, col_d = st.columns([3, 1, 1, 1])
        with col_a:
            if st.button(f"🔍 {item['keyword']}", key=f"hist_{item['timestamp']}"):
                st.session_state.current_keyword = item['keyword']
                st.rerun()
        with col_b:
            ts = item.get('trend_score', 0)
            color = "#10B981" if ts >= 60 else "#F59E0B" if ts >= 30 else "#6B7280"
            st.markdown(f"<span style='color:{color}'>TS:{ts}</span>", unsafe_allow_html=True)
        with col_c:
            ps = item.get('potential_score', 0)
            st.caption(f"PS:{ps}")
        with col_d:
            st.caption(item['timestamp'][:10])
```

### 5. Exportación a Excel (Implementar)
**Problema:** Solo hay exportación a PDF.
**Solución:** Añadir exportación a Excel con múltiples hojas.

```python
# En modules/excel_report.py (nuevo)
import pandas as pd
from io import BytesIO

def generate_excel_report(data: dict) -> BytesIO:
    """Genera informe Excel completo"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja 1: Resumen
        summary = pd.DataFrame([{
            "Keyword": data["keyword"],
            "País": data["country"],
            "Trend Score": data.get("trend_score", {}).get("score", 0),
            "Potential Score": data.get("potential_score", {}).get("score", 0),
            "Crecimiento %": data.get("growth_data", {}).get("pct_change", 0),
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
        }])
        summary.to_excel(writer, sheet_name="Resumen", index=False)
        
        # Hoja 2: Timeline
        if data.get("timeline_data"):
            timeline = pd.DataFrame(data["timeline_data"])
            timeline.to_excel(writer, sheet_name="Tendencia", index=False)
        
        # Hoja 3: Related Queries
        if data.get("related_data", {}).get("queries", {}).get("rising"):
            queries = pd.DataFrame(data["related_data"]["queries"]["rising"])
            queries.to_excel(writer, sheet_name="Queries Rising", index=False)
        
        # Hoja 4: YouTube
        if data.get("youtube_data"):
            videos = pd.DataFrame([{
                "Título": v.title,
                "Canal": v.channel,
                "Vistas": v.views,
                "Likes": v.likes,
                "Fecha": v.published_at
            } for v in data["youtube_data"].get("all_videos", [])])
            videos.to_excel(writer, sheet_name="YouTube", index=False)
        
        # Hoja 5: Noticias
        if data.get("news_data"):
            news = pd.DataFrame(data["news_data"])
            news.to_excel(writer, sheet_name="Noticias", index=False)
    
    output.seek(0)
    return output
```

---

## 🎨 MEJORAS DE UX/UI

### 6. Estados Vacíos Mejorados
**Problema:** Mensajes genéricos "No hay datos".
**Solución:** Estados vacíos con acciones sugeridas.

```python
def render_empty_state(
    title: str,
    message: str,
    icon: str = "📭",
    suggestions: List[str] = None,
    action_label: str = None,
    action_callback = None
):
    """Renderiza un estado vacío con estilo"""
    st.markdown(f"""
    <div style="text-align: center; padding: 40px; background: #F9FAFB; 
         border-radius: 12px; border: 2px dashed #E5E7EB;">
        <div style="font-size: 3rem;">{icon}</div>
        <h3 style="margin: 16px 0 8px; color: #374151;">{title}</h3>
        <p style="color: #6B7280; margin-bottom: 16px;">{message}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if suggestions:
        st.markdown("**💡 Sugerencias:**")
        for s in suggestions:
            st.markdown(f"- {s}")
    
    if action_label and action_callback:
        if st.button(action_label, type="primary"):
            action_callback()
```

### 7. Modo Compacto vs Detallado
**Problema:** Demasiada información puede abrumar.
**Solución:** Toggle para alternar entre vistas.

```python
# En sidebar
view_mode = st.sidebar.radio(
    "📐 Vista",
    ["Compacta", "Detallada"],
    horizontal=True
)
st.session_state.view_mode = view_mode

# Usar en componentes
if st.session_state.get("view_mode") == "Compacta":
    render_compact_scores(trend_score, potential_score)
else:
    render_score_cards(trend_score, potential_score, opportunity)
```

### 8. Shortcuts de Teclado
**Problema:** Todo requiere clicks.
**Solución:** Añadir shortcuts comunes.

```javascript
// En assets/custom.js (nuevo)
document.addEventListener('keydown', function(e) {
    // Ctrl+K = Focus en búsqueda
    if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        document.querySelector('input[type="text"]').focus();
    }
    // Ctrl+E = Exportar PDF
    if (e.ctrlKey && e.key === 'e') {
        e.preventDefault();
        document.querySelector('[data-testid="stButton"] button').click();
    }
});
```

---

## ⚡ MEJORAS DE RENDIMIENTO

### 9. Lazy Loading de Secciones
**Problema:** Todo se carga aunque no se vea.
**Solución:** Cargar secciones bajo demanda.

```python
def lazy_section(title: str, load_func, cache_key: str):
    """Sección que se carga solo cuando se expande"""
    with st.expander(title, expanded=False):
        if st.session_state.get(f"loaded_{cache_key}", False):
            # Ya cargado, mostrar datos
            data = st.session_state.get(f"data_{cache_key}")
            if data:
                return data
        
        if st.button(f"📥 Cargar {title}", key=f"load_{cache_key}"):
            with st.spinner(f"Cargando {title}..."):
                data = load_func()
                st.session_state[f"loaded_{cache_key}"] = True
                st.session_state[f"data_{cache_key}"] = data
                st.rerun()
        else:
            st.info(f"Haz clic para cargar {title}")
```

### 10. Prefetch Inteligente
**Problema:** Cada búsqueda empieza de cero.
**Solución:** Prefetch de datos relacionados.

```python
def prefetch_related_brands(keyword: str):
    """Prefetch de marcas relacionadas en background"""
    # Obtener marcas similares del caché de queries relacionadas
    related = get_related_brands(keyword)
    
    # Prefetch en background (primeros 3)
    for brand in related[:3]:
        if brand not in st.session_state.get("prefetched", set()):
            # Guardar en caché para uso futuro
            st.session_state.setdefault("prefetched", set()).add(brand)
```

---

## 📊 MEJORAS DE UTILIDAD

### 11. Alertas y Watchlist
**Problema:** No hay forma de monitorear marcas.
**Solución:** Sistema de watchlist con alertas.

```python
# En modules/alerts.py (nuevo)
@dataclass
class WatchlistItem:
    keyword: str
    country: str
    added_at: datetime
    last_score: int = 0
    alert_threshold: int = 70

def render_watchlist():
    """Gestiona la watchlist del usuario"""
    st.markdown("### 👁️ Watchlist")
    
    watchlist = st.session_state.get("watchlist", [])
    
    if not watchlist:
        st.info("Añade marcas a tu watchlist para monitorearlas")
        return
    
    for item in watchlist:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.markdown(f"**{item.keyword}** ({item.country})")
        with col2:
            st.caption(f"TS: {item.last_score}")
        with col3:
            st.caption(f"Alerta: >{item.alert_threshold}")
        with col4:
            if st.button("❌", key=f"rm_{item.keyword}"):
                watchlist.remove(item)
                st.rerun()
```

### 12. Predicción de Estacionalidad
**Problema:** Se muestra estacionalidad pero no predicción.
**Solución:** Añadir predicción del próximo pico.

```python
def predict_next_peak(seasonality_data: dict) -> dict:
    """Predice cuándo será el próximo pico"""
    if not seasonality_data.get("is_seasonal"):
        return {"has_prediction": False}
    
    peak_months = seasonality_data.get("peak_months", [])
    current_month = datetime.now().month
    
    # Encontrar próximo pico
    future_peaks = [m for m in peak_months if m > current_month]
    if not future_peaks:
        future_peaks = [m + 12 for m in peak_months]
    
    next_peak = min(future_peaks)
    months_until = (next_peak - current_month) % 12 or 12
    
    month_names = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                   "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    return {
        "has_prediction": True,
        "next_peak_month": peak_months[0] if future_peaks else current_month,
        "next_peak_name": month_names[(next_peak - 1) % 12],
        "months_until_peak": months_until,
        "recommendation": f"Preparar stock {max(1, months_until - 2)} meses antes"
    }
```

### 13. Análisis de Competidores Automático
**Problema:** Hay que buscar competidores manualmente.
**Solución:** Detección automática de competidores.

```python
def detect_competitors(keyword: str, related_data: dict) -> List[str]:
    """Detecta competidores automáticamente"""
    competitors = set()
    
    # De queries relacionadas tipo "X vs Y"
    for query in related_data.get("queries", {}).get("rising", []):
        q = query.get("query", "").lower()
        if " vs " in q or " versus " in q:
            parts = q.replace(" versus ", " vs ").split(" vs ")
            for part in parts:
                cleaned = part.strip()
                if cleaned and cleaned != keyword.lower():
                    competitors.add(cleaned.title())
    
    # De queries con "alternativa"
    for query in related_data.get("queries", {}).get("top", []):
        q = query.get("query", "").lower()
        if "alternativa" in q or "alternative" in q:
            # Extraer nombre de marca
            pass
    
    return list(competitors)[:5]
```

---

## 🔧 MEJORAS TÉCNICAS

### 14. Logging Estructurado
**Problema:** No hay logs para debugging.
**Solución:** Sistema de logging centralizado.

```python
# En utils/logging.py (nuevo)
import logging
from datetime import datetime

def setup_logging():
    """Configura logging estructurado"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(module)s | %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'logs/abra_{datetime.now():%Y%m%d}.log')
        ]
    )

def log_search(keyword: str, country: str, scores: dict):
    """Log de búsqueda para analytics"""
    logging.info(f"SEARCH | {keyword} | {country} | TS:{scores.get('trend', 0)} | PS:{scores.get('potential', 0)}")

def log_api_call(api: str, duration: float, success: bool):
    """Log de llamadas a API"""
    status = "OK" if success else "FAIL"
    logging.info(f"API | {api} | {duration:.2f}s | {status}")
```

### 15. Tests Automatizados
**Problema:** Solo 3 archivos de test básicos.
**Solución:** Suite de tests más completa.

```python
# En tests/test_scoring.py (nuevo)
import pytest
from modules.scoring import ScoringEngine

class TestScoringEngine:
    def setup_method(self):
        self.engine = ScoringEngine()
    
    def test_trend_score_empty_data(self):
        """Score debe ser 0 con datos vacíos"""
        result = self.engine.calculate_trend_score([])
        assert result["score"] == 0
    
    def test_trend_score_range(self):
        """Score debe estar entre 0 y 100"""
        data = [{"value": i} for i in range(100)]
        result = self.engine.calculate_trend_score(data)
        assert 0 <= result["score"] <= 100
    
    def test_potential_score_growth(self):
        """Crecimiento alto debe dar score alto"""
        data = [{"value": i * 10} for i in range(12)]  # Crecimiento constante
        result = self.engine.calculate_potential_score(data)
        assert result["score"] >= 50
```

---

## 📱 MEJORAS RESPONSIVE

### 16. Vista Mobile Optimizada
**Problema:** UI no está optimizada para móvil.
**Solución:** CSS responsive y layout adaptativo.

```css
/* En assets/custom.css */
@media (max-width: 768px) {
    /* Scores en columna */
    [data-testid="column"] {
        width: 100% !important;
        flex: none !important;
    }
    
    /* Gráficos más pequeños */
    .js-plotly-plot {
        height: 250px !important;
    }
    
    /* Ocultar sidebar por defecto */
    [data-testid="stSidebar"] {
        transform: translateX(-100%);
        transition: transform 0.3s;
    }
    
    /* Botones más grandes para touch */
    .stButton > button {
        min-height: 48px;
        padding: 12px 24px;
    }
    
    /* Texto más legible */
    .stMarkdown {
        font-size: 16px;
    }
}
```

---

## 📋 PRIORIZACIÓN

| # | Mejora | Impacto | Esfuerzo | Sprint |
|---|--------|---------|----------|--------|
| 1 | Dashboard de APIs | Alto | Bajo | 1 |
| 2 | Onboarding | Alto | Bajo | 1 |
| 5 | Export Excel | Alto | Medio | 1 |
| 6 | Estados vacíos | Medio | Bajo | 1 |
| 3 | Comparador | Alto | Alto | 2 |
| 4 | Historial mejorado | Medio | Medio | 2 |
| 11 | Watchlist | Alto | Alto | 2 |
| 12 | Predicción estacionalidad | Medio | Bajo | 2 |
| 7 | Modo compacto | Bajo | Bajo | 3 |
| 9 | Lazy loading | Medio | Medio | 3 |
| 13 | Detección competidores | Alto | Medio | 3 |
| 14 | Logging | Medio | Bajo | 3 |

---

## 🚀 PRÓXIMOS PASOS

1. **Sprint 1 (Esta semana):**
   - [ ] Implementar Dashboard de APIs
   - [ ] Añadir Onboarding
   - [ ] Crear módulo de Excel export
   - [ ] Mejorar estados vacíos

2. **Sprint 2 (Próxima semana):**
   - [ ] Comparador de marcas
   - [ ] Historial mejorado
   - [ ] Sistema de watchlist

3. **Sprint 3 (Siguiente):**
   - [ ] Optimizaciones de rendimiento
   - [ ] Tests automatizados
   - [ ] Mejoras responsive

