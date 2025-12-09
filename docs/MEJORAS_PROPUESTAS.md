# 🚀 Propuestas de Mejora - Abra Trend Hunter

## Resumen Ejecutivo

Tras una auditoría exhaustiva del código (22,661 líneas en 56 archivos), se proponen mejoras en 5 categorías principales. Todas las mejoras son **incrementales y no rompen funcionalidad existente**.

---

## 1. 🎨 FRONTEND / UX

### 1.1 Feedback Visual Mejorado
**Estado actual:** Spinners básicos con texto estático
**Mejora propuesta:**

```python
# ANTES
with st.spinner("Cargando datos..."):
    data = fetch_data()

# DESPUÉS - Progress bar con etapas
def fetch_with_progress(keyword):
    progress = st.progress(0, text="Iniciando análisis...")
    
    progress.progress(20, text="📊 Consultando Google Trends...")
    trends_data = fetch_trends(keyword)
    
    progress.progress(40, text="🔍 Buscando queries relacionadas...")
    related = fetch_related(keyword)
    
    progress.progress(60, text="📰 Recopilando noticias...")
    news = fetch_news(keyword)
    
    progress.progress(80, text="🧠 Analizando con IA...")
    ai_analysis = analyze(keyword)
    
    progress.progress(100, text="✅ Análisis completado")
    return {...}
```

**Impacto:** UX mejorada, usuario sabe qué está pasando

### 1.2 Tooltips Informativos
**Estado actual:** Algunos tooltips, inconsistentes
**Mejora propuesta:** Añadir `help` parameter en todos los inputs importantes

```python
st.text_input(
    "Término de búsqueda",
    help="Introduce una marca, producto o categoría. Ejemplo: 'Beelink', 'RTX 5090', 'mini pc'"
)
```

### 1.3 Notificaciones Toast
**Mejora propuesta:** Usar `st.toast()` para feedback no intrusivo

```python
# Cuando se guarda en caché
st.toast("✅ Datos guardados en caché", icon="💾")

# Cuando se detecta algo importante
st.toast("🔥 ¡Tendencia en explosión detectada!", icon="🚀")
```

### 1.4 Estado Vacío Mejorado
**Mejora propuesta:** Empty states más informativos y accionables

```python
def render_empty_state_improved(context: str):
    suggestions = {
        "trends": ["Beelink", "Minisforum", "RTX 5090"],
        "news": ["CES 2025", "AMD Ryzen", "Intel Arc"],
        "youtube": ["Review gaming", "Unboxing tech"]
    }
    
    st.info(f"No hay datos para mostrar. Sugerencias: {', '.join(suggestions.get(context, []))}")
```

---

## 2. 🔧 BACKEND / Rendimiento

### 2.1 Caché Local Inteligente
**Estado actual:** Caché Supabase (remoto, TTL 30 días)
**Mejora propuesta:** Añadir caché en memoria para sesión activa

```python
# utils/session_cache.py
@st.cache_data(ttl=300)  # 5 minutos en memoria
def get_trends_cached(keyword: str, geo: str) -> dict:
    """Caché de sesión antes de ir a Supabase"""
    return google_trends.fetch(keyword, geo)
```

**Beneficio:** Reducir latencia en navegación entre tabs

### 2.2 Lazy Loading de Componentes
**Mejora propuesta:** Cargar secciones pesadas solo cuando se expanden

```python
with st.expander("📺 YouTube Deep Dive"):
    if st.session_state.get(f"expanded_youtube_{keyword}"):
        # Solo cargar si está expandido
        render_youtube_panel(keyword)
    else:
        st.session_state[f"expanded_youtube_{keyword}"] = True
        st.rerun()
```

### 2.3 Batch de Llamadas API
**Estado actual:** Llamadas secuenciales
**Mejora propuesta:** Paralelizar donde sea posible

```python
import concurrent.futures

def fetch_all_data(keyword: str) -> dict:
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            "trends": executor.submit(fetch_trends, keyword),
            "news": executor.submit(fetch_news, keyword),
            "youtube": executor.submit(fetch_youtube, keyword),
            "paa": executor.submit(fetch_paa, keyword)
        }
        
        results = {}
        for key, future in futures.items():
            try:
                results[key] = future.result(timeout=30)
            except Exception as e:
                results[key] = {"error": str(e)}
        
        return results
```

**Nota:** Cuidado con rate limits de APIs

### 2.4 Compresión de Datos en Caché
**Mejora propuesta:** Comprimir datos grandes antes de guardar

```python
import zlib
import json

def compress_for_cache(data: dict) -> bytes:
    json_str = json.dumps(data)
    return zlib.compress(json_str.encode())

def decompress_from_cache(data: bytes) -> dict:
    json_str = zlib.decompress(data).decode()
    return json.loads(json_str)
```

---

## 3. 📊 VISUALIZACIONES

### 3.1 Mini Dashboard de Comparación
**Mejora propuesta:** Widget compacto para comparar 2-3 keywords rápidamente

```python
def render_quick_compare():
    """Comparador rápido en sidebar"""
    with st.sidebar:
        st.subheader("⚡ Comparar rápido")
        kw1 = st.text_input("Keyword 1", key="cmp1")
        kw2 = st.text_input("Keyword 2", key="cmp2")
        
        if kw1 and kw2:
            data = compare_keywords([kw1, kw2])
            
            # Mini chart sparkline
            fig = create_comparison_sparkline(data)
            st.plotly_chart(fig, use_container_width=True)
```

### 3.2 Heatmap de Estacionalidad
**Mejora propuesta:** Visualización más clara de patrones estacionales

```python
def render_seasonality_heatmap(data: dict):
    """Heatmap mes x año con intensidad de búsquedas"""
    # Matriz 12 meses x N años
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=months,
        y=years,
        colorscale='YlOrRd'
    ))
    st.plotly_chart(fig)
```

### 3.3 Timeline Interactivo
**Mejora propuesta:** Eventos clave marcados en el gráfico de tendencia

```python
def render_trend_with_events(timeline_data, news_data):
    """Gráfico con marcadores de eventos importantes"""
    fig = go.Figure()
    
    # Línea de tendencia
    fig.add_trace(go.Scatter(...))
    
    # Marcadores de noticias importantes
    for news in news_data[:5]:
        fig.add_vline(
            x=news['date'],
            annotation_text=news['title'][:30],
            line_dash="dot"
        )
```

---

## 4. 🎯 FUNCIONALIDAD / Utilidad

### 4.1 Alertas Personalizadas
**Mejora propuesta:** Sistema de alertas cuando una keyword supera umbral

```python
# modules/alerts.py
@dataclass
class TrendAlert:
    keyword: str
    threshold: float
    alert_type: str  # "growth", "volume", "breakout"
    email: Optional[str] = None

def check_alerts(alerts: List[TrendAlert], current_data: dict):
    """Verifica si hay alertas que disparar"""
    triggered = []
    for alert in alerts:
        if alert.alert_type == "growth":
            if current_data.get("growth_rate", 0) > alert.threshold:
                triggered.append(alert)
    return triggered
```

### 4.2 Historial de Análisis
**Mejora propuesta:** Persistir y mostrar análisis anteriores

```python
def render_analysis_history():
    """Panel con historial de análisis del usuario"""
    history = get_user_history()  # De session_state o DB
    
    st.subheader("📜 Historial de análisis")
    for item in history[-10:]:
        cols = st.columns([3, 1, 1])
        cols[0].write(item['keyword'])
        cols[1].write(f"Score: {item['trend_score']}")
        cols[2].button("🔄", key=f"reload_{item['id']}")
```

### 4.3 Export Mejorado
**Mejora propuesta:** Más formatos y opciones de export

```python
def render_export_options(data: dict, keyword: str):
    """Opciones de exportación expandidas"""
    st.subheader("📥 Exportar datos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # PDF (ya existe)
        if st.button("📄 PDF"):
            pdf = generate_pdf(data)
            st.download_button("Descargar PDF", pdf)
    
    with col2:
        # Excel con múltiples hojas
        if st.button("📊 Excel"):
            excel = generate_excel_multi_sheet(data)
            st.download_button("Descargar Excel", excel)
    
    with col3:
        # JSON para integración
        if st.button("🔗 JSON (API)"):
            json_data = json.dumps(data, indent=2)
            st.download_button("Descargar JSON", json_data)
```

### 4.4 Modo Comparación de Competidores
**Mejora propuesta:** Vista dedicada para comparar marcas competidoras

```python
def render_competitor_comparison():
    """Comparación lado a lado de competidores"""
    st.header("🏆 Comparación de Competidores")
    
    # Selector múltiple
    competitors = st.multiselect(
        "Selecciona marcas",
        options=["Beelink", "Minisforum", "Geekom", "GMKtec"],
        max_selections=4
    )
    
    if len(competitors) >= 2:
        data = fetch_comparison_data(competitors)
        
        # Tabla comparativa
        render_comparison_table(data)
        
        # Gráfico radar
        render_radar_chart(data)
        
        # Timeline superpuesto
        render_overlaid_trends(data)
```

---

## 5. 🔐 ROBUSTEZ / Calidad

### 5.1 Validación de Inputs Mejorada
**Mejora propuesta:** Feedback inmediato en inputs

```python
def validate_keyword(keyword: str) -> Tuple[bool, str]:
    """Valida keyword y devuelve feedback"""
    if not keyword:
        return False, "Campo requerido"
    if len(keyword) < 2:
        return False, "Mínimo 2 caracteres"
    if len(keyword) > 100:
        return False, "Máximo 100 caracteres"
    if re.search(r'[<>{}]', keyword):
        return False, "Caracteres no permitidos"
    return True, ""

# En UI
keyword = st.text_input("Keyword")
is_valid, error = validate_keyword(keyword)
if not is_valid:
    st.error(error)
```

### 5.2 Retry con Backoff
**Mejora propuesta:** Reintentos inteligentes en APIs

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3)
def fetch_trends(keyword):
    return api.get_trends(keyword)
```

### 5.3 Health Check Endpoint
**Mejora propuesta:** Verificación rápida del estado de APIs

```python
def render_health_check():
    """Panel de estado de servicios"""
    services = {
        "SerpAPI": check_serpapi(),
        "YouTube": check_youtube(),
        "Perplexity": check_perplexity(),
        "Supabase": check_supabase(),
        "AliExpress": check_aliexpress()
    }
    
    for name, status in services.items():
        icon = "✅" if status["ok"] else "❌"
        st.write(f"{icon} {name}: {status['message']}")
```

---

## 📋 Priorización Recomendada

| Mejora | Impacto | Esfuerzo | Prioridad |
|--------|---------|----------|-----------|
| Progress bar con etapas | Alto | Bajo | 🔴 P1 |
| Tooltips informativos | Medio | Bajo | 🔴 P1 |
| Toast notifications | Medio | Bajo | 🔴 P1 |
| Retry con backoff | Alto | Bajo | 🔴 P1 |
| Comparador rápido | Alto | Medio | 🟡 P2 |
| Heatmap estacionalidad | Medio | Medio | 🟡 P2 |
| Export JSON/API | Medio | Bajo | 🟡 P2 |
| Health check | Medio | Bajo | 🟡 P2 |
| Lazy loading | Alto | Alto | 🟢 P3 |
| Batch API calls | Alto | Alto | 🟢 P3 |
| Sistema de alertas | Alto | Alto | 🟢 P3 |

---

## ✅ Mejoras para Implementar Ahora

Las siguientes mejoras se implementarán inmediatamente por ser de alto impacto y bajo riesgo:

1. **Progress bar mejorado** - En `app.py`
2. **Tooltips en inputs** - En `app.py` sidebar
3. **Toast notifications** - En puntos clave
4. **Retry decorator** - En `utils/`
5. **Health check** - En sidebar
6. **Export JSON** - En panel de reportes
