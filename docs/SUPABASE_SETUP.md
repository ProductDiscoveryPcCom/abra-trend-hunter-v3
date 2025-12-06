# 🗄️ Configuración de Supabase para Caché

## 1. Crear cuenta y proyecto

1. Ve a [supabase.com](https://supabase.com) y crea cuenta (gratis)
2. Click en "New Project"
3. Elige nombre (ej: "abra-trend-hunter")
4. Elige región (EU West para España)
5. Crea una contraseña segura para la BD
6. Espera ~2 minutos a que se cree

## 2. Obtener credenciales

1. Ve a **Project Settings** (icono engranaje)
2. Click en **API**
3. Copia:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6...`

## 3. Crear tabla

Ve a **SQL Editor** y ejecuta este script:

```sql
-- ============================================
-- TABLA DE CACHÉ PARA TREND HUNTER
-- ============================================

CREATE TABLE IF NOT EXISTS trend_cache (
    -- Identificador único
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Clave de búsqueda (única por combinación)
    keyword VARCHAR(255) NOT NULL,
    country VARCHAR(2) NOT NULL,
    timeframe VARCHAR(30) NOT NULL DEFAULT 'today 5-y',
    
    -- Versión del formato de datos (para invalidar si cambia estructura)
    data_version INT NOT NULL DEFAULT 1,
    
    -- Datos cacheados (JSONB para flexibilidad)
    timeline_data JSONB,
    related_data JSONB,
    google_ads_data JSONB,
    youtube_data JSONB,
    news_data JSONB,
    ai_analysis JSONB,
    extra_data JSONB,
    
    -- Scores calculados (para consultas rápidas)
    trend_score INT DEFAULT 0,
    potential_score INT DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Restricción de unicidad
    UNIQUE(keyword, country, timeframe)
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_cache_lookup 
    ON trend_cache(keyword, country, timeframe);

CREATE INDEX IF NOT EXISTS idx_cache_updated 
    ON trend_cache(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_cache_country 
    ON trend_cache(country);

-- Comentarios
COMMENT ON TABLE trend_cache IS 'Caché de búsquedas de tendencias - TTL 30 días';
COMMENT ON COLUMN trend_cache.data_version IS 'Versión del formato, incrementar si cambia estructura';
COMMENT ON COLUMN trend_cache.timeline_data IS 'Datos de Google Trends (puntos temporales)';
COMMENT ON COLUMN trend_cache.related_data IS 'Queries y topics relacionados';
COMMENT ON COLUMN trend_cache.google_ads_data IS 'Volúmenes de Google Ads';
COMMENT ON COLUMN trend_cache.youtube_data IS 'Métricas y videos de YouTube';
COMMENT ON COLUMN trend_cache.news_data IS 'Noticias relacionadas';
COMMENT ON COLUMN trend_cache.ai_analysis IS 'Análisis generado por IA';
```

## 4. (Opcional) Limpieza automática

Para limpiar datos viejos automáticamente, crea una función + cron:

```sql
-- Función para limpiar entradas expiradas (>30 días)
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM trend_cache 
    WHERE updated_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Para ejecutar manualmente:
-- SELECT cleanup_expired_cache();
```

Para cron automático, ve a **Database > Extensions** y habilita `pg_cron`, luego:

```sql
-- Ejecutar limpieza cada día a las 3:00 AM
SELECT cron.schedule(
    'cleanup-trend-cache',
    '0 3 * * *',
    'SELECT cleanup_expired_cache()'
);
```

## 5. Configurar secrets.toml

Añade a tu `.streamlit/secrets.toml`:

```toml
# ============================================
# SUPABASE - Caché de búsquedas
# ============================================
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 6. Instalar dependencia

Añadir a `requirements.txt`:

```
supabase>=2.0.0
```

## 7. Verificar

En la app, el sidebar mostrará:
```
💾 Caché: ✅ 0 búsquedas guardadas
```

---

## Uso del caché

El caché funciona automáticamente:

1. **Primera búsqueda** de "Beelink" + ES:
   - Llama APIs (SerpAPI, YouTube, etc.)
   - Guarda resultados en Supabase
   - Muestra: "🔄 Datos actualizados"

2. **Segunda búsqueda** (mismo día o dentro de 30 días):
   - Lee de Supabase (sin llamar APIs)
   - Muestra: "📦 Datos en caché (hace 4 horas)"

3. **Botón "🔄 Actualizar"**:
   - Ignora caché
   - Llama APIs de nuevo
   - Actualiza datos en Supabase

---

## Consultas útiles en Supabase

Ver todas las búsquedas guardadas:
```sql
SELECT keyword, country, trend_score, potential_score, updated_at
FROM trend_cache
ORDER BY updated_at DESC;
```

Ver búsquedas por país:
```sql
SELECT country, COUNT(*) as total
FROM trend_cache
GROUP BY country
ORDER BY total DESC;
```

Buscar una keyword específica:
```sql
SELECT * FROM trend_cache
WHERE keyword = 'beelink';
```

Limpiar manualmente datos viejos:
```sql
DELETE FROM trend_cache
WHERE updated_at < NOW() - INTERVAL '30 days';
```

---

## Límites del plan gratuito

| Recurso | Límite |
|---------|--------|
| Almacenamiento | 500 MB |
| Filas estimadas | ~10,000 búsquedas |
| Ancho de banda | 2 GB/mes |
| Requests | 500,000/mes |

Con 15 búsquedas/día × 30 días = 450 búsquedas/mes, estás muy dentro de los límites.
