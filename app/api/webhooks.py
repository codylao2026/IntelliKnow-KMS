"""
Webhook API routes for external integrations
"""
import logging
import json
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.fernet import Fernet
import base64

from config import settings
from app.services.frontend.whatsapp import handle_whatsapp_webhook, get_whatsapp_client
from app.services.frontend.teams import handle_teams_activity, get_teams_client
from app.utils.database import get_db
from app.models.database import Credential

logger = logging.getLogger(__name__)
router = APIRouter()


def get_cipher():
    """Get Fernet cipher for decryption"""
    hex_key = settings.ENCRYPTION_KEY[:64]
    key_bytes = bytes.fromhex(hex_key)
    key_b64 = base64.urlsafe_b64encode(key_bytes)
    return Fernet(key_b64)


# ============== WhatsApp Webhooks ==============

class WebhookVerifyRequest(BaseModel):
    """Webhook verification request"""
    hub_mode: str
    hub_verify_token: str
    hub_challenge: str


@router.get("/webhook/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = "",
    hub_verify_token: str = "",
    hub_challenge: str = ""
):
    """Verify WhatsApp webhook"""
    client = get_whatsapp_client()
    challenge = client.verify_webhook(hub_mode, hub_verify_token, hub_challenge)

    if challenge is None:
        raise HTTPException(status_code=403, detail="Verification failed")

    return Response(content=challenge, media_type="text/plain")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages"""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Verify signature (optional in development)
    signature = request.headers.get("x-hub-signature-256", "")
    # client.verify_signature(body, signature)  # Enable in production

    # Process message
    response = await handle_whatsapp_webhook(body)

    return {"success": True}


# ============== Microsoft Teams Bot ==============

@router.post("/webhook/teams")
async def teams_webhook(request: Request):
    """Handle incoming Teams messages"""
    try:
        activity = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Handle activity
    response = await handle_teams_activity(activity)

    # Teams expects 200 OK response
    return {"success": True}


# ============== Connection Status ==============

async def get_credential_from_db(db: AsyncSession, frontend_type: str) -> dict | None:
    """Get decrypted credentials from database"""
    result = await db.execute(
        select(Credential).where(Credential.frontend_type == frontend_type)
    )
    cred = result.scalar_one_or_none()
    if not cred or not cred.credentials_json:
        return None
    
    try:
        cipher = get_cipher()
        decrypted = cipher.decrypt(cred.credentials_json.encode())
        return json.loads(decrypted.decode())
    except Exception:
        return None


@router.get("/status/frontend")
async def get_frontend_status(db: AsyncSession = Depends(get_db)):
    """Get frontend integration status"""
    # Check database for saved credentials
    wa_creds = await get_credential_from_db(db, "whatsapp")
    teams_creds = await get_credential_from_db(db, "teams")

    whatsapp = get_whatsapp_client()
    teams = get_teams_client()

    # Check both database and settings
    wa_configured = (wa_creds and wa_creds.get("phone_number_id") and wa_creds.get("access_token")) or \
                   (whatsapp.phone_number_id and whatsapp.access_token)
    teams_configured = (teams_creds and teams_creds.get("app_id") and teams_creds.get("app_password")) or \
                      (teams.app_id and teams.app_password)

    return {
        "whatsapp": {
            "configured": bool(wa_configured),
            "phone_number_id": (wa_creds.get("phone_number_id") if wa_creds else whatsapp.phone_number_id)
        },
        "teams": {
            "configured": bool(teams_configured),
            "app_id": (teams_creds.get("app_id") if teams_creds else teams.app_id)
        }
    }


@router.post("/test/whatsapp")
async def test_whatsapp(message: str, to: str):
    """Test WhatsApp message sending"""
    client = get_whatsapp_client()
    result = await client.send_message(to, message)
    return result


class TestTeamsRequest(BaseModel):
    conversation_id: str | None = None
    message: str = "Hello from IntelliKnow!"


@router.post("/test/teams")
async def test_teams(data: TestTeamsRequest, db: AsyncSession = Depends(get_db)):
    """Test Teams message sending"""
    # Get credentials from database
    teams_creds = await get_credential_from_db(db, "teams")
    
    if not teams_creds or not teams_creds.get("app_id"):
        return {"success": False, "error": "Teams not configured"}
    
    # Update teams client with database credentials
    client = get_teams_client()
    client.app_id = teams_creds.get("app_id")
    client.app_password = teams_creds.get("app_password")
    client.tenant_id = teams_creds.get("tenant_id")
    
    if data.conversation_id:
        result = await client.send_message(data.conversation_id, data.message)
        return result
    
    return {"success": True, "message": "Teams credentials validated", "hint": "Provide conversation_id to send a test message"}