# Nanobot API Examples

This directory contains working code examples for integrating with the nanobot backend API.

## Quick Start

1. Update the API configuration in each file:
```javascript
const API_BASE = 'http://localhost:8000/api/v1';
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer your-token-here'
};
```

2. Run any example:
```bash
node basic-conversation.js
```

## Examples

### 1. basic-conversation.js

**Purpose:** Demonstrates the simplest conversation flow.

**What it does:**
- Creates a thread
- Sends a user message
- Polls until the run completes
- Returns the response

**Use this when:** You want a simple request-response conversation.

**Run:**
```bash
node basic-conversation.js
```

### 2. approval-flow.js

**Purpose:** Demonstrates the approval workflow for strategy synthesis.

**What it does:**
- Creates a thread
- Starts a run that requires approval
- Waits for approval state
- Shows approval UI (callback)
- Submits approval/rejection
- Returns the final artifact

**Use this when:** You need human-in-the-loop approval for generated content.

**Run:**
```bash
node approval-flow.js
```

### 3. knowledge-search.js

**Purpose:** Demonstrates document upload and knowledge-based search.

**What it does:**
- Uploads a document to the knowledge base
- Waits for chunking to complete
- Creates a conversation that uses the knowledge
- Checks if vector search was used

**Use this when:** You want to enable RAG (Retrieval-Augmented Generation) with custom documents.

**Run:**
```bash
node knowledge-search.js
```

### 4. error-handling.js

**Purpose:** Demonstrates robust error handling patterns.

**What it does:**
- Retry logic with exponential backoff
- Timeout handling
- Error response parsing
- Graceful degradation
- Recovery strategies

**Use this when:** You need production-ready error handling.

**Run:**
```bash
node error-handling.js
```

### 5. polling-utilities.js

**Purpose:** Reusable polling utilities and patterns.

**What it provides:**
- `pollUntil()` - Poll until specific status
- `pollUntilCompleted()` - Poll until completed
- `pollUntilApproval()` - Poll until approval needed
- `smartPoll()` - Automatic state handling with callbacks
- `pollMultiple()` - Batch poll multiple runs
- `ProgressTracker` - Track polling progress
- `adaptivePoll()` - Adaptive polling with backoff

**Use this when:** You want reusable polling logic for your application.

**Import:**
```javascript
const { pollUntilCompleted, ProgressTracker } = require('./polling-utilities');
```

## Common Patterns

### Pattern 1: Simple Conversation

```javascript
const { basicConversation } = require('./basic-conversation');

const result = await basicConversation('Help me with product strategy');
console.log(result.response);
```

### Pattern 2: Approval Flow

```javascript
const { approvalWorkflow } = require('./approval-flow');

const result = await approvalWorkflow(
  'Create a Q1 strategy',
  async (approvalData) => {
    // Show UI and get user decision
    return { approved: true, feedback: 'Looks good!' };
  }
);
```

### Pattern 3: Knowledge Search

```javascript
const { knowledgeWorkflow } = require('./knowledge-search');

const result = await knowledgeWorkflow(
  'Product Requirements',
  documentContent,
  'What are the key features?'
);
```

### Pattern 4: Error Handling

```javascript
const { robustConversation } = require('./error-handling');

const result = await robustConversation('Hello');
if (result.success) {
  console.log(result.response);
} else {
  console.error(result.error);
}
```

### Pattern 5: Custom Polling

```javascript
const { pollUntil, ProgressTracker } = require('./polling-utilities');

const tracker = new ProgressTracker(runId);
const state = await pollUntil(runId, 'completed', {
  interval: 1000,
  timeout: 60000,
  onProgress: (progress) => {
    tracker.update(progress.status);
    tracker.log();
  }
});
```

## Integration Tips

### 1. Environment Variables

Create a `.env` file:
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_API_TOKEN=your-token-here
```

Use in code:
```javascript
const API_BASE = process.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const API_TOKEN = process.env.VITE_API_TOKEN || 'your-token-here';
```

### 2. TypeScript Support

Add type definitions:
```typescript
interface RunState {
  run_id: string;
  status: 'queued' | 'running' | 'waiting_approval' | 'completed' | 'failed';
  state: any;
  error?: string;
  approval_request?: any;
}

interface Artifact {
  id: string;
  run_id: string;
  artifact_type: string;
  content: string;
  meta: any;
  created_at: string;
}
```

### 3. React Integration

```typescript
import { useState, useEffect } from 'react';
import { basicConversation } from './examples/basic-conversation';

function ChatComponent() {
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSend(message: string) {
    setLoading(true);
    try {
      const result = await basicConversation(message);
      setResponse(result.response);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {/* Your UI here */}
    </div>
  );
}
```

### 4. Vue Integration

```vue
<script setup>
import { ref } from 'vue';
import { basicConversation } from './examples/basic-conversation';

const response = ref('');
const loading = ref(false);

async function handleSend(message) {
  loading.value = true;
  try {
    const result = await basicConversation(message);
    response.value = result.response;
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
}
</script>
```

## Testing

### Test with cURL

```bash
# Create thread
curl -X POST http://localhost:8000/api/v1/threads \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{"meta": {"user_id": "test"}}'

# Create run
curl -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "thread_id": "thread-id-here",
    "graph_name": "conversation_router",
    "meta": {"messages": [{"role": "user", "content": "Hello"}]}
  }'

# Get run state
curl http://localhost:8000/api/v1/runs/run-id-here/state \
  -H "Authorization: Bearer your-token"
```

### Test with Postman

Import the API collection:
1. Create a new collection
2. Add environment variables: `API_BASE`, `API_TOKEN`
3. Add requests for each endpoint
4. Use examples from this directory

## Troubleshooting

### Issue: Connection refused

**Solution:** Ensure the backend is running:
```bash
docker compose up -d
curl http://localhost:8000/health
```

### Issue: CORS errors

**Solution:** Check CORS configuration in `apps/gateway/src/gateway/main.py`

### Issue: Polling timeout

**Solution:** Increase timeout or check worker logs:
```bash
docker compose logs worker --tail 50
```

### Issue: No response from run

**Solution:** Check run state for errors:
```bash
curl http://localhost:8000/api/v1/runs/{run_id}/state
```

## Best Practices

1. **Always handle errors** - Use try/catch and check response status
2. **Use reasonable polling intervals** - 1-2 seconds is recommended
3. **Set timeouts** - Don't poll indefinitely
4. **Track request IDs** - For debugging and tracing
5. **Implement retry logic** - For transient failures
6. **Log important events** - For monitoring and debugging

## Next Steps

1. Read the [main integration guide](../LOVABLE_INTEGRATION.md)
2. Try the examples in this directory
3. Adapt the code for your use case
4. Check the [API documentation](../LOVABLE_INTEGRATION.md#api-endpoints)
5. Review [best practices](../LOVABLE_INTEGRATION.md#best-practices)

## Support

For issues or questions:
- Check the [troubleshooting guide](../LOVABLE_INTEGRATION.md#troubleshooting)
- Review worker logs: `docker compose logs worker`
- Check API health: `curl http://localhost:8000/health`
