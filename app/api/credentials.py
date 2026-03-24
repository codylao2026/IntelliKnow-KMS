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
async def list_credentials(db: AsyncSession = Depends(get_db)):
    """List all frontend credentials"""
    result = await db.execute(select(Credential))
    credentials = result.scalars().all()

    return {
        "items": [
            {
                "frontend_type": cred.frontend_type,
                "is_active": cred.is_active,
                "updated_at": cred.updated_at.isoformat(),
            }
            for cred in credentials
        ]
    }


@router.get("/{frontend_type}")
async def get_credential(frontend_type: str, db: AsyncSession = Depends(get_db)):
    """Get credential status (without sensitive data)"""
    result = await db.execute(
        select(Credential).where(Credential.frontend_type == frontend_type)
    )
    cred = result.scalar_one_or_none()

    if not cred:
        return {
            "frontend_type": frontend_type,
            "is_configured": False,
            "is_active": False,
        }

    return {
        "frontend_type": cred.frontend_type,
        "is_configured": True,
        "is_active": cred.is_active,
        "updated_at": cred.updated_at.isoformat(),
    }


@router.put("/{frontend_type}")
async def update_credential(
    frontend_type: str, data: CredentialUpdate, db: AsyncSession = Depends(get_db)
):
    """Update frontend credentials"""
    # Validate frontend type
    if frontend_type not in ["whatsapp", "teams", "feishu", "telegram"]:
        raise HTTPException(status_code=400, detail="Invalid frontend type")

    cipher = get_cipher()

    # Encrypt credentials
    try:
        cred_json = json.dumps(data.credentials)
        encrypted = cipher.encrypt(cred_json.encode()).decode()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Encryption error: {e}")

    # Check if exists
    result = await db.execute(
        select(Credential).where(Credential.frontend_type == frontend_type)
    )
    cred = result.scalar_one_or_none()

    if cred:
        cred.credentials_json = encrypted
        cred.is_active = True
    else:
        cred = Credential(
            frontend_type=frontend_type, credentials_json=encrypted, is_active=True
        )
        db.add(cred)

    await db.commit()

    return {"message": f"{frontend_type} credentials updated successfully"}


@router.delete("/{frontend_type}")
async def delete_credential(frontend_type: str, db: AsyncSession = Depends(get_db)):
    """Delete frontend credentials"""
    result = await db.execute(
        select(Credential).where(Credential.frontend_type == frontend_type)
    )
    cred = result.scalar_one_or_none()

    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")

    await db.delete(cred)
    await db.commit()

    return {"message": f"{frontend_type} credentials deleted successfully"}


@router.post("/{frontend_type}/test")
async def test_credential(frontend_type: str, db: AsyncSession = Depends(get_db)):
    """Test frontend connection"""
    # For telegram and feishu, check settings instead of database
    if frontend_type == "telegram":
        from app.services.frontend.telegram import get_telegram_client

        client = get_telegram_client()

        if not client.token:
            return {"success": False, "error": "Telegram not configured in settings"}

        if client._test_connection():
            return {"success": True, "message": "Telegram connection verified"}
        else:
            return {"success": False, "error": "Telegram connection failed"}

    elif frontend_type == "feishu":
        from app.services.frontend.feishu import get_feishu_client

        client = get_feishu_client()

        if not client.app_id or not client.app_secret:
            return {"success": False, "error": "Feishu not configured in settings"}

        return {"success": True, "message": "Feishu connection configured"}

    # For whatsapp and teams, check database
    result = await db.execute(
        select(Credential).where(Credential.frontend_type == frontend_type)
    )
    cred = result.scalar_one_or_none()

    if not cred:
        return {"success": False, "error": "Credentials not configured"}

    # Try to test connection
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

    return {"success": False, "error": "Unknown frontend type"}
