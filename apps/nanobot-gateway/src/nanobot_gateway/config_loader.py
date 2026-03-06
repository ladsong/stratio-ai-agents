"""Load nanobot configuration from database."""

import os
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.repositories.integration_credential_repo import IntegrationCredentialRepository


def load_config_from_database():
    """Load channel configurations from database."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set, cannot load credentials from database")
        return None
    
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        with Session(engine) as db:
            repo = IntegrationCredentialRepository(db)
            
            telegram_creds = repo.list_by_type("telegram")
            discord_creds = repo.list_by_type("discord")
            slack_creds = repo.list_by_type("slack")
            
            channels = {}
            
            if telegram_creds and len(telegram_creds) > 0:
                cred = telegram_creds[0]
                token = repo.get_decrypted_token(cred.id)
                if token:
                    allow_from = cred.meta.get("allowFrom", ["*"]) if cred.meta else ["*"]
                    channels["telegram"] = {
                        "enabled": True,
                        "token": token,
                        "allowFrom": allow_from
                    }
                    logger.info(f"Loaded Telegram config: {cred.display_name} (allowFrom: {allow_from})")
            
            if discord_creds and len(discord_creds) > 0:
                cred = discord_creds[0]
                token = repo.get_decrypted_token(cred.id)
                if token:
                    allow_from = cred.meta.get("allowFrom", ["*"]) if cred.meta else ["*"]
                    channels["discord"] = {
                        "enabled": True,
                        "token": token,
                        "allowFrom": allow_from
                    }
                    logger.info(f"Loaded Discord config: {cred.display_name} (allowFrom: {allow_from})")
            
            if slack_creds and len(slack_creds) > 0:
                cred = slack_creds[0]
                token = repo.get_decrypted_token(cred.id)
                if token:
                    allow_from = cred.meta.get("allowFrom", ["*"]) if cred.meta else ["*"]
                    channels["slack"] = {
                        "enabled": True,
                        "token": token,
                        "allowFrom": allow_from
                    }
                    logger.info(f"Loaded Slack config: {cred.display_name} (allowFrom: {allow_from})")
            
            config = {
                "channels": channels,
                "agents": {
                    "defaults": {
                        "provider": "openai",
                        "model": "gpt-4"
                    }
                },
                "providers": {
                    "openai": {
                        "api_key": ""
                    }
                }
            }
            
            return config
    
    except Exception as e:
        logger.error(f"Error loading config from database: {e}", exc_info=True)
        return None


def load_config_from_env():
    """Load channel configurations from environment variables (fallback)."""
    channels = {}
    
    telegram_enabled = os.environ.get("TELEGRAM_ENABLED", "false").lower() == "true"
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    
    if telegram_enabled and telegram_token:
        channels["telegram"] = {
            "enabled": True,
            "token": telegram_token,
            "allowFrom": ["*"]
        }
        logger.info("Loaded Telegram config from environment variables")
    
    discord_enabled = os.environ.get("DISCORD_ENABLED", "false").lower() == "true"
    discord_token = os.environ.get("DISCORD_BOT_TOKEN", "")
    
    if discord_enabled and discord_token:
        channels["discord"] = {
            "enabled": True,
            "token": discord_token,
            "allowFrom": ["*"]
        }
        logger.info("Loaded Discord config from environment variables")
    
    slack_enabled = os.environ.get("SLACK_ENABLED", "false").lower() == "true"
    slack_token = os.environ.get("SLACK_BOT_TOKEN", "")
    slack_app_token = os.environ.get("SLACK_APP_TOKEN", "")
    
    if slack_enabled and slack_token:
        channels["slack"] = {
            "enabled": True,
            "token": slack_token,
            "appToken": slack_app_token,
            "allowFrom": ["*"]
        }
        logger.info("Loaded Slack config from environment variables")
    
    if not channels:
        return None
    
    return {
        "channels": channels,
        "agents": {
            "defaults": {
                "provider": "openai",
                "model": "gpt-4"
            }
        },
        "providers": {
            "openai": {
                "api_key": ""
            }
        }
    }
