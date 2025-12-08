-- ============================================
-- ABRA TREND HUNTER - Setup de Autenticación
-- Ejecutar en Supabase SQL Editor
-- ============================================

-- 1. Tabla de usuarios autorizados
CREATE TABLE IF NOT EXISTS authorized_users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    department TEXT DEFAULT 'Product Discovery',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- 2. Insertar usuarios autorizados
-- IMPORTANTE: Reemplaza estos emails de ejemplo con los reales de tu equipo
-- Puedes añadir más usuarios o modificar los existentes
INSERT INTO authorized_users (email, name, department) VALUES
    ('admin@tuempresa.com', 'Administrador', 'Admin'),
    ('usuario1@tuempresa.com', 'Usuario 1', 'Product Discovery'),
    ('usuario2@tuempresa.com', 'Usuario 2', 'Product Discovery')
ON CONFLICT (email) DO NOTHING;

-- Para añadir más usuarios después:
-- INSERT INTO authorized_users (email, name) VALUES ('nuevo@tuempresa.com', 'Nombre');

-- Para desactivar un usuario:
-- UPDATE authorized_users SET is_active = false WHERE email = 'usuario@tuempresa.com';

-- 3. Tabla de logs de búsquedas
CREATE TABLE IF NOT EXISTS search_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_email TEXT NOT NULL,
    keyword TEXT NOT NULL,
    country TEXT DEFAULT 'ES',
    timeframe TEXT DEFAULT 'today 12-m',
    trend_score INTEGER,
    potential_score INTEGER,
    searched_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_authorized_email ON authorized_users(email);
CREATE INDEX IF NOT EXISTS idx_authorized_active ON authorized_users(is_active);
CREATE INDEX IF NOT EXISTS idx_search_logs_email ON search_logs(user_email);
CREATE INDEX IF NOT EXISTS idx_search_logs_date ON search_logs(searched_at);

-- 5. Añadir columna user_email a trend_cache si existe
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'trend_cache') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'trend_cache' AND column_name = 'user_email') THEN
            ALTER TABLE trend_cache ADD COLUMN user_email TEXT;
        END IF;
    END IF;
END $$;

-- 6. Función para verificar si un email está autorizado
CREATE OR REPLACE FUNCTION is_user_authorized(user_email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM authorized_users 
        WHERE email = LOWER(user_email) AND is_active = true
    );
END;
$$ LANGUAGE plpgsql;

-- 7. Función para actualizar último login
CREATE OR REPLACE FUNCTION update_last_login(user_email TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE authorized_users 
    SET last_login = NOW() 
    WHERE email = LOWER(user_email);
END;
$$ LANGUAGE plpgsql;

-- 8. Vista para estadísticas de uso
CREATE OR REPLACE VIEW user_search_stats AS
SELECT 
    u.email,
    u.name,
    u.last_login,
    COUNT(s.id) as total_searches,
    MAX(s.searched_at) as last_search
FROM authorized_users u
LEFT JOIN search_logs s ON u.email = s.user_email
GROUP BY u.email, u.name, u.last_login
ORDER BY total_searches DESC;

-- 9. Vista para búsquedas recientes
CREATE OR REPLACE VIEW recent_searches AS
SELECT 
    s.user_email,
    u.name as user_name,
    s.keyword,
    s.country,
    s.trend_score,
    s.potential_score,
    s.searched_at
FROM search_logs s
LEFT JOIN authorized_users u ON s.user_email = u.email
ORDER BY s.searched_at DESC
LIMIT 100;

-- Verificar instalación
SELECT 'Setup completado. Usuarios autorizados:' as status;
SELECT email, name, is_active FROM authorized_users ORDER BY name;

-- ============================================
-- 10. TRACKING DE USO DE APIs
-- ============================================

-- Tabla principal de uso de APIs
CREATE TABLE IF NOT EXISTS api_usage_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_email TEXT,
    api_name TEXT NOT NULL,  -- 'serpapi', 'claude', 'openai', 'perplexity'
    endpoint TEXT,           -- endpoint específico: 'google_trends', 'google_news', etc.
    keyword TEXT,            -- keyword buscada (si aplica)
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    estimated_cost DECIMAL(10, 6) DEFAULT 0,  -- en USD
    response_status TEXT DEFAULT 'success',   -- 'success', 'error', 'cached'
    cached BOOLEAN DEFAULT false,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para consultas rápidas
CREATE INDEX IF NOT EXISTS idx_api_usage_api ON api_usage_logs(api_name);
CREATE INDEX IF NOT EXISTS idx_api_usage_date ON api_usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_user ON api_usage_logs(user_email);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage_logs(endpoint);

-- Vista de costes diarios por API
CREATE OR REPLACE VIEW daily_api_costs AS
SELECT 
    DATE(created_at) as date,
    api_name,
    COUNT(*) as total_calls,
    SUM(CASE WHEN cached THEN 0 ELSE 1 END) as billable_calls,
    SUM(tokens_input) as total_tokens_in,
    SUM(tokens_output) as total_tokens_out,
    SUM(estimated_cost) as total_cost_usd
FROM api_usage_logs
GROUP BY DATE(created_at), api_name
ORDER BY date DESC, api_name;

-- Vista de costes por usuario
CREATE OR REPLACE VIEW user_api_costs AS
SELECT 
    user_email,
    api_name,
    COUNT(*) as total_calls,
    SUM(CASE WHEN cached THEN 0 ELSE 1 END) as billable_calls,
    SUM(estimated_cost) as total_cost_usd,
    MAX(created_at) as last_call
FROM api_usage_logs
WHERE user_email IS NOT NULL
GROUP BY user_email, api_name
ORDER BY total_cost_usd DESC;

-- Vista de resumen mensual
CREATE OR REPLACE VIEW monthly_api_summary AS
SELECT 
    TO_CHAR(created_at, 'YYYY-MM') as month,
    api_name,
    COUNT(*) as total_calls,
    SUM(CASE WHEN cached THEN 0 ELSE 1 END) as billable_calls,
    SUM(estimated_cost) as total_cost_usd
FROM api_usage_logs
GROUP BY TO_CHAR(created_at, 'YYYY-MM'), api_name
ORDER BY month DESC, api_name;

-- Vista de keywords más buscadas
CREATE OR REPLACE VIEW top_keywords_cost AS
SELECT 
    keyword,
    COUNT(*) as search_count,
    SUM(estimated_cost) as total_cost_usd,
    array_agg(DISTINCT api_name) as apis_used
FROM api_usage_logs
WHERE keyword IS NOT NULL AND keyword != ''
GROUP BY keyword
ORDER BY search_count DESC
LIMIT 50;

-- Función para obtener coste del mes actual
CREATE OR REPLACE FUNCTION get_current_month_cost()
RETURNS TABLE(api_name TEXT, calls BIGINT, cost DECIMAL) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.api_name,
        COUNT(*)::BIGINT as calls,
        COALESCE(SUM(l.estimated_cost), 0)::DECIMAL as cost
    FROM api_usage_logs l
    WHERE DATE_TRUNC('month', l.created_at) = DATE_TRUNC('month', NOW())
    GROUP BY l.api_name;
END;
$$ LANGUAGE plpgsql;
