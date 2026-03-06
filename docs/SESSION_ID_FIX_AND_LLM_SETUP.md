# Session ID Fix and LLM Setup Guide

## ✅ Session ID Error - FIXED

### What Was Wrong
The `backend_bridge.py` was trying to access `msg.session_id`, but the `InboundMessage` class uses `session_key` (a property), not `session_id`. This caused the error:
```
ERROR: 'InboundMessage' object has no attribute 'session_id'
```

### What Was Fixed
All references to `session_id` have been changed to `session_key` in:
- `_handle_message()` method
- `_get_or_create_thread()` method
- `_send_response()` method

Additionally, the `_send_response()` method was fixed to use the correct `OutboundMessage` attributes:
```python
# Before (WRONG):
outbound = OutboundMessage(
    session_id=original_msg.session_id,  # ❌ Doesn't exist
    content=content,
    metadata=original_msg.metadata
)

# After (CORRECT):
outbound = OutboundMessage(
    channel=original_msg.channel,  # ✅ Correct
    chat_id=original_msg.chat_id,  # ✅ Correct
    content=content,
    metadata=original_msg.metadata
)
```

### Service Status
The `nanobot-gateway` service has been rebuilt and restarted with the fixes applied.

---

## ⚠️ LLM Provider Setup - ACTION REQUIRED

### Current Status
Your bot can now receive messages without errors, but **it cannot generate intelligent responses yet** because no LLM provider is configured.

### What You Need to Do

**Choose ONE of the following providers and add your API key to the `.env` file:**

#### Option 1: Groq (Recommended for Testing - FREE)
**Best for:** Testing, development, fast responses
**Cost:** Free tier available
**Speed:** Very fast

1. Sign up at https://console.groq.com/
2. Create an API key (starts with `gsk_`)
3. Edit `.env` and uncomment/add:
   ```bash
   GROQ_API_KEY=gsk_your_key_here
   ```
4. The bot will use: `groq/llama-3.1-70b-versatile`

#### Option 2: OpenAI (Recommended for Production)
**Best for:** Production, reliability, well-documented
**Cost:** Pay-as-you-go (~$0.01-0.03 per 1K tokens)
**Speed:** Fast

1. Sign up at https://platform.openai.com/
2. Add payment method
3. Create API key (starts with `sk-proj-`)
4. Edit `.env` and uncomment/add:
   ```bash
   OPENAI_API_KEY=sk-proj-your_key_here
   ```
5. The bot will use: `gpt-4` or `gpt-3.5-turbo`

#### Option 3: Anthropic (Recommended for Quality)
**Best for:** Best quality responses (Claude)
**Cost:** Pay-as-you-go (~$0.015-0.075 per 1K tokens)
**Speed:** Fast

1. Sign up at https://console.anthropic.com/
2. Add payment method
3. Create API key (starts with `sk-ant-`)
4. Edit `.env` and uncomment/add:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your_key_here
   ```
5. The bot will use: `claude-3-5-sonnet-20241022`

#### Option 4: OpenRouter (Recommended for Flexibility)
**Best for:** Access to 100+ models, cost optimization
**Cost:** Varies by model
**Speed:** Varies by model

1. Sign up at https://openrouter.ai/
2. Create API key (starts with `sk-or-v1-`)
3. Edit `.env` and uncomment/add:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-your_key_here
   ```
4. Can use any model available on OpenRouter

---

## 🚀 After Adding Your API Key

### Step 1: Restart Services
```bash
cd /Users/ladsong/Documents/EDS/bots/nanobot
docker compose restart gateway runtime
```

### Step 2: Test Your Bot
1. Open Telegram
2. Send a message to @godofredo_gomes_bot
3. The bot should respond with an AI-generated message

### Step 3: Monitor Logs
```bash
docker compose logs gateway --tail 50 -f
```

Look for:
- ✅ "Message from telegram:CHAT_ID: ..."
- ✅ "Created thread ... for session ..."
- ✅ "Run created: ..."
- ✅ LLM API calls
- ✅ "Sent response to telegram:CHAT_ID"

---

## 📊 Expected Behavior

### Before LLM Configuration
```
User: "Hello"
Bot: [No response - LLM not configured]
Logs: Error about missing API key or failed run
```

### After LLM Configuration
```
User: "Hello"
Bot: "Hello! I'm a helpful AI assistant. How can I help you today?"
Logs: Successful thread creation, run execution, and response
```

---

## 🔍 Troubleshooting

### Issue: Bot still doesn't respond
**Check:**
1. Is the API key correctly added to `.env`?
2. Did you restart the services? (`docker compose restart gateway runtime`)
3. Check logs: `docker compose logs gateway --tail 50`

### Issue: "Invalid API key" error
**Solution:**
1. Verify the API key is correct (no extra spaces)
2. Ensure the key starts with the correct prefix:
   - OpenAI: `sk-proj-`
   - Anthropic: `sk-ant-`
   - Groq: `gsk_`
   - OpenRouter: `sk-or-v1-`

### Issue: "Rate limit exceeded"
**Solution:**
1. For free tiers (Groq), wait a few minutes
2. For paid tiers, check your account balance
3. Consider switching to a different provider

### Issue: Slow responses
**Solution:**
1. Use Groq for fastest responses
2. Use smaller models (e.g., `gpt-3.5-turbo` instead of `gpt-4`)
3. Check your internet connection

---

## 💡 Model Selection

You can change the model by setting environment variables in `.env`:

```bash
# For OpenAI
NANOBOT_MODEL=gpt-4
# or
NANOBOT_MODEL=gpt-3.5-turbo

# For Anthropic
NANOBOT_MODEL=claude-3-5-sonnet-20241022
# or
NANOBOT_MODEL=claude-3-opus-20240229

# For Groq
NANOBOT_MODEL=groq/llama-3.1-70b-versatile
# or
NANOBOT_MODEL=groq/mixtral-8x7b-32768

# For OpenRouter (any model)
NANOBOT_MODEL=openrouter/anthropic/claude-3.5-sonnet
```

After changing the model, restart services:
```bash
docker compose restart gateway runtime
```

---

## 📝 Summary

### What's Working Now
✅ Telegram bot receives messages  
✅ Access control (allowFrom list) works  
✅ No more session_id errors  
✅ Messages are processed correctly  

### What You Need to Do
⚠️ Add an LLM provider API key to `.env`  
⚠️ Restart gateway and runtime services  
⚠️ Test the bot  

### Recommended Next Steps
1. **Get a Groq API key** (free, fast, easy to test)
2. **Add it to `.env`**: `GROQ_API_KEY=gsk_...`
3. **Restart services**: `docker compose restart gateway runtime`
4. **Test**: Send "Hello" to @godofredo_gomes_bot
5. **Enjoy**: Your bot should respond intelligently!

---

## 🎯 Quick Start (Groq - Free)

```bash
# 1. Get API key from https://console.groq.com/

# 2. Edit .env
nano /Users/ladsong/Documents/EDS/bots/nanobot/.env
# Uncomment and add: GROQ_API_KEY=gsk_your_key_here

# 3. Restart services
cd /Users/ladsong/Documents/EDS/bots/nanobot
docker compose restart gateway runtime

# 4. Test
# Send a message to @godofredo_gomes_bot on Telegram

# 5. Monitor
docker compose logs gateway --tail 50 -f
```

That's it! Your bot should now respond intelligently to messages.
