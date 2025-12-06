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
INSERT INTO authorized_users (email, name, department) VALUES
    ('pablo.gonzalez@pccomponentes.com', 'Pablo González', 'Product Discovery'),
    ('product.discovery@pccomponentes.com', 'Product Discovery', 'Product Discovery'),
    ('paula.ferriz@pccomponentes.com', 'Paula Ferriz', 'Product Discovery'),
    ('minerva.sanchez@pccomponentes.com', 'Minerva Sánchez', 'Product Discovery'),
    ('claudia.vidal@pccomponentes.com', 'Claudia Vidal', 'Product Discovery'),
    ('araceli.rodriguez@pccomponentes.com', 'Araceli Rodríguez', 'Product Discovery'),
    ('maximo.sanchez@pccomponentes.com', 'Máximo Sánchez', 'Product Discovery'),
    ('ja.montesinos@pccomponentes.com', 'J.A. Montesinos', 'Product Discovery')
ON CONFLICT (email) DO NOTHING;

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
