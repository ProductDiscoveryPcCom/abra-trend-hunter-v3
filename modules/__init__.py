"""
Abra Trend Hunter - Data Modules
Módulos independientes para cada fuente de datos
"""

from .google_trends import GoogleTrendsModule
from .related_queries import RelatedQueriesModule
from .serp_paa import PeopleAlsoAskModule
from .google_news import GoogleNewsModule
from .product_analysis import ProductAnalyzer, ProductData, ProductCategory, LifecycleStage
from .scoring import ScoringEngine
from .ai_analysis import AIAnalyzer
from .search_volume import SearchVolumeEstimator, estimate_from_trends_data

__all__ = [
    'GoogleTrendsModule',
    'RelatedQueriesModule', 
    'PeopleAlsoAskModule',
    'GoogleNewsModule',
    'ProductAnalyzer',
    'ProductData',
    'ProductCategory',
    'LifecycleStage',
    'ScoringEngine',
    'AIAnalyzer',
    'SearchVolumeEstimator',
    'estimate_from_trends_data'
]
