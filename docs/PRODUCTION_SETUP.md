# 🚀 Guía de Configuración: Entorno de Producción

Esta guía explica cómo convertir Abra Trend Hunter en un entorno real con persistencia de datos históricos.

---

## 📊 ¿Por qué necesitas una base de datos?

Sin base de datos, cada vez que cierras la app:
- ❌ Pierdes el historial de búsquedas
- ❌ No puedes ver evolución de tendencias en el tiempo
- ❌ No hay alertas guardadas
- ❌ No puedes comparar "hoy vs hace 3 meses"

Con base de datos:
- ✅ Guardas automáticamente cada búsqueda
- ✅ Acumulas snapshots diarios de tendencias
- ✅ Detectas patrones estacionales reales
- ✅ Creas alertas que funcionan
- ✅ Dashboard de histórico y evolución

---

## 🎯 Opciones de Base de Datos

| Opción | Dificultad | Costo | Recomendado para |
|--------|------------|-------|------------------|
| **Supabase** | ⭐ Fácil | Gratis (500MB) | Equipos pequeños |
| **PostgreSQL (Neon/Railway)** | ⭐⭐ Media | Gratis tier | Producción |
| **SQLite** | ⭐ Fácil | Gratis | Solo desarrollo local |

---

## 🏆 OPCIÓN RECOMENDADA: Supabase

### Paso 1: Crear cuenta en Supabase

1. Ve a https://supabase.com
2. Crea cuenta con GitHub o email
3. Crea nuevo proyecto (elige región EU para menor latencia)
4. Guarda la contraseña del proyecto

### Paso 2: Crear las tablas

1. En el dashboard, ve a **SQL Editor**
2. Copia y ejecuta este SQL:

```sql
-- Búsquedas realizadas
CREATE TABLE searches (
    id BIGSERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    country VARCHAR(2) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_id VARCHAR(100)
);

CREATE INDEX idx_searches_keyword ON searches(keyword);
CREATE INDEX idx_searches_timestamp ON searches(timestamp);

-- Snapshots de tendencias (histórico)
CREATE TABLE trend_snapshots (
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
CREATE TABLE products (
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
CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    country VARCHAR(2) NOT NULL,
    threshold INT DEFAULT 80,
    email VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Paso 3: Obtener credenciales

1. Ve a **Settings** → **API**
2. Copia:
   - **Project URL** (ej: `https://xxxxx.supabase.co`)
   - **anon public key** (empieza con `eyJ...`)

### Paso 4: Configurar en Streamlit

Añade a tu `secrets.toml`:

```toml
# Supabase (Base de datos)
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Paso 5: Instalar dependencia

```bash
pip install supabase
```

¡Listo! La app detectará automáticamente Supabase y empezará a guardar datos.

---

## 💻 Uso del módulo de base de datos

El módulo `modules/database.py` ya está creado. Úsalo así:

### Guardar una búsqueda
```python
from modules.database import save_search_record

# Se llama automáticamente al buscar
save_search_record(keyword="beelink", country="ES")
```

### Guardar snapshot de tendencia
```python
from modules.database import save_trend_data

save_trend_data(
    keyword="beelink ser5",
    country="ES",
    trend_value=75,  # 0-100 de Google Trends
    volume_real=12000,  # De Google Ads
    scores={
        "trend": 82,
        "potential": 75,
        "youtube": 68
    }
)
```

### Obtener historial
```python
from modules.database import get_database

db = get_database()
history = db.get_trend_history("beelink", "ES", days=90)

for snapshot in history:
    print(f"{snapshot.date}: {snapshot.trend_value}")
```

---

## 🔄 Integración automática (TODO)

Para que los datos se guarden automáticamente, añade en `app.py` después de cada búsqueda:

```python
# Al final de la función de búsqueda
from modules.database import save_search_record, save_trend_data

# Guardar búsqueda
save_search_record(keyword, selected_country)

# Guardar snapshot con scores
if trend_data:
    save_trend_data(
        keyword=keyword,
        country=selected_country,
        trend_value=trend_data.get("current_value", 0),
        volume_real=volume_data.get("volume") if volume_data else None,
        scores={
            "trend": trend_score,
            "potential": potential_score,
            "youtube": youtube_score
        }
    )
```

---

## 📈 Dashboard de Histórico (Futuro)

Con los datos guardados, puedes crear un dashboard que muestre:

1. **Evolución de keywords** - Gráfico de líneas con tendencia en el tiempo
2. **Comparativa temporal** - "Hace 1 mes" vs "Hoy"
3. **Keywords más buscadas** - Top 10 del mes
4. **Productos descubiertos** - Nuevos productos detectados
5. **Alertas activas** - Keywords que superaron umbral

---

## 🔔 Sistema de Alertas

### Crear alerta
```python
from modules.database import get_database, Alert

db = get_database()
db.save_alert(Alert(
    keyword="nvidia rtx 5090",
    country="ES",
    threshold=80,
    email="tu@email.com"
))
```

### Verificar alertas (para cron job)
```python
def check_alerts():
    db = get_database()
    alerts = db.get_alerts(active_only=True)
    
    for alert in alerts:
        # Obtener tendencia actual
        current_trend = get_current_trend(alert.keyword, alert.country)
        
        if current_trend >= alert.threshold:
            send_alert_email(alert.email, alert.keyword, current_trend)
```

---

## 🕐 Automatización con Cron

Para acumular datos automáticamente, programa un cron job:

### Opción A: GitHub Actions (gratis)

Crea `.github/workflows/daily-snapshot.yml`:

```yaml
name: Daily Trend Snapshot

on:
  schedule:
    - cron: '0 8 * * *'  # Cada día a las 8:00 UTC
  workflow_dispatch:

jobs:
  snapshot:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run snapshot
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          SERPAPI_KEY: ${{ secrets.SERPAPI_KEY }}
        run: python scripts/daily_snapshot.py
```

### Script `scripts/daily_snapshot.py`:

```python
"""
Script para ejecutar snapshots diarios de keywords monitorizadas
"""
import os
from modules.database import get_database, TrendSnapshot
from modules.google_trends import GoogleTrendsModule
from datetime import date

# Keywords a monitorizar diariamente
MONITORED_KEYWORDS = [
    ("beelink", "ES"),
    ("minisforum", "ES"),
    ("geekom", "ES"),
    # ... añade las que quieras
]

def main():
    db = get_database()
    trends = GoogleTrendsModule(os.environ["SERPAPI_KEY"])
    
    for keyword, country in MONITORED_KEYWORDS:
        try:
            data = trends.get_interest_over_time(keyword, country)
            current_value = data[-1]["value"] if data else 0
            
            db.save_trend_snapshot(TrendSnapshot(
                keyword=keyword,
                country=country,
                date=date.today(),
                trend_value=current_value
            ))
            print(f"✓ {keyword} ({country}): {current_value}")
        except Exception as e:
            print(f"✗ {keyword}: {e}")

if __name__ == "__main__":
    main()
```

---

## 📦 Resumen de archivos creados

| Archivo | Propósito |
|---------|-----------|
| `modules/database.py` | Módulo de persistencia con Supabase/SQLite |
| `utils/countries.py` | Mapeos centralizados de países e idiomas |
| `utils/formatting.py` | Funciones de formateo unificadas |
| `docs/FULL_AUDIT_REPORT.md` | Informe completo de auditoría |
| `docs/PRODUCTION_SETUP.md` | Esta guía |

---

## ✅ Checklist de producción

- [ ] Crear cuenta en Supabase
- [ ] Ejecutar SQL para crear tablas
- [ ] Añadir SUPABASE_URL y SUPABASE_KEY a secrets.toml
- [ ] Instalar `pip install supabase`
- [ ] Integrar guardado automático en app.py
- [ ] Configurar GitHub Actions para snapshots diarios
- [ ] Crear dashboard de histórico

---

## 🆘 Troubleshooting

### "Error conectando a Supabase"
- Verifica que SUPABASE_URL empiece con `https://`
- Verifica que SUPABASE_KEY sea el `anon public key`

### "No se guardan los datos"
- Verifica que las tablas existan en Supabase
- Revisa los logs en el dashboard de Supabase

### "SQLite no persiste en Streamlit Cloud"
- SQLite es solo para desarrollo local
- En Streamlit Cloud, usa Supabase obligatoriamente
