"""Load nanobot configuration from database."""

import os
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.repositories.integration_credential_repo import IntegrationCredentialRepository


def load_config_from_database():
    """Load channel and LLM provider configurations from database."""
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
            
            # Load LLM providers from database
            llm_providers = repo.list_by_type("llm_provider")
            providers_config = {}
            default_provider = None
            default_model = None
            
            for cred in llm_providers:
                if cred.status != "valid":
                    continue
                
                # Decrypt API key
                api_key = repo.get_decrypted_token(cred.id)
                if not api_key:
                    continue
                
                # Extract metadata
                meta = cred.meta or {}
                provider_name = meta.get("provider", "openai")
                model = meta.get("model", "gpt-4")
                api_base = meta.get("api_base")
                extra_headers = meta.get("extra_headers")
                is_default = meta.get("is_default", False)
                
                # Build provider config
                providers_config[provider_name] = {
                    "api_key": api_key,
                    "api_base": api_base,
                    "extra_headers": extra_headers
                }
                
                if is_default:
                    default_provider = provider_name
                    default_model = f"{provider_name}/{model}"
                
                logger.info(f"Loaded LLM provider: {provider_name} (model: {model}, default: {is_default})")
            
            # Fallback to environment variables if no providers in database
            if not providers_config:
                logger.info("No LLM providers in database, using environment variables")
                providers_config = {
                    "openai": {
                        "api_key": os.environ.get("OPENAI_API_KEY", "")
                    },
                    "anthropic": {
                        "api_key": os.environ.get("ANTHROPIC_API_KEY", "")
                    },
                    "groq": {
                        "api_key": os.environ.get("GROQ_API_KEY", "")
                    }
                }
                default_provider = "auto"
                default_model = "gpt-4"
            
            config = {
                "channels": channels,
                "agents": {
                    "defaults": {
                        "provider": default_provider or "auto",
                        "model": default_model or "gpt-4"
                    }
                },
                "providers": providers_config
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
