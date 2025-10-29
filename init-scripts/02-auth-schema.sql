-- ============================================================================
-- AUTHENTICATION & AUTHORIZATION DATABASE SCHEMA
-- ============================================================================
--
-- Production-ready authentication system with:
-- - User management with bcrypt password hashing
-- - Role-based access control (RBAC)
-- - API key authentication
-- - Session management with Redis integration
-- - Audit logging for security
--
-- NO mock data, NO test users, NO default passwords
-- All users must be created through the registration API
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- USERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_username_check CHECK (username ~ '^[a-zA-Z0-9_-]{3,50}$'),
    CONSTRAINT users_role_check CHECK (role IN ('admin', 'manager', 'user', 'api', 'mcp', 'readonly'))
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Comments for users table
COMMENT ON TABLE users IS 'User accounts with bcrypt password hashing';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password (cost factor 12)';
COMMENT ON COLUMN users.role IS 'User role: admin, manager, user, api, mcp, readonly';
COMMENT ON COLUMN users.failed_login_attempts IS 'Counter for rate limiting';
COMMENT ON COLUMN users.locked_until IS 'Account locked until this timestamp (for brute force protection)';

-- ============================================================================
-- API KEYS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    permissions TEXT[] NOT NULL DEFAULT ARRAY['read'],
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT api_keys_name_check CHECK (LENGTH(name) >= 3)
);

-- Indexes for api_keys table
CREATE INDEX idx_api_keys_api_key ON api_keys(api_key);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);

-- Comments for api_keys table
COMMENT ON TABLE api_keys IS 'API keys for programmatic access';
COMMENT ON COLUMN api_keys.api_key IS 'Hashed API key (format: horme_xxxx)';
COMMENT ON COLUMN api_keys.permissions IS 'Array of permissions: read, write, delete, admin';

-- ============================================================================
-- SESSIONS TABLE (for Redis backup/audit)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for sessions table
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- Comments for sessions table
COMMENT ON TABLE sessions IS 'Session tracking for audit and Redis backup';
COMMENT ON COLUMN sessions.token_hash IS 'SHA-256 hash of JWT token (for audit trail)';

-- ============================================================================
-- AUDIT LOG TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    resource_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for audit_log table
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX idx_audit_log_status ON audit_log(status);

-- Comments for audit_log table
COMMENT ON TABLE audit_log IS 'Security audit trail for all authentication events';
COMMENT ON COLUMN audit_log.action IS 'Action performed: login, logout, register, update, delete, access_denied';
COMMENT ON COLUMN audit_log.status IS 'Status: success, failure, error';

-- ============================================================================
-- PASSWORD RESET TOKENS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for password_reset_tokens table
CREATE INDEX idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_tokens_expires_at ON password_reset_tokens(expires_at);

-- Comments
COMMENT ON TABLE password_reset_tokens IS 'One-time password reset tokens';

-- ============================================================================
-- PERMISSIONS TABLE (for fine-grained access control)
-- ============================================================================

CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for permissions table
CREATE INDEX idx_permissions_name ON permissions(name);

-- Insert default permissions
INSERT INTO permissions (name, description) VALUES
    ('read', 'Read access to resources'),
    ('write', 'Write access to resources'),
    ('delete', 'Delete access to resources'),
    ('admin', 'Administrative access'),
    ('api_access', 'API access'),
    ('mcp_access', 'MCP server access'),
    ('websocket_access', 'WebSocket access')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- USER PERMISSIONS MAPPING
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_permissions (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    granted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    PRIMARY KEY (user_id, permission_id)
);

-- Indexes for user_permissions table
CREATE INDEX idx_user_permissions_user_id ON user_permissions(user_id);
CREATE INDEX idx_user_permissions_permission_id ON user_permissions(permission_id);

-- Comments
COMMENT ON TABLE user_permissions IS 'Maps users to specific permissions';

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to clean expired sessions
CREATE OR REPLACE FUNCTION clean_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sessions WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean expired password reset tokens
CREATE OR REPLACE FUNCTION clean_expired_password_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM password_reset_tokens
    WHERE expires_at < NOW() OR used_at IS NOT NULL;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to log authentication events
CREATE OR REPLACE FUNCTION log_auth_event(
    p_user_id INTEGER,
    p_action VARCHAR(100),
    p_status VARCHAR(50),
    p_ip_address INET DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO audit_log (user_id, action, status, ip_address, error_message)
    VALUES (p_user_id, p_action, p_status, p_ip_address, p_error_message);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for active users with their permissions
CREATE OR REPLACE VIEW active_users_with_permissions AS
SELECT
    u.id,
    u.email,
    u.username,
    u.name,
    u.role,
    u.created_at,
    u.last_login,
    ARRAY_AGG(DISTINCT p.name) as permissions
FROM users u
LEFT JOIN user_permissions up ON u.id = up.user_id
LEFT JOIN permissions p ON up.permission_id = p.id
WHERE u.is_active = true
GROUP BY u.id, u.email, u.username, u.name, u.role, u.created_at, u.last_login;

-- View for active sessions
CREATE OR REPLACE VIEW active_sessions AS
SELECT
    s.id,
    s.user_id,
    u.email,
    u.username,
    s.ip_address,
    s.expires_at,
    s.created_at,
    s.last_activity
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE s.expires_at > NOW();

-- View for audit trail (last 7 days)
CREATE OR REPLACE VIEW recent_audit_events AS
SELECT
    a.id,
    a.user_id,
    u.email,
    u.username,
    a.action,
    a.status,
    a.ip_address,
    a.created_at
FROM audit_log a
LEFT JOIN users u ON a.user_id = u.id
WHERE a.created_at > NOW() - INTERVAL '7 days'
ORDER BY a.created_at DESC;

-- ============================================================================
-- SECURITY POLICIES (Row Level Security)
-- ============================================================================

-- Enable RLS on sensitive tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own data
CREATE POLICY users_select_own ON users
    FOR SELECT
    USING (id = current_setting('app.current_user_id', TRUE)::INTEGER OR
           current_setting('app.current_user_role', TRUE) = 'admin');

-- Policy: Only admins can insert users
CREATE POLICY users_insert_admin ON users
    FOR INSERT
    WITH CHECK (current_setting('app.current_user_role', TRUE) = 'admin');

-- Policy: Users can update their own data, admins can update all
CREATE POLICY users_update_own ON users
    FOR UPDATE
    USING (id = current_setting('app.current_user_id', TRUE)::INTEGER OR
           current_setting('app.current_user_role', TRUE) = 'admin');

-- ============================================================================
-- GRANTS (for application user)
-- ============================================================================

-- Create application role if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'horme_app') THEN
        CREATE ROLE horme_app WITH LOGIN;
    END IF;
END
$$;

-- Grant permissions to application role
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO horme_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO horme_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO horme_app;

-- ============================================================================
-- INITIAL DATA VALIDATION
-- ============================================================================

-- Verify schema creation
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('users', 'api_keys', 'sessions', 'audit_log',
                       'password_reset_tokens', 'permissions', 'user_permissions');

    IF table_count = 7 THEN
        RAISE NOTICE '✅ Authentication schema created successfully: % tables', table_count;
    ELSE
        RAISE WARNING '⚠️  Expected 7 tables, found %', table_count;
    END IF;
END
$$;

-- Log schema initialization
INSERT INTO audit_log (action, status, metadata)
VALUES (
    'schema_init',
    'success',
    jsonb_build_object(
        'version', '1.0.0',
        'timestamp', NOW(),
        'description', 'Authentication schema initialized'
    )
);

-- ============================================================================
-- MAINTENANCE RECOMMENDATIONS
-- ============================================================================

-- Run these queries periodically (via cron or scheduled task):
--
-- 1. Clean expired sessions (daily):
--    SELECT clean_expired_sessions();
--
-- 2. Clean expired password tokens (daily):
--    SELECT clean_expired_password_tokens();
--
-- 3. Archive old audit logs (monthly):
--    DELETE FROM audit_log WHERE created_at < NOW() - INTERVAL '90 days';
--
-- 4. Vacuum and analyze (weekly):
--    VACUUM ANALYZE users, sessions, audit_log;
--
-- ============================================================================

RAISE NOTICE '✅ Authentication schema initialization complete!';
RAISE NOTICE '📋 Tables created: users, api_keys, sessions, audit_log, password_reset_tokens, permissions, user_permissions';
RAISE NOTICE '🔒 Row-level security enabled on users, sessions, api_keys';
RAISE NOTICE '🚀 Ready for production use!';
RAISE NOTICE '';
RAISE NOTICE 'Next steps:';
RAISE NOTICE '1. Create admin user via API: POST /api/auth/register';
RAISE NOTICE '2. Configure Redis for session caching';
RAISE NOTICE '3. Set up scheduled maintenance tasks';
