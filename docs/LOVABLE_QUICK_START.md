# Lovable Quick Start Guide

Get your nanobot frontend up and running in Lovable in 30 minutes.

## Prerequisites

- Nanobot backend running at `http://localhost:8000`
- Lovable.dev account
- Basic understanding of React and TypeScript

## Step-by-Step Implementation

### Step 1: Initial Setup (5 minutes)

Copy this prompt into Lovable:

```
Create a React application with TypeScript and TailwindCSS that integrates with a nanobot backend API.

API Base URL: http://localhost:8000/api/v1

Create an API client utility with the following structure:

1. Create src/lib/api-client.ts with:
   - Base configuration using environment variables (VITE_API_BASE_URL, VITE_API_TOKEN)
   - Authorization header support (Bearer token)
   - Error handling with typed responses
   - Request/response interceptors for logging

2. Create src/types/api.ts with TypeScript interfaces for:
   - Thread: { id: string, meta?: Record<string, any>, created_at: string, updated_at: string }
   - Run: { id: string, thread_id: string, graph_name: string, status: string, meta?: Record<string, any>, error?: string, created_at: string, updated_at: string }
   - Event: { id: string, thread_id: string, role: string, content?: string, meta?: Record<string, any>, created_at: string }
   - Artifact: { id: string, run_id: string, artifact_type: string, content: string, meta?: Record<string, any>, created_at: string }

3. Create .env.example with:
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   VITE_API_TOKEN=

4. Add CORS handling and proper error messages for network failures.

Use modern React patterns with hooks and proper TypeScript typing throughout.
```

**What you'll get**: Basic project structure with API client and TypeScript types.

### Step 2: Add Conversation UI (10 minutes)

Copy this prompt into Lovable:

```
Add conversation and run management with polling:

1. Create src/services/run-service.ts with:
   - createRun(threadId: string, graphName: string, messages: Array<{role: string, content: string}>): Promise<Run>
   - getRun(runId: string): Promise<Run>
   - getRunState(runId: string): Promise<{id: string, status: string, error?: string}>
   - pollRunUntilComplete(runId: string, onStatusChange?: (status: string) => void): Promise<Run>

2. Create src/components/ConversationPanel.tsx with:
   - Message input field
   - Send button
   - Message history display (user messages and bot responses)
   - Loading indicator while run is processing
   - Status display (queued, running, completed, failed)
   - Error messages if run fails

3. Create src/hooks/useConversation.ts:
   - Manage conversation state (messages array)
   - Send message function that creates run and polls for completion
   - Loading and error states
   - Automatic artifact retrieval when run completes

4. Implement polling logic:
   - Poll every 1 second
   - Maximum 60 attempts (60 seconds timeout)
   - Show status updates to user
   - Handle timeout gracefully

5. Style the conversation UI:
   - Chat-like interface with message bubbles
   - User messages on right (blue), bot on left (gray)
   - Smooth animations for new messages
   - Loading spinner during processing
   - Timestamp for each message

Also create a thread automatically on first message.
```

**What you'll get**: Working chat interface with message sending and response polling.

### Step 3: Add Approval Workflow (5 minutes)

Copy this prompt into Lovable:

```
Add approval workflow for runs that require user approval:

1. Create src/services/approval-service.ts with:
   - approveRun(runId: string, response?: string): Promise<void>
   - rejectRun(runId: string, reason?: string): Promise<void>

2. Create src/components/ApprovalDialog.tsx with:
   - Modal/dialog that appears when run status is "requires_approval"
   - Display approval request details
   - Text area for user response/reason
   - Approve and Reject buttons
   - Clear explanation of what's being approved

3. Update ConversationPanel:
   - Detect when run status is "requires_approval"
   - Show ApprovalDialog automatically
   - Continue polling after approval/rejection
   - Display approval status in message history

4. Style the approval UI:
   - Modal overlay with backdrop
   - Warning colors (yellow/orange) for approval requests
   - Clear action buttons (green for approve, red for reject)
   - Responsive modal design

Add visual indicators in the conversation when approval is needed.
```

**What you'll get**: Approval workflow handling for runs that need user confirmation.

### Step 4: Add Knowledge Management (5 minutes)

Copy this prompt into Lovable:

```
Add knowledge document management:

1. Create src/services/knowledge-service.ts with:
   - createDocument(title: string, content: string, source?: string): Promise<Document>
   - listDocuments(limit?: number): Promise<Document[]>

2. Create src/components/KnowledgeManager.tsx with:
   - Upload/create document form (title, content, source)
   - Document list with search
   - Document viewer showing content

3. Create src/components/DocumentUpload.tsx:
   - Text input for manual entry
   - URL input for web content
   - Upload button

4. Style with TailwindCSS:
   - Card-based document display
   - Upload area with dashed border
   - Proper spacing and grid layout

Create a separate tab for Knowledge Management.
```

**What you'll get**: Knowledge document upload and management interface.

### Step 5: Add Dashboard (5 minutes)

Copy this prompt into Lovable:

```
Create a dashboard with navigation:

1. Create src/components/Dashboard.tsx with:
   - Summary cards showing recent activity
   - Quick actions (new conversation, upload document)

2. Add navigation:
   - Sidebar or top nav with links to:
     * Conversations
     * Knowledge
     * Settings

3. Create src/components/Layout.tsx:
   - Main layout wrapper
   - Navigation component
   - Content area

4. Style with TailwindCSS:
   - Modern dashboard layout
   - Grid system for cards
   - Responsive design

Use Lucide React icons (Home, MessageSquare, Book, Settings).
```

**What you'll get**: Complete navigation and dashboard layout.

## Testing Your Implementation

### 1. Start Backend

```bash
cd /path/to/nanobot
docker compose up -d
```

### 2. Configure Frontend

Create `.env.local`:
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_API_TOKEN=
```

### 3. Test Conversation Flow

1. Open the app in browser
2. Type a message: "Hello, can you help me?"
3. Click Send
4. Watch the status change: queued → running → completed
5. See the bot's response appear

### 4. Test Approval Flow

1. Send a message that requires approval (if configured)
2. Approval dialog should appear
3. Click Approve or Reject
4. Conversation should continue

### 5. Test Knowledge Upload

1. Go to Knowledge tab
2. Enter title and content
3. Click Upload
4. Document should appear in list

## Common Issues & Solutions

### CORS Error
**Problem**: Browser shows CORS error  
**Solution**: Add your frontend URL to backend CORS_ALLOW_ORIGINS
```bash
# In backend .env
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 401 Unauthorized
**Problem**: All API calls return 401  
**Solution**: Check AUTH_BEARER_TOKEN in backend .env
```bash
# In backend .env - leave empty for development
AUTH_BEARER_TOKEN=
```

### Polling Timeout
**Problem**: Run never completes  
**Solution**: Check backend logs for errors
```bash
docker compose logs -f worker runtime
```

### No Response from Bot
**Problem**: Run completes but no message appears  
**Solution**: Check if artifacts are being created
```bash
# Test with curl
curl http://localhost:8000/api/v1/runs/{run_id}/artifacts
```

## Next Steps

After basic implementation:

1. **Add More Features**: Use remaining prompts from the full guide
2. **Customize Styling**: Adjust colors and layout to match your brand
3. **Add Error Handling**: Implement comprehensive error states
4. **Optimize Performance**: Add caching and request deduplication
5. **Deploy**: Build and deploy to production

## Full Feature List

For complete implementation with all features, see:
- `/docs/lovable-prompts-for-endpoints-0f5f1e.md` - All 15 prompts
- `/docs/LOVABLE_INTEGRATION.md` - Detailed API documentation

## Support

If you encounter issues:
1. Check browser console for errors
2. Review backend logs: `docker compose logs -f`
3. Test endpoints with curl
4. Verify environment variables
5. Ask Lovable to fix specific errors with detailed messages

## Estimated Timeline

- **Minimal viable product**: 30 minutes (Steps 1-3)
- **Full featured app**: 2-3 hours (All 15 prompts)
- **Production ready**: 4-6 hours (With testing and optimization)

Start with the minimal version and add features incrementally!
