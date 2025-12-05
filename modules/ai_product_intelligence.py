"""
AI Product Intelligence
Análisis avanzado de productos usando IA para generar:
- Clusters inteligentes
- Matrices de riesgo/oportunidad
- Mapas de posicionamiento
- Identificación de gaps de mercado
- Predicciones de ciclo de vida
"""

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests


@dataclass
class ProductCluster:
    """Un cluster de productos identificado por IA"""
    name: str
    description: str
    products: List[str]
    characteristics: List[str]
    opportunity_score: float  # 0-100
    risk_score: float  # 0-100
    recommended_action: str
    color: str = "#6366F1"


@dataclass
class MarketGap:
    """Un gap de mercado identificado"""
    name: str
    description: str
    potential: str  # "alto", "medio", "bajo"
    competition_level: str
    suggested_products: List[str]
    estimated_demand: int  # 0-100


@dataclass 
class AIProductAnalysis:
    """Resultado completo del análisis de IA"""
    clusters: List[ProductCluster] = field(default_factory=list)
    market_gaps: List[MarketGap] = field(default_factory=list)
    risk_matrix: Dict[str, Any] = field(default_factory=dict)
    positioning_map: Dict[str, Any] = field(default_factory=dict)
    lifecycle_predictions: Dict[str, str] = field(default_factory=dict)
    key_insights: List[str] = field(default_factory=list)
    strategic_recommendations: List[str] = field(default_factory=list)
    raw_analysis: str = ""


class AIProductAnalyzer:
    """
    Analizador de productos con IA.
    
    Usa Claude/GPT/Perplexity para analizar productos y generar
    insights accionables con visualizaciones.
    """
    
    def __init__(self, provider: str = "claude"):
        """
        Args:
            provider: "claude", "openai", o "perplexity"
        """
        self.provider = provider
        self._last_error = ""
    
    def analyze_products(
        self,
        products: List[Dict],
        brand: str,
        market_context: str = "",
        include_clusters: bool = True,
        include_gaps: bool = True,
        include_predictions: bool = True
    ) -> AIProductAnalysis:
        """
        Analiza productos usando IA.
        
        Args:
            products: Lista de productos con datos (name, volume, growth, category, etc.)
            brand: Nombre de la marca
            market_context: Contexto adicional del mercado
            include_clusters: Si generar análisis de clusters
            include_gaps: Si identificar gaps de mercado
            include_predictions: Si hacer predicciones de ciclo de vida
            
        Returns:
            AIProductAnalysis con todos los análisis
        """
        result = AIProductAnalysis()
        
        if not products:
            result.key_insights = ["No hay productos para analizar"]
            return result
        
        # Preparar datos para la IA
        products_summary = self._prepare_products_data(products)
        
        # Construir prompt
        prompt = self._build_analysis_prompt(
            products_summary=products_summary,
            brand=brand,
            market_context=market_context,
            include_clusters=include_clusters,
            include_gaps=include_gaps,
            include_predictions=include_predictions
        )
        
        # Llamar a la IA
        ai_response = self._call_ai(prompt)
        
        if not ai_response:
            result.key_insights = [f"Error en análisis: {self._last_error}"]
            return result
        
        result.raw_analysis = ai_response
        
        # Parsear respuesta
        self._parse_ai_response(ai_response, result)
        
        return result
    
    def _prepare_products_data(self, products: List[Dict]) -> str:
        """Prepara los datos de productos para el prompt"""
        lines = []
        
        for i, p in enumerate(products[:20]):  # Limitar a 20 para no exceder contexto
            if hasattr(p, 'name'):
                name = p.name
                volume = getattr(p, 'volume', 0) or 0
                growth = getattr(p, 'growth', 0) or 0
                category = getattr(p, 'category', None)
                if hasattr(category, 'value'):
                    category = category.value
                lifecycle = getattr(p, 'lifecycle', None)
                if hasattr(lifecycle, 'value'):
                    lifecycle = lifecycle.value
            else:
                name = p.get('name', f'Producto {i+1}')
                volume = p.get('volume', 0) or 0
                growth = p.get('growth', 0) or 0
                category = p.get('category', 'desconocido')
                lifecycle = p.get('lifecycle', 'desconocido')
            
            lines.append(
                f"- {name}: volumen={volume:.0f}, crecimiento={growth:+.1f}%, "
                f"categoría={category}, ciclo={lifecycle}"
            )
        
        return "\n".join(lines)
    
    def _build_analysis_prompt(
        self,
        products_summary: str,
        brand: str,
        market_context: str,
        include_clusters: bool,
        include_gaps: bool,
        include_predictions: bool
    ) -> str:
        """Construye el prompt para el análisis"""
        
        sections = []
        
        if include_clusters:
            sections.append("""
## CLUSTERS
Agrupa los productos en 2-4 clusters lógicos basándote en sus características.
Para cada cluster indica:
- Nombre descriptivo del cluster
- Productos que lo componen
- Características comunes
- Puntuación de oportunidad (0-100)
- Puntuación de riesgo (0-100)
- Acción recomendada
- Color sugerido (hex)

Formato JSON:
```json
{
  "clusters": [
    {
      "name": "Nombre del cluster",
      "description": "Descripción",
      "products": ["PROD1", "PROD2"],
      "characteristics": ["característica1", "característica2"],
      "opportunity_score": 75,
      "risk_score": 30,
      "recommended_action": "Invertir en marketing",
      "color": "#10B981"
    }
  ]
}
```""")
        
        if include_gaps:
            sections.append("""
## GAPS DE MERCADO
Identifica 1-3 oportunidades o gaps en el mercado basándote en los productos existentes.
Para cada gap:
- Nombre del gap
- Descripción de la oportunidad
- Potencial (alto/medio/bajo)
- Nivel de competencia
- Productos sugeridos para cubrir el gap
- Demanda estimada (0-100)

Formato JSON:
```json
{
  "market_gaps": [
    {
      "name": "Gap identificado",
      "description": "Descripción de la oportunidad",
      "potential": "alto",
      "competition_level": "baja",
      "suggested_products": ["Producto sugerido 1"],
      "estimated_demand": 70
    }
  ]
}
```""")
        
        if include_predictions:
            sections.append("""
## PREDICCIONES
Para cada producto, predice su evolución en los próximos 6 meses:
- "creciendo": seguirá subiendo
- "estable": se mantendrá
- "declive": bajará
- "explosivo": crecimiento viral potencial

Formato JSON:
```json
{
  "predictions": {
    "PRODUCTO1": "creciendo",
    "PRODUCTO2": "estable"
  }
}
```""")
        
        sections.append("""
## MATRIZ RIESGO/OPORTUNIDAD
Posiciona cada producto en una matriz de 4 cuadrantes:
- Eje X: Oportunidad (0-100)
- Eje Y: Riesgo (0-100)

Formato JSON:
```json
{
  "risk_matrix": {
    "PRODUCTO1": {"opportunity": 80, "risk": 20},
    "PRODUCTO2": {"opportunity": 40, "risk": 60}
  }
}
```""")
        
        sections.append("""
## INSIGHTS Y RECOMENDACIONES
Lista de 3-5 insights clave y 3-5 recomendaciones estratégicas.

Formato JSON:
```json
{
  "key_insights": ["Insight 1", "Insight 2"],
  "strategic_recommendations": ["Recomendación 1", "Recomendación 2"]
}
```""")
        
        prompt = f"""Analiza los siguientes productos de la marca "{brand}" para un retailer de tecnología (PCComponentes).

DATOS DE PRODUCTOS:
{products_summary}

{f"CONTEXTO DE MERCADO: {market_context}" if market_context else ""}

Realiza un análisis estratégico completo. Responde SOLO con JSON válido para cada sección.

{"".join(sections)}

IMPORTANTE: 
- Sé específico y accionable en las recomendaciones
- Basa el análisis en los datos proporcionados
- Los scores deben reflejar los datos reales (no inventar)
- Responde en español
"""
        
        return prompt
    
    def _call_ai(self, prompt: str) -> Optional[str]:
        """Llama a la IA según el provider configurado"""
        
        try:
            if self.provider == "claude":
                return self._call_claude(prompt)
            elif self.provider == "openai":
                return self._call_openai(prompt)
            elif self.provider == "perplexity":
                return self._call_perplexity(prompt)
            else:
                self._last_error = f"Provider desconocido: {self.provider}"
                return None
        except Exception as e:
            self._last_error = str(e)
            return None
    
    def _call_claude(self, prompt: str) -> Optional[str]:
        """Llama a Claude API"""
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            self._last_error = "ANTHROPIC_API_KEY no configurada"
            return None
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("content", [{}])[0].get("text", "")
        else:
            self._last_error = f"Claude API error: {response.status_code}"
            return None
    
    def _call_openai(self, prompt: str) -> Optional[str]:
        """Llama a OpenAI API"""
        api_key = st.secrets.get("OPENAI_API_KEY", "")
        if not api_key:
            self._last_error = "OPENAI_API_KEY no configurada"
            return None
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4000,
            "temperature": 0.3
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            self._last_error = f"OpenAI API error: {response.status_code}"
            return None
    
    def _call_perplexity(self, prompt: str) -> Optional[str]:
        """Llama a Perplexity API"""
        api_key = st.secrets.get("PERPLEXITY_API_KEY", "")
        if not api_key:
            self._last_error = "PERPLEXITY_API_KEY no configurada"
            return None
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4000,
            "temperature": 0.3
        }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            self._last_error = f"Perplexity API error: {response.status_code}"
            return None
    
    def _parse_ai_response(self, response: str, result: AIProductAnalysis):
        """Parsea la respuesta de la IA y llena el resultado"""
        
        # Extraer bloques JSON
        json_blocks = re.findall(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        
        for block in json_blocks:
            try:
                data = json.loads(block)
                
                # Clusters
                if "clusters" in data:
                    for c in data["clusters"]:
                        result.clusters.append(ProductCluster(
                            name=c.get("name", ""),
                            description=c.get("description", ""),
                            products=c.get("products", []),
                            characteristics=c.get("characteristics", []),
                            opportunity_score=c.get("opportunity_score", 50),
                            risk_score=c.get("risk_score", 50),
                            recommended_action=c.get("recommended_action", ""),
                            color=c.get("color", "#6366F1")
                        ))
                
                # Market gaps
                if "market_gaps" in data:
                    for g in data["market_gaps"]:
                        result.market_gaps.append(MarketGap(
                            name=g.get("name", ""),
                            description=g.get("description", ""),
                            potential=g.get("potential", "medio"),
                            competition_level=g.get("competition_level", "media"),
                            suggested_products=g.get("suggested_products", []),
                            estimated_demand=g.get("estimated_demand", 50)
                        ))
                
                # Predictions
                if "predictions" in data:
                    result.lifecycle_predictions = data["predictions"]
                
                # Risk matrix
                if "risk_matrix" in data:
                    result.risk_matrix = data["risk_matrix"]
                
                # Insights
                if "key_insights" in data:
                    result.key_insights = data["key_insights"]
                
                # Recommendations
                if "strategic_recommendations" in data:
                    result.strategic_recommendations = data["strategic_recommendations"]
                    
            except json.JSONDecodeError:
                continue
        
        # Si no se parsearon insights, intentar extraerlos del texto
        if not result.key_insights:
            insights_match = re.findall(r'(?:insight|hallazgo)[s]?[:\s]+([^\n]+)', response, re.IGNORECASE)
            result.key_insights = insights_match[:5] if insights_match else ["Análisis completado"]


# =============================================================================
# VISUALIZACIONES
# =============================================================================

def render_ai_clusters(clusters: List[ProductCluster]) -> None:
    """Renderiza los clusters identificados por IA"""
    
    if not clusters:
        st.info("No se identificaron clusters")
        return
    
    st.markdown("### 🎯 Clusters de Productos (IA)")
    
    # Gráfico de burbujas: oportunidad vs riesgo por cluster
    fig = go.Figure()
    
    for cluster in clusters:
        fig.add_trace(go.Scatter(
            x=[cluster.opportunity_score],
            y=[cluster.risk_score],
            mode='markers+text',
            marker=dict(
                size=len(cluster.products) * 15 + 30,
                color=cluster.color,
                opacity=0.7,
                line=dict(width=2, color='white')
            ),
            text=[cluster.name],
            textposition="middle center",
            textfont=dict(size=11, color="white"),
            hovertemplate=(
                f"<b>{cluster.name}</b><br>"
                f"Productos: {len(cluster.products)}<br>"
                f"Oportunidad: {cluster.opportunity_score}<br>"
                f"Riesgo: {cluster.risk_score}<br>"
                f"<extra></extra>"
            )
        ))
    
    # Cuadrantes
    fig.add_shape(type="rect", x0=0, y0=0, x1=50, y1=50,
                  fillcolor="rgba(16, 185, 129, 0.1)", line_width=0)  # Bajo riesgo, baja oportunidad
    fig.add_shape(type="rect", x0=50, y0=0, x1=100, y1=50,
                  fillcolor="rgba(59, 130, 246, 0.1)", line_width=0)  # Bajo riesgo, alta oportunidad
    fig.add_shape(type="rect", x0=0, y0=50, x1=50, y1=100,
                  fillcolor="rgba(107, 114, 128, 0.1)", line_width=0)  # Alto riesgo, baja oportunidad
    fig.add_shape(type="rect", x0=50, y0=50, x1=100, y1=100,
                  fillcolor="rgba(245, 158, 11, 0.1)", line_width=0)  # Alto riesgo, alta oportunidad
    
    fig.add_hline(y=50, line_dash="dash", line_color="#9CA3AF")
    fig.add_vline(x=50, line_dash="dash", line_color="#9CA3AF")
    
    # Etiquetas de cuadrantes
    fig.add_annotation(x=25, y=95, text="⚠️ Evitar", showarrow=False, font=dict(size=10, color="#6B7280"))
    fig.add_annotation(x=75, y=95, text="🎲 Alto riesgo/recompensa", showarrow=False, font=dict(size=10, color="#F59E0B"))
    fig.add_annotation(x=25, y=5, text="😴 Mantener", showarrow=False, font=dict(size=10, color="#10B981"))
    fig.add_annotation(x=75, y=5, text="⭐ Invertir", showarrow=False, font=dict(size=10, color="#3B82F6"))
    
    fig.update_layout(
        title="Mapa de Clusters: Oportunidad vs Riesgo",
        xaxis=dict(title="Oportunidad", range=[0, 100], showgrid=False),
        yaxis=dict(title="Riesgo", range=[0, 100], showgrid=False),
        showlegend=False,
        height=450,
        plot_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detalle de cada cluster
    cols = st.columns(len(clusters))
    for col, cluster in zip(cols, clusters):
        with col:
            st.markdown(
                f'<div style="background: {cluster.color}15; border-left: 4px solid {cluster.color}; '
                f'padding: 16px; border-radius: 8px;">'
                f'<h4 style="margin: 0 0 8px 0; color: {cluster.color};">{cluster.name}</h4>'
                f'<p style="font-size: 0.85rem; color: #4B5563; margin-bottom: 12px;">{cluster.description}</p>'
                f'<div style="font-size: 0.8rem; color: #6B7280;">'
                f'<b>Productos:</b> {", ".join(cluster.products[:5])}'
                f'{"..." if len(cluster.products) > 5 else ""}'
                f'</div>'
                f'<div style="margin-top: 12px; padding: 8px; background: {cluster.color}20; border-radius: 4px;">'
                f'<b>💡 Acción:</b> {cluster.recommended_action}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )


def render_risk_opportunity_matrix(risk_matrix: Dict[str, Any], products: List) -> None:
    """Renderiza la matriz de riesgo/oportunidad por producto"""
    
    if not risk_matrix:
        st.info("No hay datos de matriz riesgo/oportunidad")
        return
    
    st.markdown("### ⚖️ Matriz Riesgo/Oportunidad (IA)")
    
    # Preparar datos
    names = []
    opportunities = []
    risks = []
    colors = []
    
    color_map = {
        "estrella": "#F59E0B",
        "emergente": "#8B5CF6", 
        "consolidado": "#3B82F6",
        "nicho": "#6B7280"
    }
    
    for product_name, scores in risk_matrix.items():
        names.append(product_name)
        opportunities.append(scores.get("opportunity", 50))
        risks.append(scores.get("risk", 50))
        
        # Buscar categoría del producto
        category = "nicho"
        for p in products:
            p_name = getattr(p, 'name', p.get('name', '')) if hasattr(p, 'name') or isinstance(p, dict) else ''
            if p_name == product_name:
                cat = getattr(p, 'category', None) or p.get('category', 'nicho')
                if hasattr(cat, 'value'):
                    cat = cat.value
                category = cat
                break
        colors.append(color_map.get(category, "#6B7280"))
    
    fig = go.Figure()
    
    # Cuadrantes de fondo
    fig.add_shape(type="rect", x0=0, y0=0, x1=50, y1=50,
                  fillcolor="rgba(16, 185, 129, 0.08)", line_width=0)
    fig.add_shape(type="rect", x0=50, y0=0, x1=100, y1=50,
                  fillcolor="rgba(59, 130, 246, 0.08)", line_width=0)
    fig.add_shape(type="rect", x0=0, y0=50, x1=50, y1=100,
                  fillcolor="rgba(239, 68, 68, 0.08)", line_width=0)
    fig.add_shape(type="rect", x0=50, y0=50, x1=100, y1=100,
                  fillcolor="rgba(245, 158, 11, 0.08)", line_width=0)
    
    fig.add_hline(y=50, line_dash="dash", line_color="#D1D5DB")
    fig.add_vline(x=50, line_dash="dash", line_color="#D1D5DB")
    
    # Puntos
    fig.add_trace(go.Scatter(
        x=opportunities,
        y=risks,
        mode='markers+text',
        marker=dict(size=20, color=colors, line=dict(width=2, color='white')),
        text=names,
        textposition="top center",
        textfont=dict(size=9),
        hovertemplate="<b>%{text}</b><br>Oportunidad: %{x}<br>Riesgo: %{y}<extra></extra>"
    ))
    
    # Etiquetas
    fig.add_annotation(x=25, y=95, text="❌ EVITAR", showarrow=False, 
                      font=dict(size=11, color="#EF4444", weight="bold"))
    fig.add_annotation(x=75, y=95, text="🎲 APOSTAR", showarrow=False,
                      font=dict(size=11, color="#F59E0B", weight="bold"))
    fig.add_annotation(x=25, y=5, text="😴 MANTENER", showarrow=False,
                      font=dict(size=11, color="#10B981", weight="bold"))
    fig.add_annotation(x=75, y=5, text="🚀 INVERTIR", showarrow=False,
                      font=dict(size=11, color="#3B82F6", weight="bold"))
    
    fig.update_layout(
        xaxis=dict(title="Oportunidad →", range=[-5, 105]),
        yaxis=dict(title="Riesgo →", range=[-5, 105]),
        showlegend=False,
        height=500,
        plot_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_market_gaps(gaps: List[MarketGap]) -> None:
    """Renderiza los gaps de mercado identificados"""
    
    if not gaps:
        st.info("No se identificaron gaps de mercado")
        return
    
    st.markdown("### 🎯 Gaps de Mercado Identificados (IA)")
    
    potential_colors = {
        "alto": "#10B981",
        "medio": "#F59E0B", 
        "bajo": "#6B7280"
    }
    
    for gap in gaps:
        color = potential_colors.get(gap.potential.lower(), "#6B7280")
        
        st.markdown(
            f'<div style="background: white; border: 1px solid #E5E7EB; '
            f'border-radius: 12px; padding: 20px; margin-bottom: 16px;">'
            f'<div style="display: flex; justify-content: space-between; align-items: start;">'
            f'<div>'
            f'<h4 style="margin: 0; color: #1F2937;">💡 {gap.name}</h4>'
            f'<p style="color: #6B7280; margin: 8px 0;">{gap.description}</p>'
            f'</div>'
            f'<span style="background: {color}20; color: {color}; padding: 4px 12px; '
            f'border-radius: 20px; font-size: 0.8rem; font-weight: 600;">'
            f'Potencial {gap.potential.upper()}</span>'
            f'</div>'
            f'<div style="display: flex; gap: 24px; margin-top: 16px;">'
            f'<div>'
            f'<span style="font-size: 0.75rem; color: #9CA3AF;">Competencia</span><br>'
            f'<span style="font-weight: 600;">{gap.competition_level}</span>'
            f'</div>'
            f'<div>'
            f'<span style="font-size: 0.75rem; color: #9CA3AF;">Demanda estimada</span><br>'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'<div style="width: 100px; height: 8px; background: #F3F4F6; border-radius: 4px;">'
            f'<div style="width: {gap.estimated_demand}%; height: 100%; background: {color}; border-radius: 4px;"></div>'
            f'</div>'
            f'<span style="font-weight: 600;">{gap.estimated_demand}/100</span>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'<div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #E5E7EB;">'
            f'<span style="font-size: 0.75rem; color: #9CA3AF;">Productos sugeridos:</span><br>'
            f'<span style="color: #4B5563;">{", ".join(gap.suggested_products)}</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )


def render_lifecycle_predictions(predictions: Dict[str, str], products: List) -> None:
    """Renderiza las predicciones de ciclo de vida"""
    
    if not predictions:
        st.info("No hay predicciones de ciclo de vida")
        return
    
    st.markdown("### 🔮 Predicciones de Evolución (IA)")
    
    prediction_config = {
        "explosivo": {"icon": "🚀", "color": "#8B5CF6", "text": "Crecimiento explosivo esperado"},
        "creciendo": {"icon": "📈", "color": "#10B981", "text": "Seguirá creciendo"},
        "estable": {"icon": "➡️", "color": "#3B82F6", "text": "Se mantendrá estable"},
        "declive": {"icon": "📉", "color": "#EF4444", "text": "Posible declive"}
    }
    
    # Agrupar por predicción
    grouped = {}
    for product, prediction in predictions.items():
        pred_lower = prediction.lower()
        if pred_lower not in grouped:
            grouped[pred_lower] = []
        grouped[pred_lower].append(product)
    
    cols = st.columns(4)
    for i, (pred_type, config) in enumerate(prediction_config.items()):
        products_in_pred = grouped.get(pred_type, [])
        with cols[i]:
            st.markdown(
                f'<div style="background: {config["color"]}10; padding: 16px; '
                f'border-radius: 12px; text-align: center; min-height: 150px;">'
                f'<div style="font-size: 2rem;">{config["icon"]}</div>'
                f'<div style="font-weight: 600; color: {config["color"]}; margin: 8px 0;">'
                f'{pred_type.title()}</div>'
                f'<div style="font-size: 0.8rem; color: #6B7280; margin-bottom: 8px;">'
                f'{config["text"]}</div>'
                f'<div style="font-size: 1.5rem; font-weight: 700; color: #1F2937;">'
                f'{len(products_in_pred)}</div>'
                f'<div style="font-size: 0.75rem; color: #9CA3AF; margin-top: 8px;">'
                f'{", ".join(products_in_pred[:3])}'
                f'{"..." if len(products_in_pred) > 3 else ""}</div>'
                f'</div>',
                unsafe_allow_html=True
            )


def render_ai_insights(analysis: AIProductAnalysis) -> None:
    """Renderiza insights y recomendaciones de IA"""
    
    st.markdown("### 💡 Insights Estratégicos (IA)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔍 Hallazgos Clave")
        for i, insight in enumerate(analysis.key_insights[:5]):
            st.markdown(
                f'<div style="display: flex; gap: 12px; padding: 12px; '
                f'background: #F9FAFB; border-radius: 8px; margin-bottom: 8px;">'
                f'<span style="color: #6366F1; font-weight: 700;">{i+1}</span>'
                f'<span style="color: #374151;">{insight}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    
    with col2:
        st.markdown("#### 🎯 Recomendaciones")
        for rec in analysis.strategic_recommendations[:5]:
            st.markdown(
                f'<div style="display: flex; gap: 12px; padding: 12px; '
                f'background: #ECFDF5; border-radius: 8px; margin-bottom: 8px; '
                f'border-left: 3px solid #10B981;">'
                f'<span style="color: #059669;">✓</span>'
                f'<span style="color: #065F46;">{rec}</span>'
                f'</div>',
                unsafe_allow_html=True
            )


# =============================================================================
# FUNCIÓN PRINCIPAL DE RENDERIZADO
# =============================================================================

def render_ai_product_analysis(
    products: List,
    brand: str,
    market_context: str = ""
) -> Optional[AIProductAnalysis]:
    """
    Renderiza el panel completo de análisis de productos con IA.
    
    Args:
        products: Lista de productos
        brand: Nombre de la marca
        market_context: Contexto adicional
        
    Returns:
        AIProductAnalysis si se ejecutó, None si no
    """
    
    st.markdown("---")
    st.markdown("## 🤖 Análisis Inteligente de Productos")
    
    # Verificar APIs disponibles
    has_claude = bool(st.secrets.get("ANTHROPIC_API_KEY", ""))
    has_openai = bool(st.secrets.get("OPENAI_API_KEY", ""))
    has_perplexity = bool(st.secrets.get("PERPLEXITY_API_KEY", ""))
    
    if not (has_claude or has_openai or has_perplexity):
        st.warning(
            "⚠️ No hay API de IA configurada. Añade ANTHROPIC_API_KEY, OPENAI_API_KEY "
            "o PERPLEXITY_API_KEY en secrets.toml para habilitar el análisis inteligente."
        )
        return None
    
    # Selector de provider
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        available_providers = []
        if has_claude:
            available_providers.append("claude")
        if has_openai:
            available_providers.append("openai")
        if has_perplexity:
            available_providers.append("perplexity")
        
        provider = st.selectbox(
            "Modelo de IA",
            available_providers,
            format_func=lambda x: {"claude": "Claude (Anthropic)", "openai": "GPT-4 (OpenAI)", "perplexity": "Perplexity"}[x]
        )
    
    with col2:
        context = st.text_input(
            "Contexto adicional (opcional)",
            placeholder="Ej: Enfocarse en mercado español, temporada navideña...",
            value=market_context
        )
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        run_analysis = st.button("🧠 Analizar con IA", type="primary")
    
    # Ejecutar análisis
    if run_analysis:
        if len(products) < 2:
            st.warning("Se necesitan al menos 2 productos para el análisis")
            return None
        
        analyzer = AIProductAnalyzer(provider=provider)
        
        with st.spinner(f"Analizando {len(products)} productos con {provider.title()}..."):
            analysis = analyzer.analyze_products(
                products=products,
                brand=brand,
                market_context=context
            )
        
        if analysis.clusters or analysis.key_insights:
            st.session_state[f"ai_analysis_{brand}"] = analysis
            st.success("✅ Análisis completado")
        else:
            st.error(f"Error en el análisis: {analyzer._last_error}")
            return None
    
    # Mostrar resultados si existen
    analysis = st.session_state.get(f"ai_analysis_{brand}")
    
    if analysis:
        tabs = st.tabs(["🎯 Clusters", "⚖️ Riesgo/Oportunidad", "💡 Gaps de Mercado", "🔮 Predicciones", "📊 Insights"])
        
        with tabs[0]:
            render_ai_clusters(analysis.clusters)
        
        with tabs[1]:
            render_risk_opportunity_matrix(analysis.risk_matrix, products)
        
        with tabs[2]:
            render_market_gaps(analysis.market_gaps)
        
        with tabs[3]:
            render_lifecycle_predictions(analysis.lifecycle_predictions, products)
        
        with tabs[4]:
            render_ai_insights(analysis)
        
        return analysis
    
    return None
