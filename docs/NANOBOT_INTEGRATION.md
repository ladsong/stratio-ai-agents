# Nanobot Integration Guide

This guide explains how to use the integrated nanobot tools, skills, and channels with the backend API.

## Overview

The nanobot integration provides:

- **9 Production-Ready Tools** - Shell execution, file operations, web search, etc.
- **6 Built-in Skills** - GitHub, weather, summarization, tmux, clawhub, skill-creator
- **10+ Channel Integrations** - Telegram, Discord, Slack, WhatsApp, Email, and more
- **Message Bus Architecture** - Seamless integration with backend API

## Architecture

```
Telegram/Discord/Slack
         ↓
Nanobot Channel (receives message)
         ↓
Message Bus
         ↓
Backend Bridge
         ↓
Backend API (POST /api/v1/runs)
         ↓
Worker → Runtime → LangGraph → Nanobot Tools
         ↓
Artifacts
         ↓
Backend Bridge
         ↓
Message Bus → Channel → User
```

## Available Nanobot Tools

| Tool | Description | Permission Level |
|------|-------------|------------------|
| `exec` | Execute shell commands with safety guards | admin |
| `read_file` | Read file contents | safe |
| `write_file` | Write to files | admin |
| `list_dir` | List directory contents | safe |
| `web_search` | Search the web using Brave API | network |
| `fetch_url` | Fetch URL content | network |
| `message` | Send messages through channels | safe |
| `cron` | Schedule tasks | admin |
| `spawn` | Run background processes | admin |

## Available Nanobot Skills

| Skill | Description |
|-------|-------------|
| `github` | Interact with GitHub using the `gh` CLI |
| `weather` | Get weather information using wttr.in and Open-Meteo |
| `summarize` | Summarize URLs, files, and YouTube videos |
| `tmux` | Remote-control tmux sessions |
| `clawhub` | Search and install skills from ClawHub registry |
| `skill-creator` | Create new skills |

## Setup

### 1. Configure Telegram Bot

Get a bot token from [@BotFather](https://t.me/BotFather):

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy the bot token

### 2. Update Environment Variables

Add to your `.env` file:

```bash
# Enable Telegram channel
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your-bot-token-here

# Optional: Enable other channels
DISCORD_ENABLED=false
DISCORD_BOT_TOKEN=

SLACK_ENABLED=false
SLACK_BOT_TOKEN=
SLACK_APP_TOKEN=
```

### 3. Start the Services

```bash
# Build and start all services including nanobot-gateway
docker compose up -d

# Check nanobot-gateway logs
docker compose logs -f nanobot-gateway
```

You should see:
```
Starting nanobot gateway → http://gateway:8000/api/v1
BackendBridge started
```

## Usage Examples

### Basic Conversation

**User in Telegram:**
```
Hello! Can you help me?
```

**Bot Response:**
```
Hi! I'm here to help. I have access to various tools and skills.
What would you like me to do?
```

### Using Tools

**User:**
```
List files in /tmp directory
```

**Bot uses `list_dir` tool:**
```
Files in /tmp:
- file1.txt
- file2.log
- temp_data/
```

**User:**
```
Search for "LangGraph tutorial"
```

**Bot uses `web_search` tool:**
```
Here are the top results for "LangGraph tutorial":
1. LangGraph Documentation - https://...
2. Building with LangGraph - https://...
```

### Using Skills

**User:**
```
What's the weather in Tokyo?
```

**Bot uses `weather` skill:**
```
Weather in Tokyo:
🌡️ Temperature: 15°C
☁️ Conditions: Partly cloudy
💨 Wind: 10 km/h
```

**User:**
```
Summarize this article: https://example.com/article
```

**Bot uses `summarize` skill:**
```
Summary of the article:
- Main point 1
- Main point 2
- Conclusion
```

## Channel Configuration

### Telegram

```yaml
telegram:
  enabled: true
  token: YOUR_BOT_TOKEN
  allowFrom: ["*"]  # Allow all users, or specify user IDs
```

### Discord

```yaml
discord:
  enabled: true
  token: YOUR_BOT_TOKEN
  allowFrom: ["*"]
```

### Slack

```yaml
slack:
  enabled: true
  token: YOUR_BOT_TOKEN
  appToken: YOUR_APP_TOKEN
  allowFrom: ["*"]
```

## Message Flow

1. **User sends message** in Telegram/Discord/Slack
2. **Nanobot channel** receives the message
3. **Message bus** queues the inbound message
4. **Backend bridge** processes the message:
   - Gets or creates a thread for the session
   - Creates a run with the user's message
   - Polls until the run completes
   - Retrieves artifacts
5. **Response sent** back through the message bus
6. **Channel delivers** response to user

## Tool Policy Integration

Nanobot tools respect the backend's tool policy system:

```bash
# Create a global policy allowing only safe tools
curl -X PUT http://localhost:8000/api/v1/config/tool-policy \
  -H "Content-Type: application/json" \
  -d '{
    "scope_type": "global",
    "mode": "allowlist",
    "tools": ["read_file", "list_dir", "web_search"]
  }'
```

Now users can only use safe tools through the channels.

## Skills in Workflows

Load nanobot skills into your LangGraph workflows:

```python
from core.skills.loader import SkillsManager

skills_manager = SkillsManager()

# List available skills
skills = skills_manager.list_available_skills()

# Load specific skills for context
skills_context = skills_manager.load_skills_for_context([
    "github",
    "weather",
    "summarize"
])

# Use in workflow state
state = {
    "messages": messages,
    "skills": skills_context
}
```

## Troubleshooting

### Bot not responding

Check the logs:
```bash
docker compose logs -f nanobot-gateway
```

Look for:
- "BackendBridge started" - Bridge is running
- "Message from {session_id}" - Messages are being received
- "Created thread X for session Y" - Threads are being created
- "Created run Z for thread X" - Runs are being created

### Channel not connecting

Verify your bot token:
```bash
# Check environment variables
docker compose exec nanobot-gateway env | grep TELEGRAM
```

### Tools not working

Check tool policies:
```bash
# List current policies
curl http://localhost:8000/api/v1/config/tool-policy
```

## Advanced Configuration

### Custom Skills

Create custom skills in `/workspace/skills/`:

```bash
mkdir -p /workspace/skills/my-skill
cat > /workspace/skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: My custom skill
---

# My Custom Skill

Instructions for the agent on how to use this skill...
EOF
```

### Multiple Channels

Enable multiple channels simultaneously:

```bash
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=telegram-token

DISCORD_ENABLED=true
DISCORD_BOT_TOKEN=discord-token

SLACK_ENABLED=true
SLACK_BOT_TOKEN=slack-token
SLACK_APP_TOKEN=slack-app-token
```

Each channel gets its own session, but all use the same backend API.

## Next Steps

- Add more nanobot tools as needed
- Create custom skills for your use cases
- Enable additional channels (Email, WhatsApp, etc.)
- Integrate MCP (Model Context Protocol) support
- Add tool usage analytics
- Create skill marketplace integration

## Resources

- [Nanobot Documentation](https://github.com/HKUDS/nanobot)
- [Backend API Documentation](./openapi-draft.md)
- [Tool Policy Documentation](./CONFIG_POLICY.md)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
