-- Initialize MCP Production Database
-- Create necessary tables and sample data

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id INTEGER REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    project_id INTEGER REFERENCES projects(id),
    assigned_to INTEGER REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_sessions table for AI interactions
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id),
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create analytics table for metrics
CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    user_id INTEGER REFERENCES users(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample users
INSERT INTO users (username, email, full_name) VALUES
    ('admin', 'admin@mcp.local', 'MCP Administrator'),
    ('john_doe', 'john@example.com', 'John Doe'),
    ('jane_smith', 'jane@example.com', 'Jane Smith'),
    ('alice_wilson', 'alice@example.com', 'Alice Wilson')
ON CONFLICT (username) DO NOTHING;

-- Insert sample projects
INSERT INTO projects (name, description, owner_id, status) VALUES
    ('MCP Development', 'Main MCP server development project', 1, 'active'),
    ('AI Integration', 'Integrate AI capabilities into the platform', 2, 'active'),
    ('Database Optimization', 'Optimize database queries and performance', 3, 'active'),
    ('Frontend Dashboard', 'Create user-friendly dashboard interface', 4, 'planning')
ON CONFLICT DO NOTHING;

-- Insert sample tasks
INSERT INTO tasks (title, description, project_id, assigned_to, status, priority, due_date) VALUES
    ('Setup PostgreSQL', 'Configure PostgreSQL database with proper indexes', 1, 1, 'completed', 'high', '2024-01-15'),
    ('Implement Redis Caching', 'Add Redis caching layer for better performance', 1, 2, 'in_progress', 'medium', '2024-01-20'),
    ('OpenAI Integration', 'Connect OpenAI API for chat functionality', 2, 2, 'pending', 'high', '2024-01-25'),
    ('Query Optimization', 'Optimize slow database queries', 3, 3, 'in_progress', 'medium', '2024-01-30'),
    ('User Authentication', 'Implement JWT-based authentication', 1, 4, 'completed', 'high', '2024-01-10'),
    ('Dashboard Design', 'Create responsive dashboard layout', 4, 4, 'planning', 'low', '2024-02-05')
ON CONFLICT DO NOTHING;

-- Insert sample chat session
INSERT INTO chat_sessions (user_id, session_name) VALUES
    (1, 'MCP Server Support'),
    (2, 'AI Development Discussion'),
    (3, 'Database Query Help')
ON CONFLICT DO NOTHING;

-- Insert sample chat messages
INSERT INTO chat_messages (session_id, role, content) VALUES
    (1, 'user', 'How do I check the server health?'),
    (1, 'assistant', 'You can check server health by sending a GET request to /health endpoint. It will return the status of PostgreSQL and Redis connections.'),
    (2, 'user', 'What AI models are supported?'),
    (2, 'assistant', 'The server supports OpenAI models including GPT-3.5-turbo and GPT-4. You can specify the model in your chat requests.'),
    (3, 'user', 'How can I optimize my database queries?'),
    (3, 'assistant', 'Use EXPLAIN ANALYZE to understand query performance, add appropriate indexes, and consider using connection pooling for better resource management.')
ON CONFLICT DO NOTHING;

-- Insert sample analytics events
INSERT INTO analytics (event_type, event_data, user_id) VALUES
    ('server_start', '{"version": "1.0.0", "port": 3002}', 1),
    ('api_request', '{"endpoint": "/health", "response_time_ms": 45}', NULL),
    ('chat_session', '{"session_id": 1, "messages_count": 2}', 1),
    ('database_query', '{"query_type": "SELECT", "execution_time_ms": 23}', 2)
ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics(timestamp);

-- Create a view for task summary
CREATE OR REPLACE VIEW task_summary AS
SELECT 
    p.name as project_name,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as in_progress_tasks,
    COUNT(CASE WHEN t.status = 'pending' THEN 1 END) as pending_tasks
FROM projects p
LEFT JOIN tasks t ON p.id = t.project_id
GROUP BY p.id, p.name;

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mcpuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mcpuser;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mcpuser;

-- Print completion message
DO $$
BEGIN
    RAISE NOTICE 'MCP Production database initialized successfully!';
    RAISE NOTICE 'Tables created: users, projects, tasks, chat_sessions, chat_messages, analytics';
    RAISE NOTICE 'Sample data inserted for testing';
    RAISE NOTICE 'Indexes and triggers configured for performance';
END $$;