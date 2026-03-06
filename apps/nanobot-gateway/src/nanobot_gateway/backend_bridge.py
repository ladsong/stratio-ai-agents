"""Bridge nanobot channels to backend API."""

import asyncio
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
        session_id = msg.session_id
        content = msg.content
        
        logger.info(f"Message from {session_id}: {content[:50]}...")
        
        try:
            thread_id = await self._get_or_create_thread(session_id, msg.metadata)
            
            run_id = await self._create_run(thread_id, content)
            
            state = await self._poll_run(run_id)
            
            if state["status"] == "failed":
                await self._send_response(msg, f"Error: {state.get('error')}")
                return
            
            artifacts = await self._get_artifacts(run_id)
            
            if artifacts:
                response = artifacts[0].get("content", "No response")
                await self._send_response(msg, response)
            else:
                await self._send_response(msg, "Processed but no response generated.")
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await self._send_response(msg, f"Unexpected error: {str(e)}")
    
    async def _get_or_create_thread(self, session_id: str, metadata: dict) -> str:
        """Get or create thread for session."""
        if session_id in self.session_threads:
            return self.session_threads[session_id]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/threads",
                headers=self.headers,
                json={"meta": {"session_id": session_id, **metadata}}
            )
            response.raise_for_status()
            thread_id = response.json()["id"]
            self.session_threads[session_id] = thread_id
            logger.info(f"Created thread {thread_id} for session {session_id}")
            return thread_id
    
    async def _create_run(self, thread_id: str, message: str) -> str:
        """Create a run."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/runs",
                headers=self.headers,
                json={
                    "thread_id": thread_id,
                    "graph_name": "conversation_router",
                    "meta": {"messages": [{"role": "user", "content": message}]}
                }
            )
            response.raise_for_status()
            run_id = response.json()["id"]
            logger.info(f"Created run {run_id} for thread {thread_id}")
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
    
    async def _send_response(self, original_msg: InboundMessage, content: str):
        """Send response back through bus."""
        outbound = OutboundMessage(
            session_id=original_msg.session_id,
            content=content,
            metadata=original_msg.metadata
        )
        await self.bus.publish_outbound(outbound)
        logger.info(f"Sent response to session {original_msg.session_id}")
