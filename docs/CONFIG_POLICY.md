# Configuration and Policy Management

Complete guide for managing integration credentials and tool access policies in nanobot.

## Overview

The nanobot backend includes a comprehensive configuration and policy system that provides:

1. **Integration Credentials** - Secure storage of API tokens and secrets with encryption
2. **Tool Policies** - Allowlist-based access control for tools at multiple scope levels
3. **Policy Enforcement** - Runtime checking to prevent unauthorized tool usage

## Integration Credentials

Integration credentials allow you to securely store API tokens and secrets for external services like Telegram, Slack, etc.

### Features

- **Encrypted Storage** - All tokens encrypted using Fernet (AES-128)
- **Never Exposed** - API never returns decrypted tokens
- **Credential Rotation** - Support for updating tokens
- **Status Tracking** - Track credential validity
- **Metadata** - Store additional configuration per integration

### API Endpoints

#### List Integrations

```bash
GET /api/v1/config/integrations?integration_type=telegram
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "integration_type": "telegram",
    "display_name": "Main Bot",
    "status": "valid",
    "meta": {
      "webhook_url": "https://example.com/webhook"
    },
    "created_at": "2026-03-05T22:00:00Z",
    "updated_at": "2026-03-05T22:00:00Z"
  }
]
```

#### Create Integration

```bash
POST /api/v1/config/integrations/telegram
Content-Type: application/json

{
  "display_name": "Main Bot",
  "token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
  "meta": {
    "webhook_url": "https://example.com/webhook",
    "default_chat_ids": ["12345", "67890"]
  }
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "integration_type": "telegram",
  "display_name": "Main Bot",
  "status": "valid",
  "meta": {
    "webhook_url": "https://example.com/webhook",
    "default_chat_ids": ["12345", "67890"]
  },
  "created_at": "2026-03-05T22:00:00Z",
  "updated_at": "2026-03-05T22:00:00Z"
}
```

#### Rotate Credentials

```bash
POST /api/v1/config/integrations/{credential_id}/rotate
Content-Type: application/json

{
  "token": "new-token-here"
}
```

#### Delete Integration

```bash
DELETE /api/v1/config/integrations/{credential_id}
```

## Tool Policies

Tool policies control which tools can be executed in different contexts using an allowlist-based approach.

### Policy Scopes

Policies are hierarchical and resolved in order of specificity:

1. **Thread-level** - Most specific, applies to a single thread
2. **Workspace-level** - Applies to all threads in a workspace
3. **Global** - Default for all threads

**Resolution Example:**
```
Global:    allowlist = ["postgres_query", "artifact_writer"]
Workspace: allowlist = ["postgres_query", "artifact_writer", "vector_search"]
Thread:    allowlist = ["postgres_query"]

Result for thread: Only "postgres_query" is allowed
```

### Policy Modes

- **allowlist** (recommended) - Only listed tools are allowed
- **denylist** - All tools except listed ones are allowed

**Default:** If no policy exists, all tools are denied (secure by default).

### API Endpoints

#### Get Policy

```bash
GET /api/v1/config/tool-policy?scope_type=global
GET /api/v1/config/tool-policy?scope_type=thread&scope_id=thread-123
```

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "scope_type": "global",
  "scope_id": null,
  "mode": "allowlist",
  "tools": [
    "postgres_query",
    "artifact_writer",
    "vector_search"
  ],
  "created_at": "2026-03-05T22:00:00Z",
  "updated_at": "2026-03-05T22:00:00Z"
}
```

#### Create/Update Policy

```bash
PUT /api/v1/config/tool-policy
Content-Type: application/json

{
  "scope_type": "global",
  "mode": "allowlist",
  "tools": [
    "postgres_query",
    "artifact_writer",
    "vector_search"
  ]
}
```

**Thread-specific policy:**
```json
{
  "scope_type": "thread",
  "scope_id": "thread-123",
  "mode": "allowlist",
  "tools": ["postgres_query"]
}
```

#### Delete Policy

```bash
DELETE /api/v1/config/tool-policy?scope_type=global
DELETE /api/v1/config/tool-policy?scope_type=thread&scope_id=thread-123
```

## Policy Enforcement

Tool policies are enforced at runtime in the `ToolExecutor`:

1. When a tool is requested, the executor checks the effective policy
2. If the tool is not in the allowlist, execution is denied
3. Policy violations are logged with full context
4. A `PermissionError` is raised

**Enforcement Flow:**
```
Tool Execution Request
       ↓
Load Effective Policy (thread → workspace → global)
       ↓
Check if tool in allowlist
       ↓
   Allowed?
   ├─ Yes → Check permission level → Execute
   └─ No  → Log violation → Raise PermissionError
```

## Security Best Practices

### 1. Use Allowlists

Always use allowlist mode (default) rather than denylist:

```json
{
  "mode": "allowlist",
  "tools": ["postgres_query", "artifact_writer"]
}
```

### 2. Principle of Least Privilege

Only grant access to tools that are absolutely necessary:

```json
// Good - minimal tools
{
  "scope_type": "thread",
  "scope_id": "analytics-thread",
  "mode": "allowlist",
  "tools": ["postgres_query"]
}

// Bad - too permissive
{
  "scope_type": "global",
  "mode": "allowlist",
  "tools": ["*"]  // Don't do this
}
```

### 3. Scope Policies Appropriately

Use the most specific scope possible:

- **Global** - Only for widely-used, safe tools
- **Workspace** - For team-specific tool access
- **Thread** - For specific use cases requiring restricted access

### 4. Rotate Credentials Regularly

```bash
# Rotate integration credentials periodically
POST /api/v1/config/integrations/{id}/rotate
{
  "token": "new-token"
}
```

### 5. Monitor Policy Violations

Check logs for denied tool executions:

```bash
docker compose logs worker | grep "denied_by_policy"
```

## Environment Setup

### Encryption Key

Generate an encryption key for credential storage:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add to `.env`:

```bash
ENCRYPTION_KEY=your-generated-key-here
```

**Important:** Keep this key secure and never commit it to version control.

## Examples

### Example 1: Global Policy for Safe Tools

```bash
curl -X PUT http://localhost:8000/api/v1/config/tool-policy \
  -H "Content-Type: application/json" \
  -d '{
    "scope_type": "global",
    "mode": "allowlist",
    "tools": ["postgres_query", "artifact_writer", "vector_search"]
  }'
```

### Example 2: Restricted Thread Policy

```bash
curl -X PUT http://localhost:8000/api/v1/config/tool-policy \
  -H "Content-Type: application/json" \
  -d '{
    "scope_type": "thread",
    "scope_id": "sensitive-thread-123",
    "mode": "allowlist",
    "tools": ["artifact_writer"]
  }'
```

### Example 3: Add Telegram Integration

```bash
curl -X POST http://localhost:8000/api/v1/config/integrations/telegram \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Production Bot",
    "token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
    "meta": {
      "environment": "production",
      "webhook_url": "https://api.example.com/telegram/webhook"
    }
  }'
```

### Example 4: Workspace-Level Policy

```bash
curl -X PUT http://localhost:8000/api/v1/config/tool-policy \
  -H "Content-Type: application/json" \
  -d '{
    "scope_type": "workspace",
    "scope_id": "engineering-workspace",
    "mode": "allowlist",
    "tools": [
      "postgres_query",
      "artifact_writer",
      "vector_search",
      "logger"
    ]
  }'
```

## Troubleshooting

### Tool Execution Denied

**Problem:** Tool execution fails with "Tool denied by policy"

**Solution:**
1. Check effective policy for the thread/workspace
2. Add tool to allowlist
3. Verify policy scope is correct

```bash
# Check current policy
curl http://localhost:8000/api/v1/config/tool-policy?scope_type=global

# Update policy to include tool
curl -X PUT http://localhost:8000/api/v1/config/tool-policy \
  -H "Content-Type: application/json" \
  -d '{
    "scope_type": "global",
    "mode": "allowlist",
    "tools": ["postgres_query", "artifact_writer", "your_tool_here"]
  }'
```

### Encryption Key Error

**Problem:** "ENCRYPTION_KEY environment variable not set"

**Solution:**
1. Generate encryption key
2. Add to `.env` file
3. Restart services

```bash
# Generate key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env
echo "ENCRYPTION_KEY=your-key-here" >> .env

# Restart
docker compose restart gateway worker
```

### Policy Not Taking Effect

**Problem:** Policy changes don't seem to apply

**Solution:**
1. Policies are loaded when ToolExecutor is initialized
2. Restart the worker to pick up new policies
3. Check policy hierarchy (thread > workspace > global)

```bash
docker compose restart worker
```

## Database Schema

### integration_credentials

```sql
CREATE TABLE integration_credentials (
    id VARCHAR(255) PRIMARY KEY,
    integration_type VARCHAR(50) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    ciphertext TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'valid',
    meta JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### tool_policies

```sql
CREATE TABLE tool_policies (
    id VARCHAR(255) PRIMARY KEY,
    scope_type VARCHAR(50) NOT NULL,
    scope_id VARCHAR(255),
    mode VARCHAR(50) DEFAULT 'allowlist',
    tools JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(scope_type, scope_id)
);
```

## Next Steps

1. Set up global tool policy for your environment
2. Add integration credentials for external services
3. Configure workspace-specific policies as needed
4. Monitor policy violations in logs
5. Rotate credentials regularly

## Support

For issues or questions:
- Check logs: `docker compose logs worker --tail 50`
- Verify policy: `GET /api/v1/config/tool-policy`
- Review [LOVABLE_INTEGRATION.md](./LOVABLE_INTEGRATION.md) for API usage
