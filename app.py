"""
🔮 Abra Trend Hunter
Detecta tendencias de hardware antes que la competencia

PCComponentes - Product Discovery Tool
"""

import streamlit as st
import html

# Configuración de página (DEBE ser lo primero)
st.set_page_config(
    page_title="Abra Trend Hunter",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Imports
from modules.google_trends import GoogleTrendsModule, calculate_growth_rate, calculate_seasonality
from modules.related_queries import RelatedQueriesModule
from modules.serp_paa import PeopleAlsoAskModule
from modules.google_news import GoogleNewsModule
from modules.product_analysis import ProductAnalyzer
from modules.scoring import ScoringEngine
from modules.ai_analysis import AIAnalyzer, render_provider_selector

from components.trend_chart import render_trend_chart, render_comparison_chart
from components.seasonality import render_seasonality_panel
from components.score_cards import render_score_cards, render_score_breakdown
from components.related_cards import render_related_queries, render_related_topics, render_competitor_brands
from components.keyword_table import render_keyword_table, render_questions_panel
from components.geo_map import render_geo_comparison, render_country_selector
from components.news_panel import render_news_panel, render_news_comparison
from components.product_matrix import render_product_section

from utils import (
    load_css, render_logo, check_api_keys, render_api_status,
    init_session_state, add_to_history, render_search_history,
    render_empty_state, render_loading_state, sanitize_html, sanitize_for_query
)


def main():
    """Función principal de la aplicación"""
    
    # Inicializar
    load_css()
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        render_logo()
        st.markdown("---")
        
        # Configuración de región y tiempo
        st.markdown("#### ⚙️ Configuración")
        
        region = st.selectbox(
            "Región",
            options=["ES", "PT", "FR", "IT", "DE"],
            format_func=lambda x: {
                "ES": "🇪🇸 España",
                "PT": "🇵🇹 Portugal", 
                "FR": "🇫🇷 Francia",
                "IT": "🇮🇹 Italia",
                "DE": "🇩🇪 Alemania"
            }.get(x, x),
            index=0
        )
        st.session_state.selected_country = region
        
        timeframe = st.selectbox(
            "Período",
            options=[
                "today 1-m",
                "today 3-m", 
                "today 12-m",
                "today 5-y"
            ],
            format_func=lambda x: {
                "today 1-m": "Último mes",
                "today 3-m": "Últimos 3 meses",
                "today 12-m": "Último año",
                "today 5-y": "Últimos 5 años"
            }.get(x, x),
            index=2
        )
        st.session_state.selected_timeframe = timeframe
        
        st.markdown("---")
        
        # Selector de IA
        st.markdown("#### 🤖 Proveedor IA")
        ai_provider = render_provider_selector()
        st.session_state.ai_provider = ai_provider
        
        st.markdown("---")
        
        # Estado de APIs
        render_api_status()
        
        st.markdown("---")
        st.markdown(
            '<p style="font-size: 0.75rem; color: #9CA3AF; text-align: center;">'
            'Abra Trend Hunter v1.0<br>PCComponentes Product Discovery</p>',
            unsafe_allow_html=True
        )
    
    # Contenido principal
    # Header con búsqueda
    col_search, col_button = st.columns([4, 1])
    
    with col_search:
        keyword = st.text_input(
            "Buscar marca o producto",
            placeholder="Ej: Beelink, Framework Laptop, Steam Deck...",
            label_visibility="collapsed",
            key="search_input",
            max_chars=200  # Limitar longitud
        )
    
    with col_button:
        search_clicked = st.button("🔍 Analizar", type="primary", use_container_width=True)
    
    # Historial de búsquedas
    history_selection = render_search_history()
    if history_selection:
        keyword = history_selection
        search_clicked = True
    
    # Si no hay búsqueda, mostrar estado vacío
    if not keyword or not search_clicked:
        if not st.session_state.current_keyword:
            render_empty_state()
            return
        else:
            keyword = st.session_state.current_keyword
    
    # Sanitizar keyword para seguridad
    keyword = sanitize_for_query(keyword)
    
    if not keyword:
        st.warning("Por favor, introduce un término de búsqueda válido.")
        return
    
    # Verificar API key de SerpAPI
    api_status = check_api_keys()
    if not api_status["serpapi"]:
        st.error("⚠️ SerpAPI no está configurada. Añade tu API key en los secrets.")
        st.info("Ve a Settings > Secrets y añade: SERPAPI_KEY = 'tu_api_key'")
        return
    
    # Guardar keyword actual
    st.session_state.current_keyword = keyword
    add_to_history(keyword)
    
    # Análisis
    keyword_display = sanitize_html(keyword)
    st.markdown(f"## 📊 Análisis: **{keyword_display}**")
    
    # Inicializar módulos
    try:
        serpapi_key = st.secrets.get("SERPAPI_KEY", "")
        trends_module = GoogleTrendsModule(serpapi_key)
        related_module = RelatedQueriesModule(serpapi_key)
        paa_module = PeopleAlsoAskModule(serpapi_key)
        news_module = GoogleNewsModule(serpapi_key)
        product_analyzer = ProductAnalyzer(serpapi_key)
        scoring_engine = ScoringEngine()
        ai_analyzer = AIAnalyzer()
    except Exception as e:
        st.error(f"Error inicializando módulos: {sanitize_html(str(e))}")
        return
    
    # Obtener datos
    with st.spinner("🔮 Consultando Google Trends..."):
        try:
            trends_data = trends_module.get_interest_over_time(
                keyword=keyword,
                geo=st.session_state.selected_country,
                timeframe=st.session_state.selected_timeframe
            )
        except Exception as e:
            st.error(f"Error consultando Google Trends: {sanitize_html(str(e))}")
            return
    
    if not trends_data.get("success"):
        error_msg = trends_data.get('error', 'Error desconocido')
        st.error(f"Error obteniendo datos: {sanitize_html(str(error_msg))}")
        st.info("💡 Esto puede ocurrir si la marca es muy nueva o tiene poco volumen de búsqueda.")
        return
    
    timeline_data = trends_data.get("timeline_data", [])
    
    if not timeline_data:
        st.warning(f"No se encontraron datos para '{keyword_display}'.")
        st.info("💡 Prueba con otro término o verifica que la marca existe.")
        return
    
    # Calcular métricas (manejando valores cero)
    growth_data = calculate_growth_rate(timeline_data)
    seasonality_data = calculate_seasonality(timeline_data)
    
    # Obtener datos relacionados
    with st.spinner("🔍 Obteniendo búsquedas relacionadas..."):
        try:
            related_data = related_module.get_all_related(
                keyword=keyword,
                geo=st.session_state.selected_country,
                timeframe=st.session_state.selected_timeframe
            )
        except Exception as e:
            related_data = {"success": False, "queries": {"rising": [], "top": []}, "topics": {"rising": [], "top": []}}
    
    # Obtener PAA expandido
    with st.spinner("❓ Buscando preguntas frecuentes..."):
        try:
            paa_data = paa_module.categorize_searches(
                keyword=keyword,
                country=st.session_state.selected_country
            )
        except Exception as e:
            paa_data = {"success": False, "categorized": {"all": [], "questions": [], "comparatives": [], "others": []}}
        
        try:
            expanded_questions = paa_module.get_expanded_questions(
                keyword=keyword,
                country=st.session_state.selected_country,
                max_depth=2,
                max_questions=25
            )
            questions = expanded_questions.get("questions", [])
        except Exception as e:
            questions = []
    
    # Calcular scores (manejando valores cero)
    try:
        trend_score = scoring_engine.calculate_trend_score(
            timeline_data=timeline_data,
            related_queries_count=len(related_data.get("queries", {}).get("rising", []))
        )
    except Exception:
        trend_score = {"score": 0, "grade": "F", "factors": {}}
    
    try:
        potential_score = scoring_engine.calculate_potential_score(
            timeline_data=timeline_data,
            rising_queries=related_data.get("queries", {}).get("rising", []),
            current_value=growth_data.get("current_value", 0),
            is_seasonal=seasonality_data.get("is_seasonal", False)
        )
    except Exception:
        potential_score = {"score": 0, "grade": "F", "factors": {}}
    
    try:
        opportunity = scoring_engine.calculate_opportunity_level(
            trend_score=trend_score.get("score", 0),
            potential_score=potential_score.get("score", 0)
        )
    except Exception:
        opportunity = {"level": "MUY BAJA", "combined_score": 0, "color": "#EF4444", "icon": "❄️", "action": "No prioritario"}
    
    # === LAYOUT PRINCIPAL ===
    
    # Fila 1: Gráfico de tendencia
    st.markdown("### 📈 Tendencia temporal")
    render_trend_chart(
        timeline_data=timeline_data,
        keyword=keyword,
        show_trajectory=st.session_state.get("show_trajectory", True)
    )
    
    # Fila 2: Scores y Estacionalidad
    col_scores, col_season = st.columns([2, 1])
    
    with col_scores:
        st.markdown("### 🎯 Scoring")
        render_score_cards(trend_score, potential_score, opportunity)
        
        # Desglose de scores
        with st.expander("Ver desglose de factores"):
            col_t, col_p = st.columns(2)
            with col_t:
                render_score_breakdown(
                    "Trend Score",
                    trend_score.get("factors", {}),
                    "#F5C518"
                )
            with col_p:
                render_score_breakdown(
                    "Potential Score",
                    potential_score.get("factors", {}),
                    "#7C3AED"
                )
    
    with col_season:
        # Explicación IA de estacionalidad
        ai_explanation = None
        if ai_analyzer.get_available_providers():
            try:
                with st.spinner("🤖 Generando explicación..."):
                    ai_explanation = ai_analyzer.explain_seasonality(
                        seasonality_data=seasonality_data,
                        brand=keyword,
                        provider=st.session_state.ai_provider
                    )
            except Exception:
                ai_explanation = None
        
        render_seasonality_panel(
            seasonality_data=seasonality_data,
            ai_explanation=ai_explanation
        )
    
    st.markdown("---")
    
    # Fila 3: Related Queries y Topics
    col_queries, col_topics = st.columns(2)
    
    with col_queries:
        render_related_queries(related_data.get("queries", {}))
    
    with col_topics:
        render_related_topics(related_data.get("topics", {}))
    
    st.markdown("---")
    
    # Fila 4: Análisis de Productos de la Marca
    with st.spinner("🏷️ Analizando productos de la marca..."):
        try:
            # Combinar queries rising y top para detección
            all_related_queries = (
                related_data.get("queries", {}).get("rising", []) +
                related_data.get("queries", {}).get("top", [])
            )
            
            product_analysis = product_analyzer.full_analysis(
                brand=keyword,
                related_queries=all_related_queries,
                geo=st.session_state.selected_country,
                timeframe=st.session_state.selected_timeframe
            )
        except Exception as e:
            product_analysis = {"success": False, "products": [], "classified": {}, "insights": {}}
    
    render_product_section(product_analysis, keyword)
    
    st.markdown("---")
    
    # Fila 5: Keywords y Preguntas
    col_keywords, col_questions = st.columns([2, 1])
    
    with col_keywords:
        render_keyword_table(paa_data)
    
    with col_questions:
        render_questions_panel(questions)
    
    st.markdown("---")
    
    # Fila 6: Análisis IA
    if ai_analyzer.get_available_providers():
        st.markdown("### 🤖 Análisis IA")
        
        try:
            with st.spinner(f"Generando análisis con {st.session_state.ai_provider}..."):
                # Preparar datos para el análisis
                analysis_data = {
                    "keyword": keyword,
                    "current_value": growth_data.get("current_value", 0),
                    "growth_rate": growth_data.get("growth_rate", 0),
                    "trend_score": trend_score.get("score", 0),
                    "potential_score": potential_score.get("score", 0),
                    "is_seasonal": seasonality_data.get("is_seasonal", False),
                    "rising_queries": related_data.get("queries", {}).get("rising", [])[:5],
                    "questions": [q.get("question", "") for q in questions[:5] if isinstance(q, dict)]
                }
                
                ai_result = ai_analyzer.analyze(
                    trend_data=analysis_data,
                    provider=st.session_state.ai_provider
                )
            
            if ai_result.get("success"):
                # Análisis principal - sanitizar contenido de IA
                analysis_text = sanitize_html(ai_result.get("analysis", "No se pudo generar el análisis"))
                provider_name = sanitize_html(ai_result.get("provider", "IA"))
                
                st.markdown(
                    f'''
                    <div style="background: linear-gradient(135deg, #EDE9FE 0%, #FFFFFF 100%);
                    border-radius: 12px; padding: 24px; border-left: 4px solid #7C3AED;
                    margin-bottom: 16px;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                            <span style="font-size: 1.25rem;">🧠</span>
                            <span style="font-weight: 600; color: #5B21B6;">
                                Análisis ({provider_name})
                            </span>
                        </div>
                        <div style="color: #374151; line-height: 1.6;">
                            {analysis_text}
                        </div>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )
                
                # Ideas de blog
                blog_ideas = ai_result.get("blog_ideas", [])
                if blog_ideas:
                    st.markdown("#### 📝 Ideas para el blog")
                    
                    for i, idea in enumerate(blog_ideas[:5]):
                        if not isinstance(idea, dict):
                            continue
                        titulo = sanitize_html(idea.get('titulo', f'Idea {i+1}'))
                        with st.expander(f"💡 {titulo}"):
                            enfoque = sanitize_html(idea.get('enfoque', 'N/A'))
                            st.markdown(f"**Enfoque:** {enfoque}")
                            keywords = idea.get('keywords_objetivo', [])
                            if keywords and isinstance(keywords, list):
                                keywords_safe = [sanitize_html(str(k)) for k in keywords[:10]]
                                st.markdown(f"**Keywords:** {', '.join(keywords_safe)}")
            else:
                error_msg = sanitize_html(ai_result.get('error', 'Error desconocido'))
                st.warning(f"No se pudo generar el análisis: {error_msg}")
        except Exception as e:
            st.warning(f"Error en análisis IA: {sanitize_html(str(e))}")
    
    st.markdown("---")
    
    # Fila 7: Noticias relacionadas
    st.markdown("### 📰 Noticias Relacionadas")
    
    try:
        with st.spinner("Buscando noticias..."):
            news_data = news_module.search_news(
                query=keyword,
                country=st.session_state.selected_country
            )
        
        if news_data.get("success") and news_data.get("news"):
            # Analizar sentimiento
            sentiment = news_module.analyze_news_sentiment(news_data.get("news", []))
            
            render_news_panel(
                news=news_data.get("news", []),
                title=f"📰 Noticias sobre {keyword_display}",
                max_display=6,
                show_sentiment=True,
                sentiment_data=sentiment
            )
        else:
            st.info(f"No se encontraron noticias recientes sobre '{keyword_display}'")
    except Exception as e:
        st.info(f"No se pudieron cargar las noticias")
    
    st.markdown("---")
    
    # Fila 8: Comparativa por países
    st.markdown("### 🌍 Comparativa por países")
    
    compare_countries = st.checkbox("Comparar con otros países", value=False)
    
    if compare_countries:
        try:
            with st.spinner("Obteniendo datos por país..."):
                country_data = trends_module.get_multi_country_data(
                    keyword=keyword,
                    countries=["ES", "PT", "FR", "IT", "DE"],
                    timeframe=st.session_state.selected_timeframe
                )
            
            render_geo_comparison(
                country_data=country_data.get("countries", {}),
                keyword=keyword
            )
            
            # Gráfico comparativo
            render_comparison_chart(
                data_by_country=country_data.get("countries", {}),
                keyword=keyword
            )
        except Exception as e:
            st.warning("No se pudieron cargar los datos de comparativa por países")


if __name__ == "__main__":
    main()
