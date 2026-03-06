# Lovable Integration Guide

Complete guide for integrating the Lovable frontend with the nanobot backend API.

## Quick Start (5 Minutes)

Get up and running with a basic conversation in 5 minutes.

### 1. Configure API

```javascript
const API_BASE = 'http://localhost:8000/api/v1';
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer your-token-here'
};
```

### 2. Create Your First Conversation

```javascript
// Create a thread
const thread = await fetch(`${API_BASE}/threads`, {
  method: 'POST',
  headers,
  body: JSON.stringify({ meta: { user_id: 'user123' } })
}).then(r => r.json());

console.log('Thread created:', thread.id);

// Create a run
const run = await fetch(`${API_BASE}/runs`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    thread_id: thread.id,
    graph_name: 'conversation_router',
    meta: {
      messages: [{ role: 'user', content: 'Hello, I need help with my product strategy' }]
    }
  })
}).then(r => r.json());

console.log('Run created:', run.id);

// Poll for completion
let status = 'queued';
while (status !== 'completed' && status !== 'failed') {
  await new Promise(r => setTimeout(r, 1000)); // Wait 1 second
  
  const state = await fetch(`${API_BASE}/runs/${run.id}/state`, { headers })
    .then(r => r.json());
  
  status = state.status;
  console.log('Status:', status);
}

console.log('Run completed!');
```

---

## Table of Contents

1. [Authentication](#authentication)
2. [Core Workflows](#core-workflows)
3. [API Endpoints](#api-endpoints)
4. [CORS Configuration](#cors-configuration)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Authentication

### Header Format

All API requests require an `Authorization` header:

```javascript
headers: {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer your-token-here'
}
```

### Environment Variables

```javascript
// .env.local
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_API_TOKEN=your-token-here
```

### Usage in Code

```javascript
const apiClient = {
  baseUrl: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${import.meta.env.VITE_API_TOKEN}`
  }
};
```

---

## Core Workflows

### Workflow 1: Basic Conversation

**Flow:** Create thread → Send message → Create run → Poll status → Get response

```javascript
async function basicConversation(userMessage) {
  // 1. Create thread
  const thread = await fetch(`${API_BASE}/threads`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ 
      meta: { 
        user_id: 'user123',
        session_id: Date.now().toString()
      } 
    })
  }).then(r => r.json());

  // 2. Create run with user message
  const run = await fetch(`${API_BASE}/runs`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      thread_id: thread.id,
      graph_name: 'conversation_router',
      meta: {
        messages: [
          { role: 'user', content: userMessage }
        ]
      }
    })
  }).then(r => r.json());

  // 3. Poll until completed
  let state;
  do {
    await new Promise(r => setTimeout(r, 1000));
    state = await fetch(`${API_BASE}/runs/${run.id}/state`, { headers })
      .then(r => r.json());
  } while (state.status === 'queued' || state.status === 'running');

  // 4. Check for errors
  if (state.status === 'failed') {
    throw new Error(state.error || 'Run failed');
  }

  // 5. Get artifacts (response)
  const artifacts = await fetch(`${API_BASE}/runs/${run.id}/artifacts`, { headers })
    .then(r => r.json());

  return {
    thread_id: thread.id,
    run_id: run.id,
    response: artifacts[0]?.content || 'No response',
    artifacts
  };
}

// Usage
const result = await basicConversation('Help me create a product strategy');
console.log(result.response);
```

### Workflow 2: Approval Flow

**Flow:** Create thread → Create run → Wait for approval → Show UI → Approve → Get artifact

```javascript
async function approvalWorkflow(userRequest) {
  // 1. Create thread
  const thread = await fetch(`${API_BASE}/threads`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ meta: { user_id: 'user123' } })
  }).then(r => r.json());

  // 2. Create run with strategy_synthesis graph (requires approval)
  const run = await fetch(`${API_BASE}/runs`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      thread_id: thread.id,
      graph_name: 'strategy_synthesis',
      meta: {
        messages: [
          { role: 'user', content: userRequest }
        ]
      }
    })
  }).then(r => r.json());

  // 3. Poll until waiting_approval
  let state;
  do {
    await new Promise(r => setTimeout(r, 1000));
    state = await fetch(`${API_BASE}/runs/${run.id}/state`, { headers })
      .then(r => r.json());
  } while (state.status !== 'waiting_approval' && 
           state.status !== 'completed' && 
           state.status !== 'failed');

  // 4. If waiting for approval, show UI
  if (state.status === 'waiting_approval') {
    const approvalRequest = state.approval_request;
    
    // Show approval UI to user (implement your own UI)
    const userApproved = await showApprovalUI({
      title: 'Strategy Ready for Review',
      content: approvalRequest.payload?.strategy || 'Review the strategy',
      options: ['Approve', 'Reject']
    });

    // 5. Submit approval or rejection
    if (userApproved) {
      await fetch(`${API_BASE}/runs/${run.id}/approve`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          response: { 
            approved: true,
            feedback: 'Looks good!'
          }
        })
      });
    } else {
      await fetch(`${API_BASE}/runs/${run.id}/reject`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          reason: 'Need changes'
        })
      });
      return { approved: false };
    }

    // 6. Poll until completed
    do {
      await new Promise(r => setTimeout(r, 1000));
      state = await fetch(`${API_BASE}/runs/${run.id}/state`, { headers })
        .then(r => r.json());
    } while (state.status === 'running');
  }

  // 7. Get final artifact
  const artifacts = await fetch(`${API_BASE}/runs/${run.id}/artifacts`, { headers })
    .then(r => r.json());

  return {
    approved: true,
    artifact: artifacts[0],
    run_id: run.id
  };
}

// Usage
const result = await approvalWorkflow('Create a Q1 2026 product strategy');
if (result.approved) {
  console.log('Strategy:', result.artifact.content);
}
```

### Workflow 3: Knowledge Search

**Flow:** Upload document → Wait for processing → Search → Use in conversation

```javascript
async function knowledgeWorkflow(documentContent, searchQuery) {
  // 1. Upload document
  const doc = await fetch(`${API_BASE}/knowledge/documents`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      title: 'Product Requirements',
      content: documentContent,
      meta: { source: 'user_upload' }
    })
  }).then(r => r.json());

  console.log('Document uploaded:', doc.id);

  // 2. Wait for chunking to complete
  await new Promise(r => setTimeout(r, 5000)); // Wait 5 seconds

  // 3. Verify chunks were created
  const chunks = await fetch(`${API_BASE}/knowledge/documents/${doc.id}/chunks`, { headers })
    .then(r => r.json());

  console.log(`Document chunked into ${chunks.length} pieces`);

  // 4. Create conversation that uses knowledge
  const thread = await fetch(`${API_BASE}/threads`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ meta: { user_id: 'user123' } })
  }).then(r => r.json());

  const run = await fetch(`${API_BASE}/runs`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      thread_id: thread.id,
      graph_name: 'conversation_router',
      meta: {
        messages: [
          { role: 'user', content: searchQuery }
        ]
      }
    })
  }).then(r => r.json());

  // 5. Poll for completion
  let state;
  do {
    await new Promise(r => setTimeout(r, 1000));
    state = await fetch(`${API_BASE}/runs/${run.id}/state`, { headers })
      .then(r => r.json());
  } while (state.status === 'queued' || state.status === 'running');

  // 6. Get tool calls to see if knowledge was used
  const toolCalls = await fetch(`${API_BASE}/runs/${run.id}/tool-calls`, { headers })
    .then(r => r.json());

  const vectorSearches = toolCalls.filter(tc => tc.tool_name === 'vector_search');

  return {
    document_id: doc.id,
    chunks_created: chunks.length,
    knowledge_used: vectorSearches.length > 0,
    tool_calls: toolCalls
  };
}

// Usage
const result = await knowledgeWorkflow(
  'Long product requirements document...',
  'What are the key features in the requirements?'
);
console.log('Knowledge used:', result.knowledge_used);
```

---

## API Endpoints

### Threads

#### POST /api/v1/threads

Create a new conversation thread.

**Request:**
```json
{
  "meta": {
    "user_id": "user123",
    "session_id": "session456"
  }
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "meta": {
    "user_id": "user123",
    "session_id": "session456"
  },
  "created_at": "2026-03-05T22:00:00Z",
  "updated_at": "2026-03-05T22:00:00Z"
}
```

#### GET /api/v1/threads/{thread_id}

Get thread details.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "meta": { "user_id": "user123" },
  "created_at": "2026-03-05T22:00:00Z",
  "updated_at": "2026-03-05T22:00:00Z"
}
```

### Runs

#### POST /api/v1/runs

Create a new run (executes a graph).

**Request:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "graph_name": "conversation_router",
  "meta": {
    "messages": [
      { "role": "user", "content": "Hello!" }
    ]
  }
}
```

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "graph_name": "conversation_router",
  "status": "queued",
  "created_at": "2026-03-05T22:00:01Z",
  "updated_at": "2026-03-05T22:00:01Z"
}
```

#### GET /api/v1/runs/{run_id}/state

Get current run state and status.

**Response:**
```json
{
  "run_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "completed",
  "state": {
    "messages": [...],
    "intent": "strategy_request"
  },
  "error": null,
  "approval_request": null
}
```

**Status values:**
- `queued` - Waiting to be processed
- `running` - Currently executing
- `waiting_approval` - Paused for human approval
- `completed` - Successfully finished
- `failed` - Execution failed

### Approvals

#### POST /api/v1/runs/{run_id}/approve

Approve a run that's waiting for approval.

**Request:**
```json
{
  "response": {
    "approved": true,
    "feedback": "Looks good!"
  }
}
```

**Response:**
```json
{
  "status": "approved",
  "run_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

#### POST /api/v1/runs/{run_id}/reject

Reject a run that's waiting for approval.

**Request:**
```json
{
  "reason": "Need changes to the strategy"
}
```

**Response:**
```json
{
  "status": "rejected",
  "run_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

### Artifacts

#### GET /api/v1/runs/{run_id}/artifacts

Get all artifacts created by a run.

**Response:**
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "run_id": "660e8400-e29b-41d4-a716-446655440001",
    "artifact_type": "strategy_document",
    "content": "Q1 2026 Product Strategy...",
    "meta": { "version": "1.0" },
    "created_at": "2026-03-05T22:00:05Z"
  }
]
```

### Knowledge

#### POST /api/v1/knowledge/documents

Upload a document to the knowledge base.

**Request:**
```json
{
  "title": "Product Requirements",
  "content": "Long document content...",
  "meta": {
    "source": "user_upload",
    "category": "requirements"
  }
}
```

**Response:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "title": "Product Requirements",
  "content": "Long document content...",
  "meta": { "source": "user_upload" },
  "chunk_count": 0,
  "created_at": "2026-03-05T22:00:10Z",
  "updated_at": "2026-03-05T22:00:10Z"
}
```

#### GET /api/v1/knowledge/documents/{document_id}/chunks

Get all chunks for a document.

**Response:**
```json
[
  {
    "id": "990e8400-e29b-41d4-a716-446655440004",
    "document_id": "880e8400-e29b-41d4-a716-446655440003",
    "content": "First chunk of content...",
    "has_embedding": true,
    "meta": { "position": 0 },
    "created_at": "2026-03-05T22:00:15Z"
  }
]
```

### Tools

#### GET /api/v1/tools

List all available tools.

**Response:**
```json
[
  {
    "id": "tool-1",
    "name": "postgres_query",
    "description": "Execute read-only SQL queries",
    "schema": {...},
    "timeout_ms": 10000,
    "retries": 1,
    "permission_tag": "database"
  }
]
```

### Graphs

#### GET /api/v1/graphs

List all available graphs.

**Response:**
```json
[
  {
    "id": "graph-1",
    "name": "conversation_router",
    "description": "Routes conversations to appropriate strategy graphs",
    "config": { "timeout_ms": 60000 }
  }
]
```

---

## CORS Configuration

### Development Setup

The backend is configured to allow requests from Lovable domains:

```python
# Already configured in gateway/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.lovable.app",
        "https://*.lovable.dev",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Custom Domains

To add your custom domain:

1. Edit `apps/gateway/src/gateway/main.py`
2. Add your domain to `allow_origins` list
3. Rebuild and restart the gateway

```python
allow_origins=[
    "https://your-custom-domain.com",
    # ... existing origins
]
```

### Testing CORS

```javascript
// Test CORS from browser console
fetch('http://localhost:8000/api/v1/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

### Common Errors

**404 Not Found**
```json
{
  "detail": "Thread not found"
}
```

**400 Bad Request**
```json
{
  "detail": "Invalid graph_name"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

### Retry Strategy

```javascript
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Request failed');
      }
      
      return await response.json();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      // Exponential backoff
      await new Promise(r => setTimeout(r, Math.pow(2, i) * 1000));
    }
  }
}
```

### Error Handling Example

```javascript
async function safeCreateRun(threadId, graphName, meta) {
  try {
    const run = await fetch(`${API_BASE}/runs`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        thread_id: threadId,
        graph_name: graphName,
        meta
      })
    }).then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    });
    
    return { success: true, run };
  } catch (error) {
    console.error('Failed to create run:', error);
    return { 
      success: false, 
      error: error.message 
    };
  }
}
```

---

## Best Practices

### 1. Polling Intervals

**Recommended:** 1-2 seconds between polls

```javascript
// Good: 1 second interval
while (status !== 'completed') {
  await new Promise(r => setTimeout(r, 1000));
  status = await getRunStatus(runId);
}

// Bad: Too frequent
while (status !== 'completed') {
  await new Promise(r => setTimeout(r, 100)); // Too fast!
  status = await getRunStatus(runId);
}
```

### 2. Request IDs

Use request IDs for tracing:

```javascript
const requestId = crypto.randomUUID();
headers['X-Request-ID'] = requestId;
```

### 3. Idempotency

For events, use idempotency keys:

```javascript
const event = await fetch(`${API_BASE}/events`, {
  method: 'POST',
  headers: {
    ...headers,
    'Idempotency-Key': `event-${Date.now()}-${userId}`
  },
  body: JSON.stringify({...})
});
```

### 4. Timeout Handling

Set reasonable timeouts:

```javascript
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 30000); // 30 seconds

try {
  const response = await fetch(url, {
    ...options,
    signal: controller.signal
  });
  return await response.json();
} finally {
  clearTimeout(timeout);
}
```

### 5. State Management

Keep track of active runs:

```javascript
const activeRuns = new Map();

function trackRun(runId, metadata) {
  activeRuns.set(runId, {
    ...metadata,
    startedAt: Date.now()
  });
}

function cleanupRun(runId) {
  activeRuns.delete(runId);
}
```

---

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to API

**Solutions:**
1. Check API is running: `curl http://localhost:8000/health`
2. Verify CORS configuration
3. Check network/firewall settings
4. Ensure correct API base URL

### Authentication Errors

**Problem:** 401 Unauthorized

**Solutions:**
1. Verify Authorization header is set
2. Check token is valid
3. Ensure header format: `Bearer <token>`

### CORS Errors

**Problem:** CORS policy blocking requests

**Solutions:**
1. Check origin is in allowed list
2. Verify credentials setting
3. Check preflight OPTIONS requests
4. Add domain to CORS configuration

### Timeout Issues

**Problem:** Requests timing out

**Solutions:**
1. Increase timeout duration
2. Check backend is processing
3. Verify worker is running
4. Check database connectivity

### Polling Never Completes

**Problem:** Status stuck in 'running'

**Solutions:**
1. Check worker logs: `docker compose logs worker`
2. Verify run exists: `GET /api/v1/runs/{id}/state`
3. Check for errors in run state
4. Restart worker if needed

### Common Mistakes

**1. Not waiting for async processing**
```javascript
// Bad
const doc = await createDocument(content);
const chunks = await getChunks(doc.id); // Empty! Not processed yet

// Good
const doc = await createDocument(content);
await new Promise(r => setTimeout(r, 5000)); // Wait for processing
const chunks = await getChunks(doc.id);
```

**2. Polling too fast**
```javascript
// Bad
while (status !== 'completed') {
  status = await getStatus(); // No delay!
}

// Good
while (status !== 'completed') {
  await new Promise(r => setTimeout(r, 1000));
  status = await getStatus();
}
```

**3. Not handling errors**
```javascript
// Bad
const run = await fetch(url).then(r => r.json());

// Good
const response = await fetch(url);
if (!response.ok) {
  const error = await response.json();
  throw new Error(error.detail);
}
const run = await response.json();
```

---

## Complete Example: React Component

```typescript
import { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL;
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${import.meta.env.VITE_API_TOKEN}`
};

export function ChatComponent() {
  const [threadId, setThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>([]);
  const [loading, setLoading] = useState(false);

  // Initialize thread
  useEffect(() => {
    async function init() {
      const thread = await fetch(`${API_BASE}/threads`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ meta: { user_id: 'user123' } })
      }).then(r => r.json());
      
      setThreadId(thread.id);
    }
    init();
  }, []);

  async function sendMessage(content: string) {
    if (!threadId) return;
    
    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', content }]);

    try {
      // Create run
      const run = await fetch(`${API_BASE}/runs`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          thread_id: threadId,
          graph_name: 'conversation_router',
          meta: { messages: [{ role: 'user', content }] }
        })
      }).then(r => r.json());

      // Poll for completion
      let state;
      do {
        await new Promise(r => setTimeout(r, 1000));
        state = await fetch(`${API_BASE}/runs/${run.id}/state`, { headers })
          .then(r => r.json());
      } while (state.status === 'queued' || state.status === 'running');

      // Get response
      const artifacts = await fetch(`${API_BASE}/runs/${run.id}/artifacts`, { headers })
        .then(r => r.json());

      if (artifacts.length > 0) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: artifacts[0].content 
        }]);
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'error', 
        content: 'Failed to get response' 
      }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>
      
      <input
        type="text"
        disabled={loading || !threadId}
        onKeyPress={(e) => {
          if (e.key === 'Enter' && e.currentTarget.value) {
            sendMessage(e.currentTarget.value);
            e.currentTarget.value = '';
          }
        }}
        placeholder="Type a message..."
      />
    </div>
  );
}
```

---

## Next Steps

1. **Explore Examples**: Check `docs/examples/` for more code samples
2. **Test Integration**: Use the quick start guide to verify connectivity
3. **Build Your UI**: Implement approval flows and knowledge search
4. **Monitor**: Check run status and tool calls for debugging
5. **Optimize**: Adjust polling intervals and error handling

## Support

- **API Health**: `GET /health`
- **API Ready**: `GET /ready`
- **Available Tools**: `GET /api/v1/tools`
- **Available Graphs**: `GET /api/v1/graphs`

For issues, check the troubleshooting section or review worker logs:
```bash
docker compose logs worker --tail 50
```
