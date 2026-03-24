"""
Credential API routes
"""

import json
import logging
import base64
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.fernet import Fernet
from pydantic import BaseModel

from config import settings
from app.utils.database import get_db
from app.models.database import Credential

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Fernet cipher
_cipher = None


def get_cipher():
    """Get Fernet cipher for encryption/decryption"""
    global _cipher
    if _cipher is None:
        hex_key = settings.ENCRYPTION_KEY[:64]
        key_bytes = bytes.fromhex(hex_key)
        key_b64 = base64.urlsafe_b64encode(key_bytes)
        _cipher = Fernet(key_b64)
    return _cipher


class CredentialUpdate(BaseModel):
    credentials: dict


@router.get("")
async def list_credentials():
    """List all frontend credentials (from .env)"""
    from app.utils.env_manager import get_all_credentials

    all_creds = get_all_credentials()

    frontend_types = ["whatsapp", "teams", "feishu", "telegram"]
    items = []

    for ft in frontend_types:
        is_configured = ft in all_creds and bool(all_creds[ft])
        items.append(
            {
                "frontend_type": ft,
                "is_active": is_configured,
            }
        )

    return {"items": items}


@router.get("/{frontend_type}")
async def get_credential(frontend_type: str):
    """Get credential status (without sensitive data)"""
    from app.utils.env_manager import read_env_var

    if frontend_type == "feishu":
        app_id = read_env_var("FEISHU_APP_ID", "")
        is_configured = bool(app_id)
    elif frontend_type == "telegram":
        token = read_env_var("TELEGRAM_BOT_TOKEN", "")
        is_configured = bool(token)
    elif frontend_type == "whatsapp":
        phone_id = read_env_var("WHATSAPP_PHONE_NUMBER_ID", "")
        is_configured = bool(phone_id)
    elif frontend_type == "teams":
        app_id = read_env_var("TEAMS_APP_ID", "")
        is_configured = bool(app_id)
    else:
        is_configured = False

    return {
        "frontend_type": frontend_type,
        "is_configured": is_configured,
        "is_active": is_configured,
    }


@router.put("/{frontend_type}")
async def update_credential(frontend_type: str, data: CredentialUpdate):
    """Update frontend credentials (save to .env file)"""
    from app.utils.env_manager import save_env_var

    # Validate frontend type
    if frontend_type not in ["whatsapp", "teams", "feishu", "telegram"]:
        raise HTTPException(status_code=400, detail="Invalid frontend type")

    creds = data.credentials

    if frontend_type == "feishu":
        app_id = creds.get("app_id", "")
        app_secret = creds.get("app_secret", "")
        if not app_id or not app_secret:
            raise HTTPException(
                status_code=400, detail="app_id and app_secret required"
            )

        save_env_var("FEISHU_APP_ID", app_id)
        save_env_var("FEISHU_APP_SECRET", app_secret)

    elif frontend_type == "telegram":
        bot_token = creds.get("bot_token", "")
        if not bot_token:
            raise HTTPException(status_code=400, detail="bot_token required")

        save_env_var("TELEGRAM_BOT_TOKEN", bot_token)

    elif frontend_type == "whatsapp":
        phone_number_id = creds.get("phone_number_id", "")
        access_token = creds.get("access_token", "")
        if not phone_number_id or not access_token:
            raise HTTPException(
                status_code=400, detail="phone_number_id and access_token required"
            )

        save_env_var("WHATSAPP_PHONE_NUMBER_ID", phone_number_id)
        save_env_var("WHATSAPP_ACCESS_TOKEN", access_token)

    elif frontend_type == "teams":
        app_id = creds.get("app_id", "")
        app_password = creds.get("app_password", "")
        tenant_id = creds.get("tenant_id", "")
        if not app_id or not app_password:
            raise HTTPException(
                status_code=400, detail="app_id and app_password required"
            )

        save_env_var("TEAMS_APP_ID", app_id)
        save_env_var("TEAMS_APP_PASSWORD", app_password)
        if tenant_id:
            save_env_var("TEAMS_TENANT_ID", tenant_id)

    return {"message": f"{frontend_type} credentials saved to .env"}


@router.delete("/{frontend_type}")
async def delete_credential(frontend_type: str):
    """Delete frontend credentials"""
    from app.utils.env_manager import save_env_var

    if frontend_type not in ["whatsapp", "teams", "feishu", "telegram"]:
        raise HTTPException(status_code=400, detail="Invalid frontend type")

    if frontend_type == "feishu":
        save_env_var("FEISHU_APP_ID", "")
        save_env_var("FEISHU_APP_SECRET", "")
    elif frontend_type == "telegram":
        save_env_var("TELEGRAM_BOT_TOKEN", "")
    elif frontend_type == "whatsapp":
        save_env_var("WHATSAPP_PHONE_NUMBER_ID", "")
        save_env_var("WHATSAPP_ACCESS_TOKEN", "")
    elif frontend_type == "teams":
        save_env_var("TEAMS_APP_ID", "")
        save_env_var("TEAMS_APP_PASSWORD", "")

    return {"message": f"{frontend_type} credentials deleted"}


@router.post("/{frontend_type}/test")
async def test_credential(frontend_type: str):
    """Test frontend connection"""
    if frontend_type == "whatsapp":
        from app.services.frontend.whatsapp import get_whatsapp_client

        client = get_whatsapp_client()

        if not client.phone_number_id or not client.access_token:
            return {"success": False, "error": "WhatsApp not configured in settings"}

        return {"success": True, "message": "WhatsApp connection configured"}

    elif frontend_type == "teams":
        from app.services.frontend.teams import get_teams_client

        client = get_teams_client()

        if not client.app_id or not client.app_password:
            return {"success": False, "error": "Teams not configured in settings"}

        return {"success": True, "message": "Teams connection configured"}

    elif frontend_type == "feishu":
        from app.services.frontend.feishu import get_feishu_client

        client = get_feishu_client()

        if not client.app_id or not client.app_secret:
            return {"success": False, "error": "Feishu not configured in settings"}

        return {
            "success": True,
            "message": "Feishu connection configured",
            "running": client.is_running(),
        }

    elif frontend_type == "telegram":
        from app.services.frontend.telegram import get_telegram_client
        from config import settings

        client = get_telegram_client()

        if not client.is_configured():
            return {"success": False, "error": "Telegram not configured"}

        try:
            test_chat_id = int(settings.TELEGRAM_TEST_CHAT_ID)
            client.test_connection(test_chat_id)
            return {"success": True, "message": "Telegram test message sent"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "Unknown frontend type"}
