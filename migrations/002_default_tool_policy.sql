-- Default global tool policy migration
-- Creates a global policy allowing basic safe tools

INSERT INTO tool_policies (id, scope_type, scope_id, mode, tools, created_at, updated_at)
VALUES (
    'default-global-policy',
    'global',
    NULL,
    'allowlist',
    '{"tools": ["read_file", "list_dir", "web_search", "fetch_url", "message"]}',
    NOW(),
    NOW()
)
ON CONFLICT DO NOTHING;
