from __future__ import annotations

import os
import uuid
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END
from litellm import completion


class RouterState(TypedDict):
    thread_id: str
    run_id: str
    messages: list[dict[str, Any]]
    system_prompt: str | None
    user_id: str | None
    user_role: str | None
    intent: str | None
    route_target: str | None
    is_admin_command: bool | None
    admin_command: dict[str, Any] | None
    response: str | None
    artifact_id: str | None
    artifact_content: dict[str, Any] | None


def classify_intent(state: RouterState) -> RouterState:
    messages = state.get("messages", [])
    user_role = state.get("user_role", "user")
    
    if not messages:
        state["intent"] = "unknown"
        state["is_admin_command"] = False
        return state
    
    last_message = messages[-1]
    content = last_message.get("content", "").lower()
    
    # Check if admin is issuing a command
    if user_role == "admin":
        admin_keywords = ["add", "allow", "remove", "revoke", "make", "promote", "demote", 
                         "change", "update", "show me", "list", "who has"]
        if any(keyword in content for keyword in admin_keywords):
            state["is_admin_command"] = True
            state["intent"] = "admin_command"
            return state
    
    state["is_admin_command"] = False
    
    if any(word in content for word in ["strategy", "plan", "approach"]):
        state["intent"] = "strategy"
    elif any(word in content for word in ["analyze", "research", "investigate"]):
        state["intent"] = "analysis"
    else:
        state["intent"] = "general"
    
    return state


def route_to_strategy(state: RouterState) -> RouterState:
    intent = state.get("intent", "general")
    
    if intent == "strategy":
        state["route_target"] = "strategy_synthesis"
    elif intent == "analysis":
        state["route_target"] = "analysis_graph"
    else:
        state["route_target"] = "default_handler"
    
    return state


DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant. Be concise, accurate, and friendly.

Key guidelines:
- Provide clear, direct answers
- Ask clarifying questions when needed
- Remember context from our conversation
- Be proactive in offering relevant suggestions"""


def generate_response(state: RouterState) -> RouterState:
    """Generate AI response using LLM with system prompt and conversation history."""
    messages = state.get("messages", [])
    
    if not messages:
        state["response"] = "Hello! How can I help you today?"
        return state
    
    try:
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            state["response"] = "Error: No API key configured"
            return state
        
        # Get system prompt from state or use default
        system_prompt = state.get("system_prompt") or DEFAULT_SYSTEM_PROMPT
        
        # Apply context window limit (keep last N messages to save tokens)
        max_history_messages = 20  # ~5K tokens for history
        if len(messages) > max_history_messages:
            # Keep system context but trim old messages
            messages = messages[-max_history_messages:]
        
        # Build full message array with system prompt
        full_messages = [
            {"role": "system", "content": system_prompt}
        ] + messages
        
        # Call LLM
        response = completion(
            model="gpt-4o",
            messages=full_messages,
            api_key=api_key,
            max_tokens=2000,
            temperature=0.7
        )
        
        # Extract response content
        assistant_message = response.choices[0].message.content
        
        # Add assistant response to messages
        state["messages"].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # Store response
        state["response"] = assistant_message
        
    except Exception as e:
        state["response"] = f"Error generating response: {str(e)}"
    
    return state


def detect_admin_command(state: RouterState) -> RouterState:
    """Detect and parse admin command using LLM."""
    messages = state.get("messages", [])
    if not messages:
        return state
    
    last_message = messages[-1]
    content = last_message.get("content", "")
    
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            state["response"] = "Error: No API key configured"
            return state
        
        # Use LLM to parse admin command
        command_parser_prompt = """You are an admin command parser. Parse the following message and extract command details.

Supported commands:
- add_user: Add a new user (extract: name, channel, contact_id)
- remove_user: Remove a user (extract: name or contact_id)
- set_role: Change user role (extract: name, new_role)
- update_prompt: Update user's system prompt (extract: name, new_prompt)
- list_users: List all users
- view_user: View user details (extract: name or contact_id)

Respond with JSON only:
{"command_type": "add_user|remove_user|...", "params": {"name": "...", ...}}

If not a command, respond: {"command_type": null}"""
        
        response = completion(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": command_parser_prompt},
                {"role": "user", "content": content}
            ],
            api_key=api_key,
            max_tokens=500,
            temperature=0
        )
        
        import json
        command_data = json.loads(response.choices[0].message.content)
        state["admin_command"] = command_data
        
    except Exception as e:
        state["admin_command"] = {"command_type": None, "error": str(e)}
    
    return state


def execute_admin_command(state: RouterState) -> RouterState:
    """Execute admin command (placeholder - actual execution via API)."""
    command = state.get("admin_command", {})
    command_type = command.get("command_type")
    params = command.get("params", {})
    
    if not command_type:
        # Not a command, treat as normal conversation
        state["is_admin_command"] = False
        return state
    
    # Format response based on command type
    if command_type == "add_user":
        name = params.get("name", "Unknown")
        channel = params.get("channel", "telegram")
        contact_id = params.get("contact_id", "")
        state["response"] = f"✅ Added {name}\n   • {channel.capitalize()}: {contact_id}\n   • Role: User\n   • System prompt: Default\n\nThey can now message me. I'll remember our conversations across all channels."
    elif command_type == "remove_user":
        name = params.get("name", "user")
        state["response"] = f"✅ Removed {name}\n   • All their conversations are archived\n   • They can no longer message the bot"
    elif command_type == "set_role":
        name = params.get("name", "user")
        new_role = params.get("new_role", "user")
        state["response"] = f"✅ {name} is now {new_role.capitalize()}\n   • They can now {'see sensitive information and manage users' if new_role == 'admin' else 'access basic features'}"
    elif command_type == "update_prompt":
        name = params.get("name", "user")
        new_prompt = params.get("new_prompt", "")
        state["response"] = f"✅ Updated system prompt for {name}\n\nNew prompt:\n\"{new_prompt[:100]}...\"\n\nThis will apply to all their conversations across all channels."
    elif command_type == "list_users":
        state["response"] = "📋 Active Users\n\n👤 Users will be listed here\n   (This command needs backend API integration)"
    elif command_type == "view_user":
        name = params.get("name", "user")
        state["response"] = f"👤 {name}\n\nRole: User\nContacts: (API integration needed)\nMessages: (API integration needed)"
    else:
        state["response"] = "I didn't understand that command. Try: 'add [name]', 'remove [name]', 'list users', etc."
    
    return state


def create_response_artifact(state: RouterState) -> RouterState:
    """Create artifact from the AI response."""
    response = state.get("response")
    
    if not response:
        return state
    
    # Create artifact
    artifact_id = str(uuid.uuid4())
    
    artifact_content = {
        "type": "chat_response",
        "content": response,
        "messages": state.get("messages", []),
        "intent": state.get("intent"),
        "route_target": state.get("route_target"),
        "is_admin_command": state.get("is_admin_command", False)
    }
    
    state["artifact_id"] = artifact_id
    state["artifact_content"] = artifact_content
    
    return state


def build_conversation_router_graph(config: dict[str, Any]):
    workflow = StateGraph(RouterState)
    
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("detect_admin_command", detect_admin_command)
    workflow.add_node("execute_admin_command", execute_admin_command)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("create_response_artifact", create_response_artifact)
    
    workflow.set_entry_point("classify_intent")
    
    # Route based on whether it's an admin command
    def route_after_classify(state: RouterState) -> str:
        if state.get("is_admin_command"):
            return "admin_command"
        return "normal"
    
    workflow.add_conditional_edges(
        "classify_intent",
        route_after_classify,
        {
            "admin_command": "detect_admin_command",
            "normal": "generate_response"
        }
    )
    
    workflow.add_edge("detect_admin_command", "execute_admin_command")
    workflow.add_edge("execute_admin_command", "create_response_artifact")
    workflow.add_edge("generate_response", "create_response_artifact")
    workflow.add_edge("create_response_artifact", END)
    
    checkpointer = config.get("checkpointer")
    return workflow.compile(checkpointer=checkpointer)
