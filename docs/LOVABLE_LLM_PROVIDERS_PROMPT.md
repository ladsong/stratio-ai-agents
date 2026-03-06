# Lovable Frontend Prompt: LLM Provider Management

## Overview

Build a comprehensive LLM Provider management interface that allows users to configure AI providers (OpenAI, Anthropic, Groq, etc.), set API keys, select models, and choose a default provider - all from the web interface.

---

## Backend API Endpoints

Your backend provides these endpoints:

### 1. List LLM Providers
```
GET /api/v1/config/llm-providers
Authorization: Bearer {token}

Response: 200 OK
[
  {
    "id": "uuid",
    "provider": "openai",
    "display_name": "My OpenAI Account",
    "model": "gpt-4",
    "api_base": null,
    "is_default": true,
    "status": "valid",
    "created_at": "2024-03-06T10:00:00Z",
    "updated_at": "2024-03-06T10:00:00Z"
  }
]
```

### 2. Create LLM Provider
```
POST /api/v1/config/llm-providers
Authorization: Bearer {token}
Content-Type: application/json

Request Body:
{
  "provider": "openai",
  "display_name": "My OpenAI Account",
  "api_key": "sk-proj-...",
  "model": "gpt-4",
  "api_base": null,
  "extra_headers": null,
  "is_default": true
}

Response: 201 Created
{
  "id": "uuid",
  "provider": "openai",
  "display_name": "My OpenAI Account",
  "model": "gpt-4",
  "api_base": null,
  "is_default": true,
  "status": "valid",
  "created_at": "2024-03-06T10:00:00Z",
  "updated_at": "2024-03-06T10:00:00Z"
}
```

### 3. Update LLM Provider
```
PATCH /api/v1/config/llm-providers/{provider_id}
Authorization: Bearer {token}
Content-Type: application/json

Request Body (all fields optional):
{
  "display_name": "Updated Name",
  "api_key": "sk-proj-new-key",
  "model": "gpt-4-turbo",
  "api_base": "https://custom.openai.com/v1",
  "extra_headers": {"X-Custom": "value"},
  "is_default": false
}

Response: 200 OK
{
  "id": "uuid",
  "provider": "openai",
  "display_name": "Updated Name",
  "model": "gpt-4-turbo",
  ...
}
```

### 4. Delete LLM Provider
```
DELETE /api/v1/config/llm-providers/{provider_id}
Authorization: Bearer {token}

Response: 200 OK
{
  "message": "Provider deleted successfully"
}
```

### 5. Get Available Models
```
GET /api/v1/config/llm-providers/available-models

Response: 200 OK
{
  "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
  "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229"],
  "groq": ["llama-3.1-70b-versatile", "mixtral-8x7b-32768", "llama-3.1-8b-instant"],
  "openrouter": ["openrouter/anthropic/claude-3.5-sonnet", "openrouter/google/gemini-pro", "openrouter/meta-llama/llama-3.1-70b-instruct"]
}
```

---

## UI Requirements

### Page: LLM Providers Settings (`/settings/llm-providers`)

**Layout:**
- Header with title "LLM Providers" and "Add Provider" button
- Grid/list of provider cards
- Empty state when no providers configured

**Provider Card:**
- Provider logo/icon (OpenAI, Anthropic, Groq, etc.)
- Display name (editable)
- Current model being used
- "Default" badge if `is_default: true`
- Status indicator (green dot for "valid")
- Edit and Delete buttons

**Add/Edit Provider Modal:**

**Step 1: Provider Selection**
- Dropdown to select provider:
  - OpenAI
  - Anthropic
  - Groq
  - OpenRouter
  - (Show provider logos/icons)

**Step 2: Configuration Form**
- Display Name (text input)
  - Placeholder: "My OpenAI Account"
  - Required
- API Key (password input)
  - Placeholder: "sk-proj-..."
  - Required for new, optional for edit
  - Show/hide toggle
  - Validation: Check format based on provider
- Model Selection (dropdown)
  - Populated from `/api/v1/config/llm-providers/available-models`
  - Filtered by selected provider
  - Show model descriptions if available
- Advanced Options (collapsible):
  - API Base URL (text input)
    - Placeholder: "https://api.openai.com/v1"
    - Optional
  - Extra Headers (JSON editor)
    - Optional
- Set as Default (checkbox)
  - Note: "This provider will be used for all new conversations"

**Validation:**
- Display name: Required, max 255 chars
- API key: Required for new provider, must match provider format
- Model: Required, must be valid for selected provider
- API base: Optional, must be valid URL if provided

**Actions:**
- Save button (disabled until form is valid)
- Cancel button
- Test Connection button (optional, validates API key)

---

## User Flow

### Adding a Provider

1. User clicks "Add Provider" button
2. Modal opens with provider selection
3. User selects "OpenAI"
4. Form shows with OpenAI-specific fields
5. User enters:
   - Display name: "My OpenAI"
   - API key: "sk-proj-..."
   - Model: "gpt-4" (from dropdown)
   - Checks "Set as Default"
6. User clicks "Save"
7. API call to `POST /api/v1/config/llm-providers`
8. Modal closes, provider card appears in list
9. Success toast: "OpenAI provider added successfully"

### Editing a Provider

1. User clicks "Edit" on a provider card
2. Modal opens pre-filled with current values
3. API key field shows "••••••••" (masked)
4. User changes model from "gpt-4" to "gpt-4-turbo"
5. User clicks "Save"
6. API call to `PATCH /api/v1/config/llm-providers/{id}`
7. Modal closes, card updates
8. Success toast: "Provider updated successfully"

### Deleting a Provider

1. User clicks "Delete" on a provider card
2. Confirmation dialog: "Are you sure you want to delete this provider?"
3. User confirms
4. API call to `DELETE /api/v1/config/llm-providers/{id}`
5. Card disappears from list
6. Success toast: "Provider deleted successfully"

### Setting Default Provider

1. User checks "Set as Default" on a provider
2. Previous default provider automatically unchecked
3. Only one provider can be default at a time
4. Default provider shown with badge and highlighted card

---

## Design Guidelines

### Colors & Styling

**Provider Colors:**
- OpenAI: Green (#10A37F)
- Anthropic: Orange (#D97757)
- Groq: Purple (#7C3AED)
- OpenRouter: Blue (#3B82F6)

**Status Colors:**
- Valid: Green (#22C55E)
- Invalid: Red (#EF4444)
- Pending: Yellow (#EAB308)

**Card Design:**
- White background
- Border: 1px solid gray-200
- Hover: Shadow elevation
- Default provider: Blue border (2px)

### Icons

Use Lucide React icons:
- `Plus` - Add provider button
- `Settings` - Edit button
- `Trash2` - Delete button
- `Check` - Default badge
- `Eye` / `EyeOff` - Show/hide API key
- `AlertCircle` - Validation errors
- `Sparkles` - LLM provider icon

### Responsive Design

- Desktop: 3-column grid of provider cards
- Tablet: 2-column grid
- Mobile: Single column, full-width cards

---

## Component Structure

```tsx
// Main page component
<LLMProvidersPage>
  <PageHeader>
    <h1>LLM Providers</h1>
    <Button onClick={openAddModal}>
      <Plus /> Add Provider
    </Button>
  </PageHeader>
  
  {providers.length === 0 ? (
    <EmptyState>
      <Sparkles />
      <p>No LLM providers configured</p>
      <Button onClick={openAddModal}>Add Your First Provider</Button>
    </EmptyState>
  ) : (
    <ProviderGrid>
      {providers.map(provider => (
        <ProviderCard
          key={provider.id}
          provider={provider}
          onEdit={openEditModal}
          onDelete={handleDelete}
        />
      ))}
    </ProviderGrid>
  )}
  
  <ProviderModal
    isOpen={modalOpen}
    mode={modalMode} // "create" | "edit"
    provider={selectedProvider}
    onSave={handleSave}
    onClose={closeModal}
  />
</LLMProvidersPage>
```

---

## State Management

```typescript
interface LLMProvider {
  id: string;
  provider: string; // "openai" | "anthropic" | "groq" | "openrouter"
  display_name: string;
  model: string;
  api_base: string | null;
  is_default: boolean;
  status: "valid" | "invalid" | "pending";
  created_at: string;
  updated_at: string;
}

interface ProviderFormData {
  provider: string;
  display_name: string;
  api_key: string;
  model: string;
  api_base?: string;
  extra_headers?: Record<string, string>;
  is_default: boolean;
}

// Available models per provider
interface AvailableModels {
  [provider: string]: string[];
}
```

---

## API Integration Example

```typescript
const API_BASE = 'http://localhost:8000/api/v1';

// Fetch all providers
const fetchProviders = async (): Promise<LLMProvider[]> => {
  const response = await fetch(`${API_BASE}/config/llm-providers`, {
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`
    }
  });
  if (!response.ok) throw new Error('Failed to fetch providers');
  return response.json();
};

// Create provider
const createProvider = async (data: ProviderFormData): Promise<LLMProvider> => {
  const response = await fetch(`${API_BASE}/config/llm-providers`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to create provider');
  return response.json();
};

// Update provider
const updateProvider = async (
  id: string,
  data: Partial<ProviderFormData>
): Promise<LLMProvider> => {
  const response = await fetch(`${API_BASE}/config/llm-providers/${id}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to update provider');
  return response.json();
};

// Delete provider
const deleteProvider = async (id: string): Promise<void> => {
  const response = await fetch(`${API_BASE}/config/llm-providers/${id}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`
    }
  });
  if (!response.ok) throw new Error('Failed to delete provider');
};

// Get available models
const fetchAvailableModels = async (): Promise<AvailableModels> => {
  const response = await fetch(`${API_BASE}/config/llm-providers/available-models`);
  if (!response.ok) throw new Error('Failed to fetch models');
  return response.json();
};
```

---

## Error Handling

**Display user-friendly error messages:**

- **400 Bad Request**: "Invalid provider configuration. Please check your inputs."
- **401 Unauthorized**: "Session expired. Please log in again."
- **404 Not Found**: "Provider not found."
- **409 Conflict**: "A provider with this name already exists."
- **500 Server Error**: "Something went wrong. Please try again later."

**Validation Errors:**
- Show inline errors below form fields
- Highlight invalid fields in red
- Disable save button until all errors resolved

---

## Success Messages

Use toast notifications:
- ✅ "OpenAI provider added successfully"
- ✅ "Provider updated successfully"
- ✅ "Provider deleted successfully"
- ✅ "Default provider changed to Anthropic"

---

## Navigation

Add to settings sidebar:
```
Settings
├── Integrations
├── LLM Providers  ← New
├── Tool Policies
└── Knowledge Base
```

---

## Accessibility

- All buttons have aria-labels
- Form inputs have proper labels
- Modal has focus trap
- Keyboard navigation support (Tab, Enter, Escape)
- Screen reader announcements for state changes

---

## Testing Checklist

- [ ] Can add a new provider
- [ ] Can edit existing provider
- [ ] Can delete a provider
- [ ] Can set/unset default provider
- [ ] Model dropdown populates correctly per provider
- [ ] API key is masked in edit mode
- [ ] Validation works for all fields
- [ ] Error messages display correctly
- [ ] Success toasts appear
- [ ] Empty state shows when no providers
- [ ] Responsive on mobile/tablet/desktop
- [ ] Works with keyboard navigation
- [ ] Screen reader compatible

---

## Additional Features (Optional)

1. **Test Connection Button**
   - Validates API key by making a test call
   - Shows success/failure message

2. **Provider Status Monitoring**
   - Periodically check provider health
   - Show warning if provider is down

3. **Usage Statistics**
   - Show API calls count per provider
   - Display estimated costs

4. **Import from Environment**
   - Button to import API keys from environment variables
   - Migration helper for existing users

5. **Model Recommendations**
   - Suggest best model based on use case
   - Show model capabilities (context length, speed, cost)

---

## Implementation Notes

1. **Security**: API keys are never returned in responses (except during creation). They're stored encrypted in the database.

2. **Default Provider**: Only one provider can be default. When setting a new default, the backend automatically unsets the previous one.

3. **Model Validation**: The backend validates that the selected model is available for the chosen provider.

4. **Fallback**: If no providers are configured, the system falls back to environment variables (for backward compatibility).

5. **Real-time Updates**: Consider using WebSocket or polling to update provider status in real-time.

---

## Summary

Build a clean, intuitive interface for managing LLM providers that:
- Lists all configured providers in cards
- Allows adding/editing/deleting providers
- Supports multiple providers (OpenAI, Anthropic, Groq, OpenRouter)
- Lets users select models from a dropdown
- Manages default provider setting
- Validates all inputs
- Provides clear feedback via toasts
- Works seamlessly on all devices

The interface should feel similar to the existing integrations management but tailored specifically for LLM provider configuration with model selection as a key feature.
