# Lovable Prompt: Allow-From Access Control Management

## Overview

Add access control management to the integrations interface, allowing users to specify which users can interact with each bot integration. This includes displaying current allowed users, adding/removing users, and toggling between "allow everyone" and "specific users only" modes.

---

## Part 1: Update Integration Card to Display Allowed Users

Modify the existing `IntegrationCard` component to show who can access the bot.

### Implementation

```tsx
// components/IntegrationCard.tsx - Add to existing component

import { Users, Shield } from 'lucide-react';

// Add this section after the existing card content, before the closing </CardContent>
<div className="mt-4 pt-4 border-t">
  <div className="flex items-center justify-between mb-2">
    <div className="flex items-center gap-2">
      <Shield className="w-4 h-4 text-muted-foreground" />
      <span className="text-sm font-medium">Access Control</span>
    </div>
    <Button 
      variant="ghost" 
      size="sm"
      onClick={() => setShowAllowFromDialog(true)}
    >
      <Users className="w-4 h-4 mr-1" />
      Manage
    </Button>
  </div>
  
  <div className="flex flex-wrap gap-1">
    {integration.meta?.allowFrom?.includes("*") ? (
      <Badge variant="secondary" className="text-xs">
        <Users className="w-3 h-3 mr-1" />
        Everyone
      </Badge>
    ) : integration.meta?.allowFrom && integration.meta.allowFrom.length > 0 ? (
      integration.meta.allowFrom.map((userId: string) => (
        <Badge key={userId} variant="outline" className="text-xs">
          {userId}
        </Badge>
      ))
    ) : (
      <Badge variant="destructive" className="text-xs">
        No access (empty list)
      </Badge>
    )}
  </div>
</div>
```

---

## Part 2: Create Allow-From Management Dialog

Create a new dialog component to manage the allowed users list.

### Implementation

```tsx
// components/AllowFromDialog.tsx
import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { X, Plus, AlertCircle, Info } from 'lucide-react';

interface AllowFromDialogProps {
  open: boolean;
  onClose: () => void;
  integration: {
    id: string;
    integration_type: string;
    display_name: string;
    meta?: {
      allowFrom?: string[];
    };
  };
}

export function AllowFromDialog({ open, onClose, integration }: AllowFromDialogProps) {
  const [allowEveryone, setAllowEveryone] = useState(false);
  const [allowedUsers, setAllowedUsers] = useState<string[]>([]);
  const [newUserId, setNewUserId] = useState('');
  const queryClient = useQueryClient();
  
  // Initialize state from integration meta
  useEffect(() => {
    if (integration.meta?.allowFrom) {
      const allowFrom = integration.meta.allowFrom;
      setAllowEveryone(allowFrom.includes('*'));
      setAllowedUsers(allowFrom.filter(u => u !== '*'));
    } else {
      setAllowEveryone(true);
      setAllowedUsers([]);
    }
  }, [integration]);
  
  const mutation = useMutation({
    mutationFn: async (allowFrom: string[]) => {
      const response = await fetch(
        `/api/v1/config/integrations/${integration.id}/allow-from`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          },
          body: JSON.stringify(allowFrom),
        }
      );
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update access control');
      }
      
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
      onClose();
    },
  });
  
  const handleAddUser = () => {
    const trimmed = newUserId.trim();
    if (trimmed && !allowedUsers.includes(trimmed)) {
      setAllowedUsers([...allowedUsers, trimmed]);
      setNewUserId('');
    }
  };
  
  const handleRemoveUser = (userId: string) => {
    setAllowedUsers(allowedUsers.filter(u => u !== userId));
  };
  
  const handleSave = () => {
    const allowFrom = allowEveryone ? ['*'] : allowedUsers;
    mutation.mutate(allowFrom);
  };
  
  const getUserIdPlaceholder = () => {
    switch (integration.integration_type) {
      case 'telegram':
        return 'User ID (e.g., 170577115) or username (e.g., lgs321)';
      case 'discord':
        return 'User ID (e.g., 123456789012345678)';
      case 'slack':
        return 'User ID (e.g., U01234ABCDE)';
      default:
        return 'User ID or username';
    }
  };
  
  const getHelpText = () => {
    switch (integration.integration_type) {
      case 'telegram':
        return 'You can use Telegram user IDs (numbers) or usernames. The bot will match either.';
      case 'discord':
        return 'Use Discord user IDs. Right-click a user and select "Copy User ID" (requires Developer Mode).';
      case 'slack':
        return 'Use Slack user IDs. Find them in user profiles or via the Slack API.';
      default:
        return 'Enter user identifiers that can access this bot.';
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle>Manage Access Control</DialogTitle>
          <DialogDescription>
            Control who can interact with {integration.display_name}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Allow Everyone Toggle */}
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex-1">
              <Label htmlFor="allow-everyone" className="text-base font-medium">
                Allow Everyone
              </Label>
              <p className="text-sm text-muted-foreground mt-1">
                Anyone can send messages to this bot
              </p>
            </div>
            <Switch
              id="allow-everyone"
              checked={allowEveryone}
              onCheckedChange={setAllowEveryone}
            />
          </div>
          
          {/* Specific Users Section */}
          {!allowEveryone && (
            <div className="space-y-3">
              <div>
                <Label>Allowed Users</Label>
                <p className="text-sm text-muted-foreground mt-1">
                  {getHelpText()}
                </p>
              </div>
              
              {/* Add User Input */}
              <div className="flex gap-2">
                <Input
                  placeholder={getUserIdPlaceholder()}
                  value={newUserId}
                  onChange={(e) => setNewUserId(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddUser();
                    }
                  }}
                />
                <Button onClick={handleAddUser} size="icon">
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              
              {/* User List */}
              {allowedUsers.length > 0 ? (
                <div className="flex flex-wrap gap-2 p-3 border rounded-lg bg-muted/50">
                  {allowedUsers.map((userId) => (
                    <Badge key={userId} variant="secondary" className="pr-1">
                      {userId}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-4 w-4 ml-1 hover:bg-destructive/20"
                        onClick={() => handleRemoveUser(userId)}
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </Badge>
                  ))}
                </div>
              ) : (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    No users allowed. The bot will deny all access until you add users or enable "Allow Everyone".
                  </AlertDescription>
                </Alert>
              )}
              
              {/* Info Alert */}
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Changes require restarting the nanobot-gateway service to take effect.
                </AlertDescription>
              </Alert>
            </div>
          )}
          
          {/* Error Display */}
          {mutation.error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {mutation.error.message}
              </AlertDescription>
            </Alert>
          )}
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

---

## Part 3: Update Add Integration Dialog

Add allowFrom field to the integration creation form.

### Implementation

```tsx
// components/AddIntegrationDialog.tsx - Add to existing component

import { Switch } from '@/components/ui/switch';
import { Info } from 'lucide-react';

// Add these state variables
const [accessMode, setAccessMode] = useState<'everyone' | 'specific'>('everyone');
const [allowedUsers, setAllowedUsers] = useState('');

// Update the mutation to include allowFrom in meta
const mutation = useMutation({
  mutationFn: async (data: { type: string; displayName: string; token: string }) => {
    const allowFrom = accessMode === 'everyone' 
      ? ['*'] 
      : allowedUsers.split(',').map(u => u.trim()).filter(Boolean);
    
    const response = await fetch(`/api/v1/config/integrations/${data.type}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
      body: JSON.stringify({
        display_name: data.displayName,
        token: data.token,
        meta: {
          allowFrom: allowFrom,
        },
      }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create integration');
    }
    
    return response.json();
  },
  // ... rest of mutation config
});

// Add this section to the form, after the token input
<div className="space-y-3 pt-4 border-t">
  <div>
    <Label className="text-base font-medium">Access Control</Label>
    <p className="text-sm text-muted-foreground mt-1">
      Control who can interact with this bot
    </p>
  </div>
  
  <div className="flex items-center justify-between p-3 border rounded-lg">
    <div className="flex-1">
      <Label htmlFor="access-everyone" className="font-medium">
        Allow Everyone
      </Label>
      <p className="text-xs text-muted-foreground mt-0.5">
        Anyone can send messages
      </p>
    </div>
    <Switch
      id="access-everyone"
      checked={accessMode === 'everyone'}
      onCheckedChange={(checked) => setAccessMode(checked ? 'everyone' : 'specific')}
    />
  </div>
  
  {accessMode === 'specific' && (
    <div className="space-y-2">
      <Label htmlFor="allowed-users">Allowed User IDs</Label>
      <Input
        id="allowed-users"
        placeholder="Enter user IDs separated by commas"
        value={allowedUsers}
        onChange={(e) => setAllowedUsers(e.target.value)}
      />
      <div className="flex items-start gap-2 text-xs text-muted-foreground">
        <Info className="h-3 w-3 mt-0.5 flex-shrink-0" />
        <span>
          {type === 'telegram' && 'Use Telegram user IDs (e.g., 170577115) or usernames (e.g., lgs321)'}
          {type === 'discord' && 'Use Discord user IDs (e.g., 123456789012345678)'}
          {type === 'slack' && 'Use Slack user IDs (e.g., U01234ABCDE)'}
        </span>
      </div>
    </div>
  )}
</div>
```

---

## Part 4: API Integration Hook

Create a hook for updating the allowFrom list.

### Implementation

```tsx
// hooks/useUpdateAllowFrom.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useUpdateAllowFrom() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ integrationId, allowFrom }: { integrationId: string; allowFrom: string[] }) => {
      const response = await fetch(
        `/api/v1/config/integrations/${integrationId}/allow-from`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          },
          body: JSON.stringify(allowFrom),
        }
      );
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update access control');
      }
      
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });
}
```

---

## Part 5: Update Integration Type Definition

Update the TypeScript interface to include allowFrom in meta.

### Implementation

```typescript
// types/integration.ts or in the component file
interface Integration {
  id: string;
  integration_type: 'telegram' | 'discord' | 'slack';
  display_name: string;
  status: 'valid' | 'invalid' | 'pending';
  meta?: {
    allowFrom?: string[];
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}
```

---

## API Endpoints Reference

### Get Integrations
```http
GET /api/v1/config/integrations
Authorization: Bearer {token}

Response:
[
  {
    "id": "cred_abc123",
    "integration_type": "telegram",
    "display_name": "My Bot",
    "status": "valid",
    "meta": {
      "allowFrom": ["*"]  // or ["user1", "user2"]
    },
    "created_at": "2026-03-06T12:00:00Z",
    "updated_at": "2026-03-06T12:00:00Z"
  }
]
```

### Create Integration with AllowFrom
```http
POST /api/v1/config/integrations/telegram
Authorization: Bearer {token}
Content-Type: application/json

{
  "display_name": "My Bot",
  "token": "123456:ABC...",
  "meta": {
    "allowFrom": ["170577115", "lgs321"]
  }
}
```

### Update AllowFrom
```http
PATCH /api/v1/config/integrations/{credential_id}/allow-from
Authorization: Bearer {token}
Content-Type: application/json

["170577115", "lgs321"]  // Array of user IDs, or ["*"] for everyone
```

---

## User Experience Flow

### Viewing Access Control
1. User opens integrations page
2. Each integration card shows current access control:
   - "Everyone" badge if `allowFrom: ["*"]`
   - List of user IDs if specific users
   - "No access" warning if empty list

### Managing Access Control
1. User clicks "Manage" button on integration card
2. Dialog opens showing current settings
3. User can:
   - Toggle "Allow Everyone" switch
   - Add user IDs (one at a time or comma-separated)
   - Remove user IDs by clicking X on badges
4. User clicks "Save Changes"
5. System updates database
6. Integration card updates to show new settings
7. Info message reminds user to restart service

### Creating Integration with Access Control
1. User clicks "Add Integration"
2. Fills in platform, name, and token
3. Chooses access control:
   - "Allow Everyone" (default) - sets `["*"]`
   - "Specific Users" - enters comma-separated IDs
4. Creates integration with allowFrom in meta

---

## Access Control Behavior

### Allow Everyone (`["*"]`)
```json
{ "allowFrom": ["*"] }
```
✅ Any user can message the bot

### Specific Users
```json
{ "allowFrom": ["170577115", "lgs321"] }
```
✅ User with ID 170577115 can message  
✅ User with username lgs321 can message  
❌ Other users are denied

### Empty List (Deny All)
```json
{ "allowFrom": [] }
```
❌ All users are denied (useful for temporarily disabling)

### Not Set (Default to Everyone)
```json
{ "meta": {} }
```
✅ Defaults to `["*"]` - everyone allowed

---

## Platform-Specific User ID Formats

### Telegram
- **User ID**: Numeric (e.g., `170577115`)
- **Username**: String (e.g., `lgs321`)
- **Format**: Bot receives `user_id|username`
- **Matching**: Either part matches

### Discord
- **User ID**: Numeric string (e.g., `123456789012345678`)
- **How to get**: Right-click user → Copy User ID (requires Developer Mode)

### Slack
- **User ID**: Alphanumeric (e.g., `U01234ABCDE`)
- **How to get**: User profile or Slack API

---

## Important Notes

1. **Service Restart Required**: Changes to `allowFrom` require restarting the `nanobot-gateway` service to take effect
2. **Validation**: Backend validates that `allowFrom` is a list of strings
3. **Default Behavior**: If `allowFrom` is not set, defaults to `["*"]` (allow everyone)
4. **Security**: Empty list `[]` denies all access (security feature for disabling)
5. **Wildcard**: Use `["*"]` to allow everyone
6. **Case Sensitive**: User IDs are case-sensitive

---

## Testing Checklist

- [ ] Display "Everyone" badge when `allowFrom: ["*"]`
- [ ] Display user IDs when specific users allowed
- [ ] Display "No access" warning when `allowFrom: []`
- [ ] Can toggle between "Allow Everyone" and "Specific Users"
- [ ] Can add user IDs one at a time
- [ ] Can remove user IDs by clicking X
- [ ] Can create integration with allowFrom
- [ ] Changes persist after page refresh
- [ ] Error handling for invalid user IDs
- [ ] Info message about service restart

---

## Summary

This implementation provides:

1. **Visual Access Control** - See who can access each bot at a glance
2. **Easy Management** - Simple dialog to add/remove users
3. **Flexible Modes** - Toggle between "everyone" and "specific users"
4. **Platform Awareness** - Context-specific help text for each platform
5. **Validation** - Client and server-side validation
6. **User Feedback** - Clear error messages and info alerts

The UI integrates seamlessly with the existing integrations interface and provides a user-friendly way to manage bot access control.
