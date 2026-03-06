# Lovable Frontend: User Management System

Build a comprehensive user management interface for the Nanobot system with user profiles, contact management, and unified conversation views across all communication channels.

## Overview

The Nanobot backend now supports user-centric conversations where each person has a unified identity across multiple channels (Telegram, email, WhatsApp, etc.). Build a React frontend with TailwindCSS and shadcn/ui to manage users and view their conversations.

## API Endpoints Available

### User Management
```typescript
// Get all users
GET /api/v1/users
Response: UserResponse[]

interface UserResponse {
  id: string;
  name: string;
  role: "admin" | "user";
  system_prompt: string | null;
  meta: Record<string, any> | null;
  contacts: UserContactResponse[];
  created_at: string;
  updated_at: string;
}

interface UserContactResponse {
  id: string;
  channel: string;  // "telegram", "email", "whatsapp", etc.
  contact_id: string;
  meta: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

// Get specific user
GET /api/v1/users/{user_id}
Response: UserResponse

// Create user
POST /api/v1/users
Body: {
  name: string;
  role?: "admin" | "user";  // default: "user"
  system_prompt?: string;
  meta?: Record<string, any>;
}
Response: UserResponse

// Update user
PATCH /api/v1/users/{user_id}
Body: {
  name?: string;
  role?: "admin" | "user";
  system_prompt?: string;
  meta?: Record<string, any>;
}
Response: UserResponse

// Delete user
DELETE /api/v1/users/{user_id}
Response: { status: "deleted", id: string }

// Add contact to user
POST /api/v1/users/{user_id}/contacts
Body: {
  channel: string;
  contact_id: string;
  meta?: Record<string, any>;
}
Response: UserContactResponse

// Lookup user by contact
GET /api/v1/users/contacts/{channel}/{contact_id}
Response: UserResponse
```

### Conversation Data
```typescript
// Get thread events (conversation history)
GET /api/v1/threads/{thread_id}/events?limit=100
Response: EventResponse[]

interface EventResponse {
  id: string;
  thread_id: string;
  role: "user" | "assistant";
  content: string | null;
  meta: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

// Get all threads (to find user's threads)
GET /api/v1/threads
Response: ThreadResponse[]

interface ThreadResponse {
  id: string;
  meta: Record<string, any> | null;  // Contains user_id, channel, contact_id
  created_at: string;
  updated_at: string;
}
```

## Pages to Build

### 1. User List Page (`/users`)

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ Users                                    [+ Add User]    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Search: [________________]  Filter: [All ▾] [Admin ▾]  │
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ 👤 John Smith                            [Edit]  │   │
│ │ Role: User                                       │   │
│ │ Contacts:                                        │   │
│ │   • Telegram: @johnsmith                        │   │
│ │   • Email: john@company.com                     │   │
│ │ Messages: 45 | Last active: 2 hours ago         │   │
│ │ System Prompt: "You are helping John with..."   │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ 👑 Admin (You)                           [Edit]  │   │
│ │ Role: Admin                                      │   │
│ │ Contacts:                                        │   │
│ │   • Telegram: @admin                            │   │
│ │ Messages: 234 | Last active: 5 minutes ago      │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Display all users in card format
- Show user name, role badge (Admin/User), contacts, message count
- Search by name or contact
- Filter by role (All, Admin, User)
- Click user card to view details
- "Add User" button opens modal
- "Edit" button opens edit modal
- Show last active time (calculate from most recent thread event)
- Show contact count and channels used

**Components to use:**
- `Card` from shadcn/ui for user cards
- `Badge` for role display
- `Input` for search
- `Select` for filters
- `Button` for actions
- `Avatar` with user initials

**Data fetching:**
```typescript
const { data: users, isLoading } = useQuery({
  queryKey: ['users'],
  queryFn: async () => {
    const response = await fetch('/api/v1/users');
    return response.json();
  }
});

// Calculate message count and last active
const getUserStats = async (userId: string) => {
  // Get all threads for this user
  const threads = await fetch('/api/v1/threads').then(r => r.json());
  const userThreads = threads.filter(t => t.meta?.user_id === userId);
  
  // Get events for each thread
  let totalMessages = 0;
  let lastActive = null;
  
  for (const thread of userThreads) {
    const events = await fetch(`/api/v1/threads/${thread.id}/events`).then(r => r.json());
    totalMessages += events.length;
    
    if (events.length > 0) {
      const lastEvent = events[events.length - 1];
      if (!lastActive || new Date(lastEvent.created_at) > new Date(lastActive)) {
        lastActive = lastEvent.created_at;
      }
    }
  }
  
  return { totalMessages, lastActive };
};
```

---

### 2. User Profile Editor Modal

**Layout:**
```
┌─────────────────────────────────────────┐
│ Edit User: John Smith                ✕  │
├─────────────────────────────────────────┤
│                                         │
│ Name *                                  │
│ [John Smith                         ]   │
│                                         │
│ Role *                                  │
│ ( ) Admin  (•) User                     │
│                                         │
│ Contacts                                │
│ ┌─────────────────────────────────────┐ │
│ │ Telegram: @johnsmith (8281248569) ✕ │ │
│ │ Email: john@company.com           ✕ │ │
│ │                        [+ Add]      │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ System Prompt                           │
│ ┌─────────────────────────────────────┐ │
│ │ You are helping John with project   │ │
│ │ management. He's working on the     │ │
│ │ mobile app redesign. Be concise.    │ │
│ │                                     │ │
│ │                                     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ⚠️ Changes will apply to all future     │
│    conversations across all channels    │
│                                         │
│              [Cancel] [Save Changes]    │
└─────────────────────────────────────────┘
```

**Features:**
- Edit user name, role, system prompt
- View and manage contacts (add/remove)
- Validation: name required, at least one contact
- Show warning about system prompt changes
- Auto-save on "Save Changes"
- Close on cancel or successful save

**Add Contact Sub-Modal:**
```
┌─────────────────────────────────────────┐
│ Add Contact                          ✕  │
├─────────────────────────────────────────┤
│                                         │
│ Channel *                               │
│ [Telegram ▾]                            │
│   - Telegram                            │
│   - Email                               │
│   - WhatsApp                            │
│   - Slack                               │
│                                         │
│ Contact ID *                            │
│ [@johnsmith                         ]   │
│                                         │
│ ℹ️ For Telegram: username or user ID    │
│    For Email: email address             │
│    For WhatsApp: phone number           │
│                                         │
│              [Cancel] [Add Contact]     │
└─────────────────────────────────────────┘
```

**Components:**
- `Dialog` from shadcn/ui for modal
- `Input` for text fields
- `RadioGroup` for role selection
- `Textarea` for system prompt
- `Select` for channel selection
- `Button` for actions
- `Alert` for warnings

**API calls:**
```typescript
// Update user
const updateUser = async (userId: string, data: Partial<UserCreate>) => {
  const response = await fetch(`/api/v1/users/${userId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return response.json();
};

// Add contact
const addContact = async (userId: string, contact: { channel: string; contact_id: string }) => {
  const response = await fetch(`/api/v1/users/${userId}/contacts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(contact)
  });
  return response.json();
};
```

---

### 3. Unified Conversation View (`/users/{userId}/conversations`)

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ ← Back to Users                                         │
├─────────────────────────────────────────────────────────┤
│ Conversation: John Smith                                │
│ All Channels                                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 📅 March 5, 2026                                        │
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ [Telegram] 2:30 PM                              │   │
│ │ John: What's the status of the mobile app?      │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ [Telegram] 2:31 PM                              │   │
│ │ Bot: The mobile app redesign is 60% complete... │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ [Email] 3:45 PM                                 │   │
│ │ John: Can you send me the latest docs?          │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ [Email] 3:46 PM                                 │   │
│ │ Bot: I've attached the documentation...         │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ 📅 March 6, 2026                                        │
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ [Telegram] 9:15 AM                              │   │
│ │ John: Thanks! One more question...              │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Show all messages from all user's threads in chronological order
- Group by date
- Show channel badge (Telegram, Email, etc.)
- Show timestamp
- Distinguish user vs bot messages (different styling)
- Auto-scroll to bottom
- Load more on scroll up (pagination)
- Filter by channel (optional)

**Data fetching:**
```typescript
const getUserConversations = async (userId: string) => {
  // 1. Get all threads
  const threads = await fetch('/api/v1/threads').then(r => r.json());
  
  // 2. Filter threads for this user
  const userThreads = threads.filter(t => t.meta?.user_id === userId);
  
  // 3. Get events for each thread
  const allEvents = [];
  for (const thread of userThreads) {
    const events = await fetch(`/api/v1/threads/${thread.id}/events`).then(r => r.json());
    
    // Add channel info to each event
    const eventsWithChannel = events.map(e => ({
      ...e,
      channel: thread.meta?.channel || 'unknown',
      contact_id: thread.meta?.contact_id
    }));
    
    allEvents.push(...eventsWithChannel);
  }
  
  // 4. Sort by created_at
  allEvents.sort((a, b) => 
    new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );
  
  return allEvents;
};

const { data: conversations, isLoading } = useQuery({
  queryKey: ['conversations', userId],
  queryFn: () => getUserConversations(userId)
});
```

**Message grouping:**
```typescript
const groupByDate = (events: EventResponse[]) => {
  const grouped: Record<string, EventResponse[]> = {};
  
  events.forEach(event => {
    const date = new Date(event.created_at).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    
    if (!grouped[date]) {
      grouped[date] = [];
    }
    grouped[date].push(event);
  });
  
  return grouped;
};
```

**Components:**
- `ScrollArea` from shadcn/ui
- `Badge` for channel tags
- `Card` for message bubbles
- Custom message component with different styles for user/bot

---

### 4. Contact Management Component

**Embedded in User Profile:**
```
Contacts
┌─────────────────────────────────────────────────┐
│ Channel      Contact ID              Actions    │
├─────────────────────────────────────────────────┤
│ Telegram     @johnsmith (8281248569)    [✕]    │
│ Email        john@company.com           [✕]    │
│ WhatsApp     +1234567890                [✕]    │
│                                                 │
│                                    [+ Add]      │
└─────────────────────────────────────────────────┘
```

**Features:**
- List all contacts in table format
- Show channel icon/badge
- Show contact ID
- Delete button (with confirmation)
- Add button opens add contact modal
- Prevent deleting last contact

**Delete confirmation:**
```
⚠️ Remove Contact?

Are you sure you want to remove:
Telegram: @johnsmith (8281248569)

John will no longer be able to message via this channel.

[Cancel] [Remove]
```

---

## Design System

### Colors
```typescript
const channelColors = {
  telegram: 'bg-blue-500',
  email: 'bg-green-500',
  whatsapp: 'bg-emerald-500',
  slack: 'bg-purple-500',
  unknown: 'bg-gray-500'
};

const roleColors = {
  admin: 'bg-amber-500',
  user: 'bg-blue-500'
};
```

### Icons (use Lucide)
- `User` - User profile
- `Crown` - Admin role
- `MessageSquare` - Messages
- `Mail` - Email channel
- `Phone` - WhatsApp channel
- `Hash` - Telegram channel
- `Plus` - Add actions
- `X` - Delete/close
- `Edit` - Edit actions
- `Search` - Search
- `Filter` - Filter

### Typography
- Page titles: `text-2xl font-bold`
- Section titles: `text-lg font-semibold`
- Body text: `text-sm`
- Timestamps: `text-xs text-muted-foreground`

---

## Routing

```typescript
// App routes
const routes = [
  { path: '/', element: <Dashboard /> },
  { path: '/users', element: <UserListPage /> },
  { path: '/users/:userId', element: <UserDetailPage /> },
  { path: '/users/:userId/conversations', element: <ConversationsPage /> },
];
```

---

## State Management

Use React Query for data fetching:

```typescript
// queries/users.ts
export const useUsers = () => {
  return useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await fetch('/api/v1/users');
      if (!response.ok) throw new Error('Failed to fetch users');
      return response.json();
    }
  });
};

export const useUser = (userId: string) => {
  return useQuery({
    queryKey: ['users', userId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/users/${userId}`);
      if (!response.ok) throw new Error('Failed to fetch user');
      return response.json();
    }
  });
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ userId, data }: { userId: string; data: any }) => {
      const response = await fetch(`/api/v1/users/${userId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('Failed to update user');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    }
  });
};
```

---

## Example Component Structure

```
src/
├── components/
│   ├── users/
│   │   ├── UserCard.tsx
│   │   ├── UserListPage.tsx
│   │   ├── UserEditModal.tsx
│   │   ├── AddContactModal.tsx
│   │   └── ContactList.tsx
│   ├── conversations/
│   │   ├── ConversationsPage.tsx
│   │   ├── MessageBubble.tsx
│   │   └── DateDivider.tsx
│   └── ui/
│       └── (shadcn components)
├── lib/
│   ├── api.ts
│   └── utils.ts
├── hooks/
│   └── useUsers.ts
└── types/
    └── user.ts
```

---

## Testing Checklist

- [ ] User list loads and displays all users
- [ ] Search filters users by name
- [ ] Role filter works (All, Admin, User)
- [ ] Click user card navigates to detail page
- [ ] Add user modal creates new user
- [ ] Edit user modal updates user
- [ ] Add contact adds contact to user
- [ ] Delete contact removes contact (with confirmation)
- [ ] Cannot delete last contact
- [ ] System prompt updates apply correctly
- [ ] Conversations page shows all messages chronologically
- [ ] Messages grouped by date
- [ ] Channel badges display correctly
- [ ] User vs bot messages styled differently
- [ ] Last active time calculates correctly
- [ ] Message count displays correctly

---

## API Configuration

Set the API base URL in your environment:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Use in API calls:
```typescript
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

fetch(`${API_BASE}/api/v1/users`)
```

---

## Additional Features (Optional)

### 1. Real-time Updates
Use WebSocket or polling to update user list when admin adds users via chat:

```typescript
// Poll for updates every 30 seconds
const { data: users } = useQuery({
  queryKey: ['users'],
  queryFn: fetchUsers,
  refetchInterval: 30000
});
```

### 2. Export Conversations
Add button to export user's conversations as JSON or text:

```typescript
const exportConversations = (events: EventResponse[]) => {
  const text = events.map(e => 
    `[${e.channel}] ${new Date(e.created_at).toLocaleString()}\n${e.role}: ${e.content}\n`
  ).join('\n');
  
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `conversations-${userId}.txt`;
  a.click();
};
```

### 3. User Activity Chart
Show message activity over time using a chart library:

```typescript
import { LineChart } from 'recharts';

const getActivityData = (events: EventResponse[]) => {
  // Group by date and count messages
  const grouped = events.reduce((acc, e) => {
    const date = new Date(e.created_at).toLocaleDateString();
    acc[date] = (acc[date] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  return Object.entries(grouped).map(([date, count]) => ({ date, count }));
};
```

---

## Summary

Build a modern, responsive user management interface with:
- **User List** - View all users with search and filters
- **User Editor** - Edit user details, role, system prompt
- **Contact Management** - Add/remove contacts per user
- **Unified Conversations** - View all messages across all channels

Use shadcn/ui components, TailwindCSS for styling, and React Query for data management. The interface should be clean, intuitive, and mobile-responsive.
