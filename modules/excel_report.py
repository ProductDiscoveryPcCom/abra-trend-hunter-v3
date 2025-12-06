"""
Excel Report Module
Genera informes en formato Excel con múltiples hojas
"""

import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List, Optional
import html


def generate_excel_report(
    keyword: str,
    country: str,
    timeline_data: List[Dict] = None,
    related_data: Dict = None,
    trend_score: Dict = None,
    potential_score: Dict = None,
    growth_data: Dict = None,
    seasonality_data: Dict = None,
    youtube_data: Any = None,
    news_data: List[Dict] = None,
    paa_data: Dict = None
) -> BytesIO:
    """
    Genera un informe Excel completo con múltiples hojas.
    
    Args:
        keyword: Término analizado
        country: Código de país
        timeline_data: Datos de tendencia temporal
        related_data: Queries y topics relacionados
        trend_score: Datos del Trend Score
        potential_score: Datos del Potential Score
        growth_data: Datos de crecimiento
        seasonality_data: Datos de estacionalidad
        youtube_data: Datos de YouTube (DeepDiveResult)
        news_data: Lista de noticias
        paa_data: Preguntas de People Also Ask
    
    Returns:
        BytesIO con el archivo Excel
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # ========== HOJA 1: RESUMEN ==========
        summary_data = {
            "Métrica": [
                "Keyword",
                "País",
                "Fecha de análisis",
                "Trend Score",
                "Trend Grade",
                "Potential Score",
                "Potential Grade",
                "Crecimiento %",
                "Es Estacional",
                "Pico de Interés"
            ],
            "Valor": [
                keyword,
                country,
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                trend_score.get("score", 0) if trend_score else 0,
                trend_score.get("grade", "N/A") if trend_score else "N/A",
                potential_score.get("score", 0) if potential_score else 0,
                potential_score.get("grade", "N/A") if potential_score else "N/A",
                f"{growth_data.get('pct_change', 0):.1f}%" if growth_data else "N/A",
                "Sí" if seasonality_data and seasonality_data.get("is_seasonal") else "No",
                seasonality_data.get("peak_period", "N/A") if seasonality_data else "N/A"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Resumen", index=False)
        
        # ========== HOJA 2: TENDENCIA TEMPORAL ==========
        if timeline_data:
            timeline_rows = []
            for point in timeline_data:
                date = point.get("date", "")
                values = point.get("values", [{}])
                value = values[0].get("extracted_value", 0) if values else 0
                timeline_rows.append({
                    "Fecha": date,
                    "Índice de Interés": value
                })
            
            if timeline_rows:
                timeline_df = pd.DataFrame(timeline_rows)
                timeline_df.to_excel(writer, sheet_name="Tendencia", index=False)
        
        # ========== HOJA 3: QUERIES RELACIONADAS ==========
        if related_data and related_data.get("queries"):
            queries_rows = []
            
            # Rising queries
            for q in related_data.get("queries", {}).get("rising", []):
                queries_rows.append({
                    "Query": q.get("query", ""),
                    "Tipo": "Rising",
                    "Valor": q.get("value", ""),
                    "Volumen Estimado": q.get("real_volume", "N/A"),
                    "Breakout Score": q.get("breakout_score", "N/A")
                })
            
            # Top queries
            for q in related_data.get("queries", {}).get("top", []):
                queries_rows.append({
                    "Query": q.get("query", ""),
                    "Tipo": "Top",
                    "Valor": q.get("value", ""),
                    "Volumen Estimado": q.get("real_volume", "N/A"),
                    "Breakout Score": "N/A"
                })
            
            if queries_rows:
                queries_df = pd.DataFrame(queries_rows)
                queries_df.to_excel(writer, sheet_name="Queries Relacionadas", index=False)
        
        # ========== HOJA 4: TOPICS RELACIONADOS ==========
        if related_data and related_data.get("topics"):
            topics_rows = []
            
            for t in related_data.get("topics", {}).get("rising", []):
                topics_rows.append({
                    "Topic": t.get("title", t.get("topic", "")),
                    "Tipo": "Rising",
                    "Valor": t.get("value", "")
                })
            
            for t in related_data.get("topics", {}).get("top", []):
                topics_rows.append({
                    "Topic": t.get("title", t.get("topic", "")),
                    "Tipo": "Top",
                    "Valor": t.get("value", "")
                })
            
            if topics_rows:
                topics_df = pd.DataFrame(topics_rows)
                topics_df.to_excel(writer, sheet_name="Topics Relacionados", index=False)
        
        # ========== HOJA 5: YOUTUBE ==========
        if youtube_data:
            videos_rows = []
            
            # Obtener todos los videos del DeepDiveResult
            all_videos = []
            if hasattr(youtube_data, 'videos_by_type'):
                for video_type, videos in youtube_data.videos_by_type.items():
                    for v in videos:
                        all_videos.append((video_type, v))
            
            for video_type, v in all_videos:
                videos_rows.append({
                    "Título": _clean_text(getattr(v, 'title', '')),
                    "Canal": _clean_text(getattr(v, 'channel', '')),
                    "Tipo": video_type,
                    "Vistas": getattr(v, 'views', 0),
                    "Likes": getattr(v, 'likes', 0),
                    "Comentarios": getattr(v, 'comments', 0),
                    "Duración": getattr(v, 'duration', 'N/A'),
                    "Fecha": getattr(v, 'published_at', 'N/A'),
                    "Idioma": getattr(v, 'language', 'N/A'),
                    "URL": f"https://youtube.com/watch?v={getattr(v, 'video_id', '')}"
                })
            
            if videos_rows:
                videos_df = pd.DataFrame(videos_rows)
                videos_df.to_excel(writer, sheet_name="YouTube", index=False)
        
        # ========== HOJA 6: NOTICIAS ==========
        if news_data:
            news_rows = []
            news_list = news_data if isinstance(news_data, list) else news_data.get("news", [])
            
            for n in news_list:
                news_rows.append({
                    "Título": _clean_text(n.get("title", "")),
                    "Fuente": n.get("source", ""),
                    "Fecha": n.get("date", ""),
                    "Snippet": _clean_text(n.get("snippet", ""))[:200],
                    "URL": n.get("link", ""),
                    "Idioma": n.get("search_language", "N/A")
                })
            
            if news_rows:
                news_df = pd.DataFrame(news_rows)
                news_df.to_excel(writer, sheet_name="Noticias", index=False)
        
        # ========== HOJA 7: PREGUNTAS (PAA) ==========
        if paa_data:
            paa_rows = []
            
            categorized = paa_data.get("categorized", {})
            for category, questions in categorized.items():
                for q in questions:
                    question_text = q.get("question", q) if isinstance(q, dict) else q
                    paa_rows.append({
                        "Pregunta": _clean_text(question_text),
                        "Categoría": category.title()
                    })
            
            if paa_rows:
                paa_df = pd.DataFrame(paa_rows)
                paa_df.to_excel(writer, sheet_name="Preguntas PAA", index=False)
        
        # ========== HOJA 8: FACTORES DE SCORE ==========
        if trend_score or potential_score:
            factors_rows = []
            
            if trend_score and trend_score.get("factors"):
                for factor, value in trend_score.get("factors", {}).items():
                    factors_rows.append({
                        "Score": "Trend Score",
                        "Factor": factor,
                        "Valor": value
                    })
            
            if potential_score and potential_score.get("factors"):
                for factor, value in potential_score.get("factors", {}).items():
                    factors_rows.append({
                        "Score": "Potential Score",
                        "Factor": factor,
                        "Valor": value
                    })
            
            if factors_rows:
                factors_df = pd.DataFrame(factors_rows)
                factors_df.to_excel(writer, sheet_name="Factores de Score", index=False)
    
    output.seek(0)
    return output


def _clean_text(text: str) -> str:
    """Limpia texto para Excel"""
    if not text:
        return ""
    # Decodificar HTML entities
    text = html.unescape(str(text))
    # Remover caracteres problemáticos
    text = text.replace('\n', ' ').replace('\r', ' ')
    return text[:500]  # Limitar longitud


def get_excel_filename(keyword: str, country: str) -> str:
    """Genera nombre de archivo para el Excel"""
    safe_keyword = "".join(c for c in keyword if c.isalnum() or c in " -_").strip()
    safe_keyword = safe_keyword.replace(" ", "_")[:30]
    date_str = datetime.now().strftime("%Y%m%d")
    return f"trend_report_{safe_keyword}_{country}_{date_str}.xlsx"
