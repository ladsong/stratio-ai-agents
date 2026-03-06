# Lovable Integration: Conversation Memory & System Prompt Editor

## Overview

Add conversation memory and system prompt management to your Nanobot frontend. This allows users to:
- View and edit the AI's system prompt (personality/instructions)
- See conversation history and message counts
- Customize bot behavior per conversation thread

The backend is fully implemented and ready to use.

## Backend API Endpoints

### Get Thread (includes system prompt)

```http
GET /api/v1/threads/{thread_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "thread-uuid",
  "meta": {
    "system_prompt": "You are a helpful AI assistant...",
    "session_key": "telegram:12345"
  },
  "created_at": "2026-03-06T12:00:00Z",
  "updated_at": "2026-03-06T12:00:00Z"
}
```

### Update Thread System Prompt

```http
PATCH /api/v1/threads/{thread_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "system_prompt": "You are a helpful AI assistant with expertise in..."
}
```

**Response:** Same as GET (updated thread)

### Get Conversation History

```http
GET /api/v1/threads/{thread_id}/events?limit=50
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "id": "event-uuid",
    "thread_id": "thread-uuid",
    "role": "user",
    "content": "Hello!",
    "created_at": "2026-03-06T12:00:00Z"
  },
  {
    "id": "event-uuid-2",
    "thread_id": "thread-uuid",
    "role": "assistant",
    "content": "Hi! How can I help you?",
    "created_at": "2026-03-06T12:00:01Z"
  }
]
```

## UI Implementation Guide

### 1. Thread Settings Component

Create a modal or drawer component for thread settings:

```tsx
interface ThreadSettingsProps {
  threadId: string;
  onClose: () => void;
}

function ThreadSettings({ threadId, onClose }: ThreadSettingsProps) {
  const [systemPrompt, setSystemPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [messageCount, setMessageCount] = useState(0);

  // Load thread data on mount
  useEffect(() => {
    async function loadThread() {
      const response = await fetch(`/api/v1/threads/${threadId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const thread = await response.json();
      setSystemPrompt(thread.meta?.system_prompt || DEFAULT_PROMPT);
    }
    
    async function loadMessageCount() {
      const response = await fetch(`/api/v1/threads/${threadId}/events?limit=1000`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const events = await response.json();
      setMessageCount(events.length);
    }
    
    loadThread();
    loadMessageCount();
  }, [threadId]);

  async function handleSave() {
    setLoading(true);
    try {
      await fetch(`/api/v1/threads/${threadId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ system_prompt: systemPrompt })
      });
      toast.success('System prompt updated!');
      onClose();
    } catch (error) {
      toast.error('Failed to update system prompt');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Thread Settings</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          <div>
            <Label>System Prompt</Label>
            <Textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="Enter custom instructions for the AI..."
              rows={8}
              className="mt-2"
            />
            <p className="text-sm text-muted-foreground mt-1">
              {systemPrompt.length} / 2000 characters
            </p>
          </div>
          
          <div className="border-t pt-4">
            <h4 className="font-medium mb-2">Conversation Stats</h4>
            <p className="text-sm text-muted-foreground">
              • {messageCount} messages in history
            </p>
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading}>
            {loading ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

### 2. Add Settings Button to Thread List

Add a settings icon to each conversation thread:

```tsx
function ThreadListItem({ thread }: { thread: Thread }) {
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="flex items-center justify-between p-3 hover:bg-accent rounded-lg">
      <div className="flex-1">
        <h3 className="font-medium">{thread.name || 'Conversation'}</h3>
        <p className="text-sm text-muted-foreground">
          Last active: {formatDate(thread.updated_at)}
        </p>
      </div>
      
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setShowSettings(true)}
      >
        <Settings className="h-4 w-4" />
      </Button>
      
      {showSettings && (
        <ThreadSettings
          threadId={thread.id}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}
```

### 3. Default System Prompt

Use this as the default when no custom prompt is set:

```typescript
const DEFAULT_SYSTEM_PROMPT = `You are a helpful AI assistant. Be concise, accurate, and friendly.

Key guidelines:
- Provide clear, direct answers
- Ask clarifying questions when needed
- Remember context from our conversation
- Be proactive in offering relevant suggestions`;
```

## UI Layout Example

```
┌─────────────────────────────────────────┐
│ Thread Settings                      ✕  │
├─────────────────────────────────────────┤
│                                         │
│ System Prompt                           │
│ ┌─────────────────────────────────────┐ │
│ │ You are a helpful AI assistant.     │ │
│ │ Be concise, accurate, and friendly. │ │
│ │                                     │ │
│ │ Key guidelines:                     │ │
│ │ - Provide clear, direct answers     │ │
│ │ - Ask clarifying questions when     │ │
│ │   needed                            │ │
│ │ - Remember context from our         │ │
│ │   conversation                      │ │
│ └─────────────────────────────────────┘ │
│ 245 / 2000 characters                   │
│                                         │
│ ─────────────────────────────────────── │
│                                         │
│ Conversation Stats                      │
│ • 24 messages in history                │
│                                         │
│                    [Cancel] [Save]      │
└─────────────────────────────────────────┘
```

## Features Implemented in Backend

### ✅ Conversation Memory
- Bot now remembers last 20 messages from conversation history
- Messages are stored as events in the database
- Context is automatically loaded before each AI response
- Sliding window keeps token usage efficient (~2-5K tokens)

### ✅ System Prompt Support
- Each thread can have a custom system prompt
- Stored in `thread.meta.system_prompt`
- Falls back to default prompt if not set
- Passed to LLM with every request

### ✅ Context Window Management
- Automatically limits history to last 20 messages
- Prevents token bloat while maintaining context
- System prompt + history stays under 8K tokens

## Token Efficiency

**Before (no memory):**
- ~50 tokens per request
- No conversation context

**After (with memory):**
- ~2-5K tokens per request
- Full conversation context
- Still very efficient compared to unlimited history

## Testing Checklist

- [ ] Can open thread settings modal
- [ ] System prompt loads from thread.meta
- [ ] Can edit system prompt in textarea
- [ ] Character count updates correctly
- [ ] Save button shows loading state
- [ ] Success toast appears on save
- [ ] Error toast appears on failure
- [ ] Changes persist after page refresh
- [ ] Message count displays correctly
- [ ] Mobile responsive design
- [ ] Bot remembers conversation context
- [ ] Custom system prompt affects bot behavior

## Example Usage

1. **User opens thread settings**
2. **Edits system prompt:**
   ```
   You are a Python programming expert. Provide code examples
   and explain concepts clearly. Always include error handling.
   ```
3. **Saves changes**
4. **Bot now responds with Python expertise and includes error handling**
5. **Bot remembers previous messages in the conversation**

## Migration Notes

- No database migration needed (meta is already JSONB)
- Existing threads will use default system prompt
- Events table already exists, just needs to be populated
- Backward compatible with threads that have no events yet
- Works immediately after deployment

## Support

For questions or issues:
- Check backend logs: `docker compose logs runtime --tail 50`
- Verify API endpoints: `curl http://localhost:8000/api/v1/threads/{id}`
- Test system prompt: Send message and check if bot behavior changes
