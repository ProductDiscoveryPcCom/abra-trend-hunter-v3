# 🚀 Guía de Deploy - Abra Trend Hunter

## Requisitos Previos

### API Keys Necesarias

| API | Requerida | Propósito |
|-----|-----------|-----------|
| **SerpAPI** | ✅ Sí | Google Trends, News, PAA |
| **Supabase** | ✅ Sí | Autenticación por email + Caché |
| YouTube Data API | Opcional | YouTube Deep Dive |
| Perplexity API | Opcional | Inteligencia de Mercado |
| OpenAI/Claude | Opcional | Análisis IA |

---

## ⚠️ IMPORTANTE: Configurar Autenticación

La app usa **autenticación por email corporativo**. Solo pueden acceder usuarios con emails autorizados en Supabase.

### Paso 1: Crear proyecto en Supabase

1. Ve a [supabase.com](https://supabase.com) y crea cuenta
2. Crea nuevo proyecto
3. Copia **URL** y **anon key** de Settings > API

### Paso 2: Ejecutar SQL de setup

En **SQL Editor** de Supabase, ejecuta el contenido de `supabase_auth_setup.sql`:

```sql
-- Esto crea las tablas y añade los 8 usuarios autorizados
-- authorized_users: lista de emails permitidos
-- search_logs: registro de quién buscó qué
```

### Usuarios Autorizados Iniciales

| Email | Nombre |
|-------|--------|
| pablo.gonzalez@pccomponentes.com | Pablo González |
| product.discovery@pccomponentes.com | Product Discovery |
| paula.ferriz@pccomponentes.com | Paula Ferriz |
| minerva.sanchez@pccomponentes.com | Minerva Sánchez |
| claudia.vidal@pccomponentes.com | Claudia Vidal |
| araceli.rodriguez@pccomponentes.com | Araceli Rodríguez |
| maximo.sanchez@pccomponentes.com | Máximo Sánchez |
| ja.montesinos@pccomponentes.com | J.A. Montesinos |

### Añadir nuevos usuarios

```sql
INSERT INTO authorized_users (email, name, department) 
VALUES ('nuevo.usuario@pccomponentes.com', 'Nombre Apellido', 'Product Discovery');
```

### Desactivar usuario

```sql
UPDATE authorized_users SET is_active = false WHERE email = 'email@pccomponentes.com';
```

---

## Opción 1: Streamlit Community Cloud (Recomendado)

### Paso 1: Subir a GitHub

```bash
# Crear repo en GitHub y subir
git init
git add .
git commit -m "Initial commit - Abra Trend Hunter v1.0"
git remote add origin https://github.com/TU_USUARIO/abra-trend-hunter.git
git push -u origin main
```

### Paso 2: Conectar a Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Selecciona tu repositorio
4. Branch: `main`
5. Main file path: `app.py`

### Paso 3: Configurar Secrets

En Streamlit Cloud → Settings → Secrets:

```toml
# === REQUERIDO: APIs ===
SERPAPI_KEY = "tu_api_key_de_serpapi"

# === REQUERIDO: Autenticación + Caché ===
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# === OPCIONAL: YouTube ===
YOUTUBE_API_KEY = "tu_api_key_de_youtube"

# === OPCIONAL: IA ===
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
PERPLEXITY_API_KEY = "pplx-..."

# === OPCIONAL: Email ===
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "tu@email.com"
SMTP_PASSWORD = "tu_app_password"
```

### Paso 4: Verificar Deploy

La app estará disponible en:
`https://TU_USUARIO-abra-trend-hunter-app-xxxxx.streamlit.app`

---

## Opción 2: Docker (Self-hosted)

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (para cache de layers)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Puerto de Streamlit
EXPOSE 8501

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Comando de inicio
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  abra-trend-hunter:
    build: .
    ports:
      - "8501:8501"
    environment:
      - SERPAPI_KEY=${SERPAPI_KEY}
      - PASSWORD=${PASSWORD}
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY:-}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      - PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY:-}
      - SUPABASE_URL=${SUPABASE_URL:-}
      - SUPABASE_KEY=${SUPABASE_KEY:-}
    volumes:
      - ./.streamlit:/app/.streamlit:ro
    restart: unless-stopped
```

### Deploy con Docker

```bash
# Crear archivo .env con tus secrets
cp secrets.toml.example .env

# Editar .env con tus API keys
nano .env

# Build y run
docker-compose up -d

# Ver logs
docker-compose logs -f
```

---

## Opción 3: VPS / Cloud VM

### Ubuntu 22.04+

```bash
# 1. Actualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# 3. Crear directorio
mkdir -p /opt/abra-trend-hunter
cd /opt/abra-trend-hunter

# 4. Descomprimir app
unzip abra-trend-hunter-deploy.zip

# 5. Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate

# 6. Instalar dependencias
pip install -r requirements.txt

# 7. Configurar secrets
mkdir -p .streamlit
cat > .streamlit/secrets.toml << EOF
SERPAPI_KEY = "tu_api_key"
PASSWORD = "tu_password"
# ... resto de secrets
EOF

# 8. Ejecutar (desarrollo)
streamlit run app.py --server.port 8501

# 9. Para producción, usar systemd:
```

### Servicio systemd

```ini
# /etc/systemd/system/abra-trend-hunter.service
[Unit]
Description=Abra Trend Hunter
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/abra-trend-hunter
ExecStart=/opt/abra-trend-hunter/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable abra-trend-hunter
sudo systemctl start abra-trend-hunter
```

---

## Configuración de Caché Supabase

### 1. Crear proyecto en Supabase

1. Ve a [supabase.com](https://supabase.com)
2. Crea nuevo proyecto
3. Copia URL y API Key (anon/public)

### 2. Crear tabla

Ejecuta en SQL Editor:

```sql
CREATE TABLE IF NOT EXISTS trend_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cache_key TEXT UNIQUE NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

-- Índice para búsquedas rápidas
CREATE INDEX idx_cache_key ON trend_cache(cache_key);
CREATE INDEX idx_expires_at ON trend_cache(expires_at);

-- Función para limpiar expirados
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM trend_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;
```

### 3. Añadir secrets

```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Verificación Post-Deploy

### Checklist

- [ ] La app carga sin errores
- [ ] Login con password funciona
- [ ] Búsqueda de keyword retorna datos
- [ ] Gráfico de tendencia se muestra
- [ ] Score cards calculan correctamente
- [ ] Noticias se cargan (con banderas de idioma)
- [ ] YouTube Deep Dive funciona (si está configurado)
- [ ] PDF se genera correctamente
- [ ] Excel se descarga correctamente
- [ ] JSON export funciona
- [ ] Caché guarda y recupera datos

### Health Check

Accede a:
- `https://tu-app.streamlit.app` - App principal
- `https://tu-app.streamlit.app/?check=health` - Si implementas health endpoint

---

## Troubleshooting

### Error: "SerpAPI no configurada"
→ Verifica que `SERPAPI_KEY` está en secrets

### Error: "No se encontraron datos"
→ La keyword puede ser muy nueva o sin volumen
→ Prueba con keywords conocidas como "iPhone" o "Samsung"

### Error de caché
→ Verifica credenciales de Supabase
→ La app funciona sin caché, solo es más lenta

### Gráficos no cargan
→ Puede ser timeout de API
→ Refresca la página

---

## Soporte

Para reportar bugs o sugerir mejoras:
- Crear issue en GitHub
- Contactar al equipo de Product Discovery

---

**Versión:** 1.0
**Última actualización:** Diciembre 2025
**Líneas de código:** 27,584
**Archivos:** 59
