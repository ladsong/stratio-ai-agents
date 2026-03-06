# Lovable Prompt: Integrations Management UI

## Prompt for Lovable

Create a complete integrations management interface that allows users to view, add, and manage their bot integrations (Telegram, Discord, Slack). The interface should fetch existing integrations from the backend API and provide a clean UI for managing them.

---

## Part 1: Integrations List Page

Create a new page at `/integrations` that displays all configured integrations with the following features:

### API Integration

**Endpoint:** `GET /api/v1/config/integrations`

**Query Parameters:**
- `integration_type` (optional): Filter by type (telegram, discord, slack)

**Response Format:**
```typescript
interface Integration {
  id: string;
  integration_type: 'telegram' | 'discord' | 'slack';
  display_name: string;
  status: 'valid' | 'invalid' | 'pending';
  meta: Record<string, any>;
  created_at: string;
  updated_at: string;
}

type IntegrationsResponse = Integration[];
```

**Example Response:**
```json
[
  {
    "id": "cred_abc123",
    "integration_type": "telegram",
    "display_name": "My Telegram Bot",
    "status": "valid",
    "meta": {},
    "created_at": "2026-03-06T12:00:00Z",
    "updated_at": "2026-03-06T12:00:00Z"
  }
]
```

### UI Components

**Page Layout:**
- Header with title "Integrations" and "Add Integration" button
- Filter tabs: All, Telegram, Discord, Slack
- Grid or list view of integration cards
- Empty state when no integrations exist

**Integration Card:**
Each card should display:
- Integration icon (Telegram/Discord/Slack logo)
- Display name
- Integration type badge
- Status indicator (green dot for "valid", red for "invalid", yellow for "pending")
- Created date (formatted as "Added on Mar 6, 2026")
- Actions menu (Edit, Delete)

**Status Indicators:**
```typescript
const statusConfig = {
  valid: { color: 'green', label: 'Active', icon: '✓' },
  invalid: { color: 'red', label: 'Invalid', icon: '✗' },
  pending: { color: 'yellow', label: 'Pending', icon: '⏳' }
};
```

### Implementation Code

```typescript
// hooks/useIntegrations.ts
import { useQuery } from '@tanstack/react-query';

interface Integration {
  id: string;
  integration_type: 'telegram' | 'discord' | 'slack';
  display_name: string;
  status: 'valid' | 'invalid' | 'pending';
  meta: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export function useIntegrations(type?: string) {
  return useQuery({
    queryKey: ['integrations', type],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (type) params.append('integration_type', type);
      
      const response = await fetch(
        `/api/v1/config/integrations?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          },
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch integrations');
      }
      
      return response.json() as Promise<Integration[]>;
    },
  });
}
```

```tsx
// components/IntegrationCard.tsx
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DropdownMenu } from '@/components/ui/dropdown-menu';
import { MoreVertical, MessageSquare, Hash, MessageCircle } from 'lucide-react';

interface IntegrationCardProps {
  integration: Integration;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

const integrationIcons = {
  telegram: MessageSquare,
  discord: Hash,
  slack: MessageCircle,
};

const statusConfig = {
  valid: { color: 'bg-green-500', label: 'Active' },
  invalid: { color: 'bg-red-500', label: 'Invalid' },
  pending: { color: 'bg-yellow-500', label: 'Pending' },
};

export function IntegrationCard({ integration, onEdit, onDelete }: IntegrationCardProps) {
  const Icon = integrationIcons[integration.integration_type];
  const status = statusConfig[integration.status];
  
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-primary/10 rounded-lg">
              <Icon className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">{integration.display_name}</h3>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className="capitalize">
                  {integration.integration_type}
                </Badge>
                <div className="flex items-center gap-1">
                  <div className={`w-2 h-2 rounded-full ${status.color}`} />
                  <span className="text-sm text-muted-foreground">{status.label}</span>
                </div>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Added on {new Date(integration.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit(integration.id)}>
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => onDelete(integration.id)}
                className="text-red-600"
              >
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardContent>
    </Card>
  );
}
```

```tsx
// pages/Integrations.tsx
import { useState } from 'react';
import { useIntegrations } from '@/hooks/useIntegrations';
import { IntegrationCard } from '@/components/IntegrationCard';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus } from 'lucide-react';

export function IntegrationsPage() {
  const [filter, setFilter] = useState<string | undefined>();
  const { data: integrations, isLoading, error } = useIntegrations(filter);
  const [showAddDialog, setShowAddDialog] = useState(false);
  
  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }
  
  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-red-600">
        Error loading integrations. Please try again.
      </div>
    );
  }
  
  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Integrations</h1>
          <p className="text-muted-foreground mt-1">
            Manage your bot integrations across different platforms
          </p>
        </div>
        <Button onClick={() => setShowAddDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Integration
        </Button>
      </div>
      
      <Tabs value={filter || 'all'} onValueChange={(v) => setFilter(v === 'all' ? undefined : v)}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="telegram">Telegram</TabsTrigger>
          <TabsTrigger value="discord">Discord</TabsTrigger>
          <TabsTrigger value="slack">Slack</TabsTrigger>
        </TabsList>
      </Tabs>
      
      {integrations && integrations.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-muted-foreground mb-4">No integrations configured yet</p>
          <Button onClick={() => setShowAddDialog(true)}>
            Add Your First Integration
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
          {integrations?.map((integration) => (
            <IntegrationCard
              key={integration.id}
              integration={integration}
              onEdit={(id) => console.log('Edit', id)}
              onDelete={(id) => console.log('Delete', id)}
            />
          ))}
        </div>
      )}
      
      {showAddDialog && (
        <AddIntegrationDialog 
          open={showAddDialog} 
          onClose={() => setShowAddDialog(false)} 
        />
      )}
    </div>
  );
}
```

---

## Part 2: Add Integration Dialog

Create a dialog component for adding new integrations:

### API Integration

**Endpoint:** `POST /api/v1/config/integrations/{integration_type}`

**Path Parameters:**
- `integration_type`: telegram | discord | slack

**Request Body:**
```typescript
interface IntegrationCreate {
  display_name: string;
  token: string;
  meta?: Record<string, any>;
}
```

**Response:** Same as Integration interface above

**Example Request:**
```bash
POST /api/v1/config/integrations/telegram
Content-Type: application/json

{
  "display_name": "My Telegram Bot",
  "token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
  "meta": {}
}
```

### Implementation Code

```tsx
// components/AddIntegrationDialog.tsx
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface AddIntegrationDialogProps {
  open: boolean;
  onClose: () => void;
}

export function AddIntegrationDialog({ open, onClose }: AddIntegrationDialogProps) {
  const [type, setType] = useState<'telegram' | 'discord' | 'slack'>('telegram');
  const [displayName, setDisplayName] = useState('');
  const [token, setToken] = useState('');
  const queryClient = useQueryClient();
  
  const mutation = useMutation({
    mutationFn: async (data: { type: string; displayName: string; token: string }) => {
      const response = await fetch(`/api/v1/config/integrations/${data.type}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({
          display_name: data.displayName,
          token: data.token,
          meta: {},
        }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create integration');
      }
      
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
      onClose();
      setDisplayName('');
      setToken('');
    },
  });
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate({ type, displayName, token });
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add Integration</DialogTitle>
          <DialogDescription>
            Connect your bot to a messaging platform
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="type">Platform</Label>
            <Select value={type} onValueChange={(v: any) => setType(v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="telegram">Telegram</SelectItem>
                <SelectItem value="discord">Discord</SelectItem>
                <SelectItem value="slack">Slack</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="displayName">Display Name</Label>
            <Input
              id="displayName"
              placeholder="My Bot"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="token">Bot Token</Label>
            <Input
              id="token"
              type="password"
              placeholder={
                type === 'telegram' 
                  ? '123456:ABC-DEF...' 
                  : type === 'discord'
                  ? 'MTk4NjIyNDgzNDcxOTI1MjQ4.Cl2FMQ...'
                  : 'xoxb-...'
              }
              value={token}
              onChange={(e) => setToken(e.target.value)}
              required
            />
            <p className="text-sm text-muted-foreground">
              {type === 'telegram' && 'Get your token from @BotFather on Telegram'}
              {type === 'discord' && 'Get your token from Discord Developer Portal'}
              {type === 'slack' && 'Get your token from Slack API Dashboard'}
            </p>
          </div>
          
          {mutation.error && (
            <Alert variant="destructive">
              <AlertDescription>
                {mutation.error.message}
              </AlertDescription>
            </Alert>
          )}
          
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? 'Adding...' : 'Add Integration'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

---

## Part 3: Delete Integration

### API Integration

**Endpoint:** `DELETE /api/v1/config/integrations/{credential_id}`

**Path Parameters:**
- `credential_id`: The integration ID

**Response:** `204 No Content`

### Implementation Code

```tsx
// hooks/useDeleteIntegration.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useDeleteIntegration() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (integrationId: string) => {
      const response = await fetch(`/api/v1/config/integrations/${integrationId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete integration');
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });
}
```

```tsx
// Add to IntegrationCard.tsx
import { useDeleteIntegration } from '@/hooks/useDeleteIntegration';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

// Inside IntegrationCard component:
const [showDeleteDialog, setShowDeleteDialog] = useState(false);
const deleteMutation = useDeleteIntegration();

const handleDelete = () => {
  deleteMutation.mutate(integration.id);
  setShowDeleteDialog(false);
};

// Add to the component JSX:
<AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Delete Integration</AlertDialogTitle>
      <AlertDialogDescription>
        Are you sure you want to delete "{integration.display_name}"? 
        This action cannot be undone.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction onClick={handleDelete} className="bg-red-600">
        Delete
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

---

## Part 4: Error Handling & Loading States

### Error Handling

```tsx
// components/ErrorBoundary.tsx
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

export function ErrorDisplay({ error }: { error: Error }) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>{error.message}</AlertDescription>
    </Alert>
  );
}
```

### Loading States

```tsx
// components/IntegrationsSkeleton.tsx
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function IntegrationsSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <Skeleton className="w-12 h-12 rounded-lg" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-3 w-40" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```

---

## Summary

This implementation provides:

1. **Integrations List Page** - Displays all configured integrations with filtering
2. **Add Integration Dialog** - Form to create new integrations
3. **Delete Functionality** - Confirmation dialog for deletion
4. **Status Indicators** - Visual feedback for integration health
5. **Error Handling** - Graceful error states
6. **Loading States** - Skeleton loaders during data fetch
7. **Responsive Design** - Works on mobile and desktop

### Required Dependencies

```json
{
  "@tanstack/react-query": "^5.0.0",
  "lucide-react": "^0.300.0",
  "@radix-ui/react-dialog": "^1.0.0",
  "@radix-ui/react-dropdown-menu": "^2.0.0",
  "@radix-ui/react-select": "^2.0.0",
  "@radix-ui/react-alert-dialog": "^1.0.0"
}
```

### Environment Setup

Make sure to configure the API base URL in your environment:

```typescript
// lib/api.ts
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

Update all fetch calls to use: `${API_BASE_URL}/api/v1/config/integrations`
