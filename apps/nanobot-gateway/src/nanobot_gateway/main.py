"""Nanobot gateway entry point."""

import asyncio
import os
from loguru import logger
from nanobot.bus.queue import MessageBus
from nanobot.channels.manager import ChannelManager
from nanobot.config.loader import Config
from nanobot_gateway.backend_bridge import BackendBridge
from nanobot_gateway.config_loader import load_config_from_database, load_config_from_env


async def main():
    """Run nanobot gateway."""
    api_base = os.environ.get("BACKEND_API_BASE", "http://gateway:8000/api/v1")
    api_token = os.environ.get("BACKEND_API_TOKEN", "")
    
    logger.info(f"Starting nanobot gateway → {api_base}")
    
    logger.info("Loading channel configurations from database...")
    config_dict = load_config_from_database()
    
    if not config_dict:
        logger.info("No database config found, trying environment variables...")
        config_dict = load_config_from_env()
    
    if not config_dict or "channels" not in config_dict or not config_dict["channels"]:
        logger.warning("No channel configurations found")
        logger.info("Add integrations via API: POST /api/v1/config/integrations/{type}")
        logger.info("Or set environment variables: TELEGRAM_ENABLED=true TELEGRAM_BOT_TOKEN=...")
        logger.info("Waiting 60 seconds then exiting...")
        await asyncio.sleep(60)
        return
    
    channels = list(config_dict["channels"].keys())
    logger.info(f"Loaded configurations for: {', '.join(channels)}")
    
    logger.debug(f"Config dict structure: {config_dict}")
    config = Config(**config_dict)
    logger.info(f"Config object created - telegram enabled: {config.channels.telegram.enabled}")
    
    bus = MessageBus()
    
    bridge = BackendBridge(bus, api_base, api_token)
    
    channel_manager = ChannelManager(config, bus)
    
    logger.info("Starting backend bridge and channels...")
    
    await asyncio.gather(
        bridge.start(),
        channel_manager.start_all()
    )


if __name__ == "__main__":
    asyncio.run(main())
