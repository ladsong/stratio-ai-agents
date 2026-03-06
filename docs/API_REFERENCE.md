# Nanobot API Reference

Complete reference for all nanobot backend API endpoints.

**Base URL**: `http://localhost:8000/api/v1`

**Authentication**: Bearer token in Authorization header (optional in development)

---

## Health & Status

### GET /health
Health check endpoint.

**Response**:
```json
{
  "status": "ok"
}
```

### GET /ready
Readiness check with database and Redis connectivity.

**Response**:
```json
{
  "status": "ready"
}
```

---

## Threads

### POST /api/v1/threads
Create a new conversation thread.

**Request**:
```json
{
  "id": "optional-custom-id",
  "meta": {
    "user_id": "user123",
    "source": "web"
  }
}
```

**Response**:
```json
{
  "id": "thread_abc123",
  "meta": {
    "user_id": "user123",
    "source": "web"
  },
  "created_at": "2026-03-06T00:00:00Z",
  "updated_at": "2026-03-06T00:00:00Z"
}
```

### GET /api/v1/threads/{thread_id}
Get thread details.

**Response**:
```json
{
  "id": "thread_abc123",
  "meta": {},
  "created_at": "2026-03-06T00:00:00Z",
  "updated_at": "2026-03-06T00:00:00Z"
}
```

---

## Events

### POST /api/v1/threads/{thread_id}/events
Create an event in a thread.

**Request**:
```json
{
  "role": "user",
  "content": "Hello, I need help",
  "meta": {
    "source": "web"
  }
}
```

**Response**:
```json
{
  "id": "event_xyz789",
  "thread_id": "thread_abc123",
  "role": "user",
  "content": "Hello, I need help",
  "meta": {
    "source": "web"
  },
  "created_at": "2026-03-06T00:00:00Z"
}
```

### GET /api/v1/threads/{thread_id}/events
List events in a thread.

**Query Parameters**:
- `limit` (optional): Maximum number of events (default: 100)
- `offset` (optional): Offset for pagination (default: 0)

**Response**:
```json
[
  {
    "id": "event_xyz789",
    "thread_id": "thread_abc123",
    "role": "user",
    "content": "Hello, I need help",
    "meta": {},
    "created_at": "2026-03-06T00:00:00Z"
  }
]
```

---

## Runs

### POST /api/v1/runs
Create and execute a workflow run.

**Request**:
```json
{
  "thread_id": "thread_abc123",
  "graph_name": "conversation_router",
  "meta": {
    "messages": [
      {
        "role": "user",
        "content": "What's the weather like?"
      }
    ]
  }
}
```

**Response**:
```json
{
  "id": "run_def456",
  "thread_id": "thread_abc123",
  "graph_name": "conversation_router",
  "status": "queued",
  "meta": {
    "messages": [...]
  },
  "error": null,
  "created_at": "2026-03-06T00:00:00Z",
  "updated_at": "2026-03-06T00:00:00Z"
}
```

**Status Values**:
- `queued` - Run is queued for execution
- `running` - Run is currently executing
- `requires_approval` - Run needs user approval to continue
- `completed` - Run finished successfully
- `failed` - Run failed with error

### GET /api/v1/runs/{run_id}
Get run details.

**Response**:
```json
{
  "id": "run_def456",
  "thread_id": "thread_abc123",
  "graph_name": "conversation_router",
  "status": "completed",
  "meta": {},
  "error": null,
  "created_at": "2026-03-06T00:00:00Z",
  "updated_at": "2026-03-06T00:00:00Z"
}
```

### GET /api/v1/runs/{run_id}/state
Get run state (lightweight status check).

**Response**:
```json
{
  "id": "run_def456",
  "status": "completed",
  "error": null
}
```

### POST /api/v1/runs/{run_id}/approve
Approve a run that requires approval.

**Request**:
```json
{
  "response": "Yes, proceed with the action"
}
```

**Response**:
```json
{
  "status": "approved",
  "run_id": "run_def456"
}
```

### POST /api/v1/runs/{run_id}/reject
Reject a run that requires approval.

**Request**:
```json
{
  "reason": "Not authorized for this action"
}
```

**Response**:
```json
{
  "status": "rejected",
  "run_id": "run_def456"
}
```

### POST /api/v1/runs/{run_id}/resume
Resume an interrupted run.

**Request**:
```json
{
  "response": "Continue with updated parameters"
}
```

**Response**:
```json
{
  "status": "resumed",
  "run_id": "run_def456"
}
```

---

## Artifacts

### GET /api/v1/artifacts/{artifact_id}
Get artifact details.

**Response**:
```json
{
  "id": "artifact_ghi789",
  "run_id": "run_def456",
  "artifact_type": "text",
  "content": "Here's the response to your question...",
  "meta": {},
  "created_at": "2026-03-06T00:00:00Z"
}
```

**Note**: To get all artifacts for a run, use `GET /api/v1/runs/{run_id}` and check the run's metadata or use tool calls endpoint.

---

## Tools & Graphs

### GET /api/v1/tools
List all available tools.

**Response**:
```json
[
  {
    "id": "tool_123",
    "name": "web_search",
    "description": "Search the web for information",
    "schema": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string"
        }
      }
    },
    "timeout_ms": 30000,
    "retries": 2,
    "permission_tag": "network"
  }
]
```

**Permission Tags**:
- `safe` - Safe tools (read-only operations)
- `network` - Network access required
- `admin` - Administrative/dangerous operations

### GET /api/v1/graphs
List all available workflow graphs.

**Response**:
```json
[
  {
    "id": "graph_456",
    "name": "conversation_router",
    "description": "Routes conversations to appropriate handlers"
  }
]
```

---

## Tool Calls

### GET /api/v1/runs/{run_id}/tool-calls
List tool calls made during a run.

**Query Parameters**:
- `limit` (optional): Maximum number of tool calls (default: 100)

**Response**:
```json
[
  {
    "id": "toolcall_abc",
    "run_id": "run_def456",
    "tool_name": "web_search",
    "inputs": {
      "query": "weather in Tokyo"
    },
    "output": "Temperature: 15°C, Conditions: Partly cloudy",
    "status": "success",
    "error": null,
    "created_at": "2026-03-06T00:00:00Z",
    "updated_at": "2026-03-06T00:00:00Z"
  }
]
```

### GET /api/v1/tool-calls/{tool_call_id}
Get specific tool call details.

**Response**:
```json
{
  "id": "toolcall_abc",
  "run_id": "run_def456",
  "tool_name": "web_search",
  "inputs": {
    "query": "weather in Tokyo"
  },
  "output": "Temperature: 15°C, Conditions: Partly cloudy",
  "status": "success",
  "error": null,
  "created_at": "2026-03-06T00:00:00Z",
  "updated_at": "2026-03-06T00:00:00Z"
}
```

---

## Knowledge Management

### POST /api/v1/knowledge/documents
Create a knowledge document.

**Request**:
```json
{
  "title": "Product Documentation",
  "content": "This is the full text content of the document...",
  "source": "https://example.com/docs",
  "meta": {
    "author": "John Doe",
    "category": "documentation"
  }
}
```

**Response**:
```json
{
  "id": "doc_xyz123",
  "title": "Product Documentation",
  "content": "This is the full text content...",
  "source": "https://example.com/docs",
  "chunk_count": 5,
  "meta": {
    "author": "John Doe",
    "category": "documentation"
  },
  "created_at": "2026-03-06T00:00:00Z"
}
```

### GET /api/v1/knowledge/documents
List knowledge documents.

**Query Parameters**:
- `limit` (optional): Maximum number of documents (default: 100)
- `offset` (optional): Offset for pagination (default: 0)

**Response**:
```json
[
  {
    "id": "doc_xyz123",
    "title": "Product Documentation",
    "content": "This is the full text...",
    "source": "https://example.com/docs",
    "chunk_count": 5,
    "meta": {},
    "created_at": "2026-03-06T00:00:00Z"
  }
]
```

### GET /api/v1/knowledge/documents/{document_id}
Get specific document.

**Response**:
```json
{
  "id": "doc_xyz123",
  "title": "Product Documentation",
  "content": "This is the full text content...",
  "source": "https://example.com/docs",
  "chunk_count": 5,
  "meta": {},
  "created_at": "2026-03-06T00:00:00Z"
}
```

### GET /api/v1/knowledge/documents/{document_id}/chunks
Get document chunks (for vector search).

**Query Parameters**:
- `limit` (optional): Maximum number of chunks (default: 100)

**Response**:
```json
[
  {
    "id": "chunk_abc",
    "document_id": "doc_xyz123",
    "content": "This is chunk 1 of the document...",
    "chunk_index": 0,
    "meta": {
      "tokens": 150
    }
  }
]
```

---

## Integration Credentials

### GET /api/v1/config/integrations
List integration credentials.

**Query Parameters**:
- `integration_type` (optional): Filter by type (telegram, slack, github, etc.)

**Response**:
```json
[
  {
    "id": "cred_abc123",
    "integration_type": "telegram",
    "display_name": "Main Telegram Bot",
    "status": "valid",
    "meta": {
      "bot_username": "@mybot"
    },
    "created_at": "2026-03-06T00:00:00Z",
    "updated_at": "2026-03-06T00:00:00Z"
  }
]
```

**Note**: Token/secret is never returned in responses for security.

### POST /api/v1/config/integrations/{integration_type}
Create integration credential.

**Request**:
```json
{
  "display_name": "Main Telegram Bot",
  "token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
  "meta": {
    "bot_username": "@mybot"
  }
}
```

**Response**:
```json
{
  "id": "cred_abc123",
  "integration_type": "telegram",
  "display_name": "Main Telegram Bot",
  "status": "valid",
  "meta": {
    "bot_username": "@mybot"
  },
  "created_at": "2026-03-06T00:00:00Z",
  "updated_at": "2026-03-06T00:00:00Z"
}
```

### POST /api/v1/config/integrations/{credential_id}/rotate
Rotate integration credential.

**Request**:
```json
{
  "new_token": "654321:XYZ-ABC9876lmno-abc12W3v4u567zw88"
}
```

**Response**:
```json
{
  "id": "cred_abc123",
  "integration_type": "telegram",
  "display_name": "Main Telegram Bot",
  "status": "valid",
  "meta": {},
  "created_at": "2026-03-06T00:00:00Z",
  "updated_at": "2026-03-06T00:00:01Z"
}
```

### DELETE /api/v1/config/integrations/{credential_id}
Delete integration credential.

**Response**:
```json
{
  "status": "deleted",
  "credential_id": "cred_abc123"
}
```

---

## Tool Policies

### GET /api/v1/config/tool-policy
Get tool policy for a scope.

**Query Parameters**:
- `scope_type` (required): global, workspace, or thread
- `scope_id` (optional): Required for workspace/thread scopes

**Response**:
```json
{
  "id": "policy_xyz",
  "scope_type": "global",
  "scope_id": null,
  "mode": "allowlist",
  "tools": ["web_search", "read_file", "list_dir"],
  "created_at": "2026-03-06T00:00:00Z",
  "updated_at": "2026-03-06T00:00:00Z"
}
```

**Scope Types**:
- `global` - Applies to all threads
- `workspace` - Applies to specific workspace
- `thread` - Applies to specific thread

**Modes**:
- `allowlist` - Only listed tools are allowed
- `denylist` - All tools except listed are allowed

### PUT /api/v1/config/tool-policy
Create or update tool policy.

**Request**:
```json
{
  "scope_type": "global",
  "scope_id": null,
  "mode": "allowlist",
  "tools": ["web_search", "read_file", "list_dir"]
}
```

**Response**:
```json
{
  "id": "policy_xyz",
  "scope_type": "global",
  "scope_id": null,
  "mode": "allowlist",
  "tools": ["web_search", "read_file", "list_dir"],
  "created_at": "2026-03-06T00:00:00Z",
  "updated_at": "2026-03-06T00:00:00Z"
}
```

### DELETE /api/v1/config/tool-policy
Delete tool policy.

**Query Parameters**:
- `scope_type` (required): global, workspace, or thread
- `scope_id` (optional): Required for workspace/thread scopes

**Response**:
```json
{
  "status": "deleted"
}
```

---

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or missing authentication token"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 409 Conflict
```json
{
  "detail": "Resource already exists or conflict detected"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Common Patterns

### Polling for Run Completion

```javascript
async function pollRunUntilComplete(runId) {
  const maxAttempts = 60;
  
  for (let i = 0; i < maxAttempts; i++) {
    const state = await fetch(`${API_BASE}/runs/${runId}/state`, { headers })
      .then(r => r.json());
    
    if (state.status === 'completed' || state.status === 'failed') {
      return state;
    }
    
    if (state.status === 'requires_approval') {
      // Handle approval
      return state;
    }
    
    await new Promise(r => setTimeout(r, 1000)); // Wait 1 second
  }
  
  throw new Error('Run timeout');
}
```

### Creating a Conversation

```javascript
// 1. Create thread
const thread = await fetch(`${API_BASE}/threads`, {
  method: 'POST',
  headers,
  body: JSON.stringify({ meta: { user_id: 'user123' } })
}).then(r => r.json());

// 2. Create run
const run = await fetch(`${API_BASE}/runs`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    thread_id: thread.id,
    graph_name: 'conversation_router',
    meta: {
      messages: [{ role: 'user', content: 'Hello!' }]
    }
  })
}).then(r => r.json());

// 3. Poll for completion
const finalState = await pollRunUntilComplete(run.id);

// 4. Get artifacts (response)
const artifacts = await fetch(`${API_BASE}/runs/${run.id}/artifacts`, { headers })
  .then(r => r.json());
```

### Handling Approvals

```javascript
// Check if approval needed
if (state.status === 'requires_approval') {
  // Show approval dialog to user
  const userApproved = await showApprovalDialog();
  
  if (userApproved) {
    await fetch(`${API_BASE}/runs/${run.id}/approve`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ response: 'Approved by user' })
    });
  } else {
    await fetch(`${API_BASE}/runs/${run.id}/reject`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ reason: 'User rejected' })
    });
  }
  
  // Continue polling
  const finalState = await pollRunUntilComplete(run.id);
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. In production, consider:
- Maximum 100 requests per minute per IP
- Maximum 10 concurrent runs per thread
- Maximum document size: 10MB

---

## Versioning

Current API version: `v1`

All endpoints are prefixed with `/api/v1/`

Future versions will use `/api/v2/`, etc.

---

## Support

For issues or questions:
- Check backend logs: `docker compose logs -f gateway`
- Review this documentation
- Test with curl or Postman
- Check CORS configuration
- Verify authentication headers
