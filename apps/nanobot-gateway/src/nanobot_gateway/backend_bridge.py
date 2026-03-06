"""Bridge nanobot channels to backend API."""

import ast
import asyncio
import uuid
import httpx
from loguru import logger
from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus


class BackendBridge:
    """Bridges nanobot message bus to backend API."""
    
    def __init__(self, bus: MessageBus, api_base: str, api_token: str = ""):
        self.bus = bus
        self.api_base = api_base
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}" if api_token else ""
        }
        self.session_threads = {}
    
    async def start(self):
        """Start processing messages."""
        logger.info("BackendBridge started")
        
        asyncio.create_task(self._process_inbound())
        
        while True:
            await asyncio.sleep(1)
    
    async def _process_inbound(self):
        """Process inbound messages from channels."""
        while True:
            try:
                msg = await self.bus.consume_inbound()
                await self._handle_message(msg)
            except Exception as e:
                logger.error(f"Error processing inbound: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _handle_message(self, msg: InboundMessage):
        """Handle an inbound message."""
        session_key = msg.session_key
        content = msg.content
        
        logger.info(f"Message from {session_key}: {content[:50]}...")
        
        try:
            # Parse channel and contact_id from session_key (e.g., "telegram:12345")
            channel, contact_id = self._parse_session_key(session_key)
            
            # Get or create user for this contact
            user_id, user_role = await self._get_or_create_user(channel, contact_id, msg.metadata)
            
            # Get or create thread for this user
            thread_id = await self._get_or_create_thread(user_id, channel, contact_id, msg.metadata)
            
            # Load conversation history across all user's threads
            history = await self._get_conversation_history(thread_id, limit=20)
            
            # Add current user message
            messages = history + [{"role": "user", "content": content}]
            
            # Create run with full context including user info
            run_id = await self._create_run(thread_id, messages, user_id, user_role)
            
            state = await self._poll_run(run_id)
            
            if state["status"] == "failed":
                await self._send_response(msg, f"Error: {state.get('error')}")
                return
            
            artifacts = await self._get_artifacts(run_id)
            
            if artifacts:
                content_str = artifacts[0].get("content", "No response")
                try:
                    # Parse stringified dict to extract actual message
                    content_dict = ast.literal_eval(content_str)
                    response = content_dict.get("content", content_str)
                except (ValueError, SyntaxError):
                    # Fallback to raw content if parsing fails
                    response = content_str
                
                # Store user message and assistant response as events
                await self._store_message_events(thread_id, content, response)
                
                await self._send_response(msg, response)
            else:
                await self._send_response(msg, "Processed but no response generated.")
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await self._send_response(msg, f"Unexpected error: {str(e)}")
    
    def _parse_session_key(self, session_key: str) -> tuple[str, str]:
        """Parse session_key into channel and contact_id."""
        parts = session_key.split(":", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return "unknown", session_key
    
    async def _get_or_create_user(self, channel: str, contact_id: str, metadata: dict) -> tuple[str, str]:
        """Get or create user for this contact."""
        async with httpx.AsyncClient() as client:
            # Try to get existing user by contact
            try:
                response = await client.get(
                    f"{self.api_base}/users/contacts/{channel}/{contact_id}",
                    headers=self.headers
                )
                if response.status_code == 200:
                    user = response.json()
                    return user["id"], user["role"]
            except:
                pass
            
            # User doesn't exist, create new user
            name = metadata.get("first_name", f"{channel}:{contact_id}")
            response = await client.post(
                f"{self.api_base}/users",
                headers=self.headers,
                json={
                    "name": name,
                    "role": "user",
                    "meta": {"auto_created": True}
                }
            )
            response.raise_for_status()
            user = response.json()
            user_id = user["id"]
            
            # Add contact to user
            await client.post(
                f"{self.api_base}/users/{user_id}/contacts",
                headers=self.headers,
                json={
                    "channel": channel,
                    "contact_id": contact_id,
                    "meta": metadata
                }
            )
            
            logger.info(f"Created user {user_id} for {channel}:{contact_id}")
            return user_id, "user"
    
    async def _get_or_create_thread(self, user_id: str, channel: str, contact_id: str, metadata: dict) -> str:
        """Get or create thread for user."""
        cache_key = f"{user_id}:{channel}:{contact_id}"
        if cache_key in self.session_threads:
            return self.session_threads[cache_key]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/threads",
                headers=self.headers,
                json={
                    "meta": {
                        "user_id": user_id,
                        "channel": channel,
                        "contact_id": contact_id,
                        **metadata
                    }
                }
            )
            response.raise_for_status()
            thread_id = response.json()["id"]
            self.session_threads[cache_key] = thread_id
            logger.info(f"Created thread {thread_id} for user {user_id}")
            return thread_id
    
    async def _create_run(self, thread_id: str, messages: list[dict], user_id: str, user_role: str) -> str:
        """Create a run with full message history and user context."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/runs",
                headers=self.headers,
                json={
                    "thread_id": thread_id,
                    "graph_name": "conversation_router",
                    "meta": {
                        "messages": messages,
                        "user_id": user_id,
                        "user_role": user_role
                    }
                }
            )
            response.raise_for_status()
            run_id = response.json()["id"]
            logger.info(f"Created run {run_id} for thread {thread_id} (user {user_id}, role {user_role})")
            return run_id
    
    async def _poll_run(self, run_id: str, max_attempts: int = 60) -> dict:
        """Poll run until complete."""
        async with httpx.AsyncClient() as client:
            for attempt in range(max_attempts):
                response = await client.get(
                    f"{self.api_base}/runs/{run_id}/state",
                    headers=self.headers
                )
                response.raise_for_status()
                state = response.json()
                
                if state["status"] in ["completed", "failed"]:
                    logger.info(f"Run {run_id} {state['status']}")
                    return state
                
                await asyncio.sleep(1)
        
        raise TimeoutError(f"Run {run_id} timeout after 60 seconds")
    
    async def _get_artifacts(self, run_id: str) -> list:
        """Get run artifacts."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/runs/{run_id}/artifacts",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def _get_conversation_history(self, thread_id: str, limit: int = 20) -> list[dict]:
        """Load recent conversation history from events."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/threads/{thread_id}/events",
                headers=self.headers,
                params={"limit": limit}
            )
            response.raise_for_status()
            events = response.json()
            
            # Convert events to message format (reverse to chronological order)
            messages = []
            for event in reversed(events):  # API returns desc, we want asc
                messages.append({
                    "role": event["role"],
                    "content": event["content"]
                })
            return messages
    
    async def _store_message_events(self, thread_id: str, user_content: str, assistant_content: str):
        """Store user and assistant messages as events."""
        async with httpx.AsyncClient() as client:
            # Store user message
            await client.post(
                f"{self.api_base}/threads/{thread_id}/events",
                headers=self.headers,
                json={
                    "id": str(uuid.uuid4()),
                    "role": "user",
                    "content": user_content
                }
            )
            
            # Store assistant message
            await client.post(
                f"{self.api_base}/threads/{thread_id}/events",
                headers=self.headers,
                json={
                    "id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": assistant_content
                }
            )
    
    async def _send_response(self, original_msg: InboundMessage, content: str):
        """Send response back through bus."""
        outbound = OutboundMessage(
            channel=original_msg.channel,
            chat_id=original_msg.chat_id,
            content=content,
            metadata=original_msg.metadata
        )
        await self.bus.publish_outbound(outbound)
        logger.info(f"Sent response to {original_msg.channel}:{original_msg.chat_id}")
