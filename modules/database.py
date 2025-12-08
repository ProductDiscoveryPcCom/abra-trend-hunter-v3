"""
Database Module para Abra Trend Hunter
Proporciona persistencia de datos con múltiples backends

Backends soportados:
- Supabase (recomendado para producción)
- PostgreSQL directo
- SQLite (solo desarrollo local)
"""

import os
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import streamlit as st


@dataclass
class SearchRecord:
    """Registro de una búsqueda realizada"""
    keyword: str
    country: str
    timestamp: datetime = None
    user_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class TrendSnapshot:
    """Snapshot de tendencia en un momento dado"""
    keyword: str
    country: str
    date: date
    trend_value: int  # 0-100 de Google Trends
    volume_real: int = None  # Volumen real de Google Ads
    trend_score: int = None
    potential_score: int = None
    youtube_score: int = None
    news_sentiment: float = None


@dataclass
class ProductRecord:
    """Producto detectado y guardado"""
    name: str
    brand: str
    category: str = None
    first_seen: date = None
    last_seen: date = None
    trend_score: int = None
    potential_score: int = None
    lifecycle: str = None
    country: str = "ES"


@dataclass
class Alert:
    """Configuración de alerta"""
    keyword: str
    country: str
    threshold: int = 80
    email: str = None
    active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class DatabaseBackend:
    """Clase base abstracta para backends de base de datos"""
    
    def save_search(self, record: SearchRecord) -> bool:
        raise NotImplementedError
    
    def save_trend_snapshot(self, snapshot: TrendSnapshot) -> bool:
        raise NotImplementedError
    
    def get_trend_history(self, keyword: str, country: str, days: int = 90) -> List[TrendSnapshot]:
        raise NotImplementedError
    
    def save_product(self, product: ProductRecord) -> bool:
        raise NotImplementedError
    
    def get_products(self, brand: str = None, country: str = None) -> List[ProductRecord]:
        raise NotImplementedError
    
    def save_alert(self, alert: Alert) -> bool:
        raise NotImplementedError
    
    def get_alerts(self, active_only: bool = True) -> List[Alert]:
        raise NotImplementedError
    
    def get_search_history(self, limit: int = 100) -> List[SearchRecord]:
        raise NotImplementedError


class SupabaseBackend(DatabaseBackend):
    """Backend usando Supabase (PostgreSQL gestionado)"""
    
    def __init__(self, url: str = None, key: str = None):
        try:
            from supabase import create_client
        except ImportError:
            raise ImportError("Instala supabase: pip install supabase")
        
        self.url = url or st.secrets.get("SUPABASE_URL")
        self.key = key or st.secrets.get("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY requeridos")
        
        self.client = create_client(self.url, self.key)
    
    def save_search(self, record: SearchRecord) -> bool:
        try:
            self.client.table("searches").insert({
                "keyword": record.keyword,
                "country": record.country,
                "timestamp": record.timestamp.isoformat(),
                "user_id": record.user_id
            }).execute()
            return True
        except Exception as e:
            st.error(f"Error guardando búsqueda: {e}")
            return False
    
    def save_trend_snapshot(self, snapshot: TrendSnapshot) -> bool:
        try:
            data = {
                "keyword": snapshot.keyword,
                "country": snapshot.country,
                "date": snapshot.date.isoformat(),
                "trend_value": snapshot.trend_value,
                "volume_real": snapshot.volume_real,
                "trend_score": snapshot.trend_score,
                "potential_score": snapshot.potential_score,
                "youtube_score": snapshot.youtube_score,
                "news_sentiment": snapshot.news_sentiment
            }
            
            # Upsert: actualizar si existe, insertar si no
            self.client.table("trend_snapshots").upsert(
                data,
                on_conflict="keyword,country,date"
            ).execute()
            return True
        except Exception as e:
            st.error(f"Error guardando snapshot: {e}")
            return False
    
    def get_trend_history(self, keyword: str, country: str, days: int = 90) -> List[TrendSnapshot]:
        try:
            from datetime import timedelta
            since = (datetime.now() - timedelta(days=days)).date().isoformat()
            
            result = self.client.table("trend_snapshots")\
                .select("*")\
                .eq("keyword", keyword)\
                .eq("country", country)\
                .gte("date", since)\
                .order("date")\
                .execute()
            
            return [
                TrendSnapshot(
                    keyword=r["keyword"],
                    country=r["country"],
                    date=date.fromisoformat(r["date"]),
                    trend_value=r["trend_value"],
                    volume_real=r.get("volume_real"),
                    trend_score=r.get("trend_score"),
                    potential_score=r.get("potential_score"),
                    youtube_score=r.get("youtube_score"),
                    news_sentiment=r.get("news_sentiment")
                )
                for r in result.data
            ]
        except Exception as e:
            st.error(f"Error obteniendo historial: {e}")
            return []
    
    def save_product(self, product: ProductRecord) -> bool:
        try:
            data = {
                "name": product.name,
                "brand": product.brand,
                "category": product.category,
                "first_seen": product.first_seen.isoformat() if product.first_seen else None,
                "last_seen": product.last_seen.isoformat() if product.last_seen else date.today().isoformat(),
                "trend_score": product.trend_score,
                "potential_score": product.potential_score,
                "lifecycle": product.lifecycle,
                "country": product.country
            }
            
            self.client.table("products").upsert(
                data,
                on_conflict="name,brand,country"
            ).execute()
            return True
        except Exception as e:
            st.error(f"Error guardando producto: {e}")
            return False
    
    def get_products(self, brand: str = None, country: str = None) -> List[ProductRecord]:
        try:
            query = self.client.table("products").select("*")
            
            if brand:
                query = query.eq("brand", brand)
            if country:
                query = query.eq("country", country)
            
            result = query.order("last_seen", desc=True).execute()
            
            return [
                ProductRecord(
                    name=r["name"],
                    brand=r["brand"],
                    category=r.get("category"),
                    first_seen=date.fromisoformat(r["first_seen"]) if r.get("first_seen") else None,
                    last_seen=date.fromisoformat(r["last_seen"]) if r.get("last_seen") else None,
                    trend_score=r.get("trend_score"),
                    potential_score=r.get("potential_score"),
                    lifecycle=r.get("lifecycle"),
                    country=r.get("country", "ES")
                )
                for r in result.data
            ]
        except Exception as e:
            st.error(f"Error obteniendo productos: {e}")
            return []
    
    def save_alert(self, alert: Alert) -> bool:
        try:
            self.client.table("alerts").insert({
                "keyword": alert.keyword,
                "country": alert.country,
                "threshold": alert.threshold,
                "email": alert.email,
                "active": alert.active,
                "created_at": alert.created_at.isoformat()
            }).execute()
            return True
        except Exception as e:
            st.error(f"Error guardando alerta: {e}")
            return False
    
    def get_alerts(self, active_only: bool = True) -> List[Alert]:
        try:
            query = self.client.table("alerts").select("*")
            
            if active_only:
                query = query.eq("active", True)
            
            result = query.execute()
            
            return [
                Alert(
                    keyword=r["keyword"],
                    country=r["country"],
                    threshold=r.get("threshold", 80),
                    email=r.get("email"),
                    active=r.get("active", True),
                    created_at=datetime.fromisoformat(r["created_at"]) if r.get("created_at") else None
                )
                for r in result.data
            ]
        except Exception as e:
            st.error(f"Error obteniendo alertas: {e}")
            return []
    
    def get_search_history(self, limit: int = 100) -> List[SearchRecord]:
        try:
            result = self.client.table("searches")\
                .select("*")\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            return [
                SearchRecord(
                    keyword=r["keyword"],
                    country=r["country"],
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    user_id=r.get("user_id")
                )
                for r in result.data
            ]
        except Exception as e:
            st.error(f"Error obteniendo historial: {e}")
            return []


class SQLiteBackend(DatabaseBackend):
    """Backend usando SQLite (solo para desarrollo local)"""
    
    def __init__(self, db_path: str = "data/abra.db"):
        import sqlite3
        import os
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()
    
    def _get_conn(self):
        import sqlite3
        return sqlite3.connect(self.db_path)
    
    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS searches (
                    id INTEGER PRIMARY KEY,
                    keyword TEXT NOT NULL,
                    country TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT
                );
                
                CREATE TABLE IF NOT EXISTS trend_snapshots (
                    id INTEGER PRIMARY KEY,
                    keyword TEXT NOT NULL,
                    country TEXT NOT NULL,
                    date DATE NOT NULL,
                    trend_value INTEGER,
                    volume_real INTEGER,
                    trend_score INTEGER,
                    potential_score INTEGER,
                    youtube_score INTEGER,
                    news_sentiment REAL,
                    UNIQUE(keyword, country, date)
                );
                
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    category TEXT,
                    first_seen DATE,
                    last_seen DATE,
                    trend_score INTEGER,
                    potential_score INTEGER,
                    lifecycle TEXT,
                    country TEXT DEFAULT 'ES',
                    UNIQUE(name, brand, country)
                );
                
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY,
                    keyword TEXT NOT NULL,
                    country TEXT NOT NULL,
                    threshold INTEGER DEFAULT 80,
                    email TEXT,
                    active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_searches_keyword ON searches(keyword);
                CREATE INDEX IF NOT EXISTS idx_snapshots_keyword ON trend_snapshots(keyword, country);
                CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
            """)
    
    def save_search(self, record: SearchRecord) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO searches (keyword, country, timestamp, user_id) VALUES (?, ?, ?, ?)",
                    (record.keyword, record.country, record.timestamp.isoformat(), record.user_id)
                )
            return True
        except Exception as e:
            st.error(f"Error: {e}")
            return False
    
    def save_trend_snapshot(self, snapshot: TrendSnapshot) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO trend_snapshots 
                    (keyword, country, date, trend_value, volume_real, trend_score, potential_score, youtube_score, news_sentiment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot.keyword, snapshot.country, snapshot.date.isoformat(),
                    snapshot.trend_value, snapshot.volume_real, snapshot.trend_score,
                    snapshot.potential_score, snapshot.youtube_score, snapshot.news_sentiment
                ))
            return True
        except Exception as e:
            st.error(f"Error: {e}")
            return False
    
    def get_trend_history(self, keyword: str, country: str, days: int = 90) -> List[TrendSnapshot]:
        try:
            with self._get_conn() as conn:
                cursor = conn.execute("""
                    SELECT * FROM trend_snapshots
                    WHERE keyword = ? AND country = ?
                    AND date >= date('now', ?)
                    ORDER BY date
                """, (keyword, country, f'-{days} days'))
                
                return [
                    TrendSnapshot(
                        keyword=r[1], country=r[2], date=date.fromisoformat(r[3]),
                        trend_value=r[4], volume_real=r[5], trend_score=r[6],
                        potential_score=r[7], youtube_score=r[8], news_sentiment=r[9]
                    )
                    for r in cursor.fetchall()
                ]
        except Exception as e:
            st.error(f"Error: {e}")
            return []
    
    def save_product(self, product: ProductRecord) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO products 
                    (name, brand, category, first_seen, last_seen, trend_score, potential_score, lifecycle, country)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product.name, product.brand, product.category,
                    product.first_seen.isoformat() if product.first_seen else None,
                    product.last_seen.isoformat() if product.last_seen else date.today().isoformat(),
                    product.trend_score, product.potential_score, product.lifecycle, product.country
                ))
            return True
        except Exception as e:
            st.error(f"Error: {e}")
            return False
    
    def get_products(self, brand: str = None, country: str = None) -> List[ProductRecord]:
        try:
            with self._get_conn() as conn:
                query = "SELECT * FROM products WHERE 1=1"
                params = []
                
                if brand:
                    query += " AND brand = ?"
                    params.append(brand)
                if country:
                    query += " AND country = ?"
                    params.append(country)
                
                query += " ORDER BY last_seen DESC"
                
                cursor = conn.execute(query, params)
                
                return [
                    ProductRecord(
                        name=r[1], brand=r[2], category=r[3],
                        first_seen=date.fromisoformat(r[4]) if r[4] else None,
                        last_seen=date.fromisoformat(r[5]) if r[5] else None,
                        trend_score=r[6], potential_score=r[7], lifecycle=r[8], country=r[9]
                    )
                    for r in cursor.fetchall()
                ]
        except Exception as e:
            st.error(f"Error: {e}")
            return []
    
    def save_alert(self, alert: Alert) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO alerts (keyword, country, threshold, email, active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (alert.keyword, alert.country, alert.threshold, alert.email, alert.active, alert.created_at.isoformat())
                )
            return True
        except Exception as e:
            st.error(f"Error: {e}")
            return False
    
    def get_alerts(self, active_only: bool = True) -> List[Alert]:
        try:
            with self._get_conn() as conn:
                query = "SELECT * FROM alerts"
                if active_only:
                    query += " WHERE active = 1"
                
                cursor = conn.execute(query)
                
                return [
                    Alert(
                        keyword=r[1], country=r[2], threshold=r[3],
                        email=r[4], active=bool(r[5]),
                        created_at=datetime.fromisoformat(r[6]) if r[6] else None
                    )
                    for r in cursor.fetchall()
                ]
        except Exception as e:
            st.error(f"Error: {e}")
            return []
    
    def get_search_history(self, limit: int = 100) -> List[SearchRecord]:
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    "SELECT * FROM searches ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                
                return [
                    SearchRecord(
                        keyword=r[1], country=r[2],
                        timestamp=datetime.fromisoformat(r[3]),
                        user_id=r[4]
                    )
                    for r in cursor.fetchall()
                ]
        except Exception as e:
            st.error(f"Error: {e}")
            return []


# =============================================================================
# SINGLETON Y HELPERS
# =============================================================================

_db_instance: Optional[DatabaseBackend] = None


def get_database() -> Optional[DatabaseBackend]:
    """
    Obtiene instancia de base de datos según configuración.
    
    Prioridad:
    1. Supabase (si SUPABASE_URL y SUPABASE_KEY están configurados)
    2. SQLite (para desarrollo local)
    
    Returns:
        DatabaseBackend configurado o None si no hay configuración
    """
    global _db_instance
    
    if _db_instance is not None:
        return _db_instance
    
    # Intentar Supabase primero
    supabase_url = st.secrets.get("SUPABASE_URL", "")
    supabase_key = st.secrets.get("SUPABASE_KEY", "")
    
    if supabase_url and supabase_key:
        try:
            _db_instance = SupabaseBackend(supabase_url, supabase_key)
            return _db_instance
        except Exception as e:
            st.warning(f"Error conectando a Supabase: {e}. Usando SQLite local.")
    
    # Fallback a SQLite
    try:
        _db_instance = SQLiteBackend()
        return _db_instance
    except Exception as e:
        st.error(f"Error iniciando base de datos: {e}")
        return None


def save_search_record(keyword: str, country: str, user_id: str = None) -> bool:
    """Helper para guardar búsqueda"""
    db = get_database()
    if db:
        return db.save_search(SearchRecord(keyword=keyword, country=country, user_id=user_id))
    return False


def save_trend_data(
    keyword: str,
    country: str,
    trend_value: int,
    volume_real: int = None,
    scores: Dict[str, int] = None
) -> bool:
    """Helper para guardar snapshot de tendencia"""
    db = get_database()
    if db:
        snapshot = TrendSnapshot(
            keyword=keyword,
            country=country,
            date=date.today(),
            trend_value=trend_value,
            volume_real=volume_real,
            trend_score=scores.get("trend") if scores else None,
            potential_score=scores.get("potential") if scores else None,
            youtube_score=scores.get("youtube") if scores else None,
            news_sentiment=scores.get("sentiment") if scores else None
        )
        return db.save_trend_snapshot(snapshot)
    return False


def is_database_configured() -> bool:
    """Verifica si hay base de datos configurada"""
    return bool(
        st.secrets.get("SUPABASE_URL") and st.secrets.get("SUPABASE_KEY")
    )


# =============================================================================
# SQL PARA CREAR TABLAS EN SUPABASE/POSTGRESQL
# =============================================================================

SUPABASE_SCHEMA = """
-- Ejecutar en Supabase SQL Editor

-- Búsquedas realizadas
CREATE TABLE IF NOT EXISTS searches (
    id BIGSERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    country VARCHAR(2) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_id VARCHAR(100)
);

CREATE INDEX idx_searches_keyword ON searches(keyword);
CREATE INDEX idx_searches_timestamp ON searches(timestamp);

-- Snapshots de tendencias (histórico)
CREATE TABLE IF NOT EXISTS trend_snapshots (
    id BIGSERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    country VARCHAR(2) NOT NULL,
    date DATE NOT NULL,
    trend_value INT,
    volume_real INT,
    trend_score INT,
    potential_score INT,
    youtube_score INT,
    news_sentiment REAL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(keyword, country, date)
);

CREATE INDEX idx_snapshots_lookup ON trend_snapshots(keyword, country, date);

-- Productos detectados
CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    first_seen DATE,
    last_seen DATE,
    trend_score INT,
    potential_score INT,
    lifecycle VARCHAR(50),
    country VARCHAR(2) DEFAULT 'ES',
    UNIQUE(name, brand, country)
);

CREATE INDEX idx_products_brand ON products(brand);

-- Alertas configuradas
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    country VARCHAR(2) NOT NULL,
    threshold INT DEFAULT 80,
    email VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security (opcional pero recomendado)
-- ALTER TABLE searches ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE trend_snapshots ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE products ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
"""


def get_schema_sql() -> str:
    """Devuelve el SQL para crear las tablas"""
    return SUPABASE_SCHEMA
