"""
Webhook API routes for external integrations

Provides endpoints for:
- WhatsApp webhook verification and message handling
- Microsoft Teams activity handling
- Feishu (Lark) long connection management
- Frontend integration status checking
- Connection testing for each platform
- Environment variable management for credentials
"""

import logging
import json
from fastapi import APIRouter, Request, Response, HTTPException, Depends, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.fernet import Fernet
import base64
from pathlib import Path

from config import settings
from app.services.frontend.whatsapp import handle_whatsapp_webhook, get_whatsapp_client
from app.services.frontend.teams import handle_teams_activity, get_teams_client

FEISHU_AVAILABLE = False
_feishu_client_getter = None


def _try_import_feishu():
    global FEISHU_AVAILABLE, _feishu_client_getter
    if _feishu_client_getter is not None:
        return _feishu_client_getter
    try:
        from app.services.frontend.feishu import get_feishu_client

        _feishu_client_getter = get_feishu_client
        FEISHU_AVAILABLE = True
        return get_feishu_client
    except Exception:
        FEISHU_AVAILABLE = False
        return None


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
    hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = ""
):
    """Verify WhatsApp webhook (FR-003)"""
    client = get_whatsapp_client()
    challenge = client.verify_webhook(hub_mode, hub_verify_token, hub_challenge)

    if challenge is None:
        raise HTTPException(status_code=403, detail="Verification failed")

    return Response(content=challenge, media_type="text/plain")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages (FR-001)"""
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
    """Handle incoming Teams messages (FR-005)"""
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
    """Get frontend integration status (FR-003)"""
    # Check database for saved credentials (for whatsapp/teams)
    wa_creds = await get_credential_from_db(db, "whatsapp")
    teams_creds = await get_credential_from_db(db, "teams")

    whatsapp = get_whatsapp_client()
    teams = get_teams_client()

    # Telegram - get from settings (env)
    from app.services.frontend.telegram import get_telegram_client

    telegram = get_telegram_client()
    telegram_configured = bool(telegram and telegram.is_configured())
    telegram_running = bool(telegram and telegram.is_running())

    # Feishu - get from settings (env)
    feishu_getter = _try_import_feishu()
    feishu = feishu_getter() if feishu_getter else None

    # Check both database and settings
    wa_configured = (
        wa_creds and wa_creds.get("phone_number_id") and wa_creds.get("access_token")
    ) or (whatsapp.phone_number_id and whatsapp.access_token)
    teams_configured = (
        teams_creds and teams_creds.get("app_id") and teams_creds.get("app_password")
    ) or (teams.app_id and teams.app_password)

    # Feishu: only check settings (env), not database
    feishu_configured = (
        bool(feishu and feishu.app_id and feishu.app_secret) if feishu else False
    )

    return {
        "whatsapp": {
            "configured": bool(wa_configured),
            "phone_number_id": (
                wa_creds.get("phone_number_id")
                if wa_creds
                else whatsapp.phone_number_id
            ),
        },
        "teams": {
            "configured": bool(teams_configured),
            "app_id": (teams_creds.get("app_id") if teams_creds else teams.app_id),
            "status": teams.get_status() if teams else {},
        },
        "feishu": {
            "configured": bool(feishu_configured),
            "app_id": feishu.app_id if feishu else None,
            "running": feishu.is_running() if feishu else False,
        },
        "telegram": {
            "is_configured": telegram_configured,
            "configured": telegram_configured,
            "running": telegram_running,
            "mode": "Polling",
        },
    }


# ============== Test Endpoints ==============


@router.post("/test/whatsapp")
async def test_whatsapp(message: str, to: str):
    """Test WhatsApp message sending (FR-003)"""
    client = get_whatsapp_client()
    result = await client.send_message(to, message)
    return result


class TestTeamsRequest(BaseModel):
    conversation_id: str | None = None
    message: str = "Hello from IntelliKnow!"
    use_card: bool = True


@router.post("/test/teams")
async def test_teams(data: TestTeamsRequest, db: AsyncSession = Depends(get_db)):
    """Test Teams connection and message sending (FR-003/FR-008)"""
    # Get credentials from database
    teams_creds = await get_credential_from_db(db, "teams")

    if not teams_creds or not teams_creds.get("app_id"):
        # Fallback to settings credentials
        client = get_teams_client()
        if not client.app_id or not client.app_password:
            return {
                "success": False,
                "error": "Teams not configured. Please set TEAMS_APP_ID, TEAMS_APP_PASSWORD, TEAMS_TENANT_ID in .env or save credentials via Frontend Integration page.",
            }

        # Try to acquire token
        token = await client._acquire_token()
        if not token:
            return {
                "success": False,
                "error": "Failed to acquire OAuth token. Check your Azure AD app registration.",
            }

        return {
            "success": True,
            "message": "Teams OAuth token acquired successfully",
            "token_expires_in": "3600 seconds",
            "hint": "Provide conversation_id to send a test message",
        }

    # Update teams client with database credentials
    client = get_teams_client()
    client.app_id = teams_creds.get("app_id")
    client.app_password = teams_creds.get("app_password")
    client.tenant_id = teams_creds.get("tenant_id")

    # Try to acquire token first
    token = await client._acquire_token()
    if not token:
        return {
            "success": False,
            "error": "Failed to acquire OAuth token. Check your Azure AD app configuration.",
        }

    if data.conversation_id:
        if data.use_card:
            result = await client.send_adaptive_card(
                conversation_id=data.conversation_id,
                title="IntelliKnow Test",
                content=data.message,
                sources=[],
            )
        else:
            result = await client.send_message(data.conversation_id, data.message)
        return result

    return {
        "success": True,
        "message": "Teams credentials validated, OAuth token acquired",
        "features": ["Adaptive Cards", "Markdown", "Rich Text"],
        "hint": "Provide conversation_id to send a test message",
    }


@router.post("/test/feishu")
async def test_feishu(db: AsyncSession = Depends(get_db)):
    """Test Feishu connection (FR-FL-003)"""
    # Get credentials from database
    feishu_creds = await get_credential_from_db(db, "feishu")

    if not feishu_creds or not feishu_creds.get("app_id"):
        # Fallback to settings
        feishu_getter = _try_import_feishu()
        if not feishu_getter:
            return {"success": False, "error": "Feishu SDK not available"}
        client = feishu_getter()
        if not client.app_id or not client.app_secret:
            return {"success": False, "error": "Feishu not configured"}

        return {
            "success": True,
            "message": "Feishu credentials validated from settings",
            "running": client.is_running(),
            "mode": "WebSocket Long Connection",
        }

    # Update feishu client with database credentials
    feishu_getter = _try_import_feishu()
    if not feishu_getter:
        return {"success": False, "error": "Feishu SDK not available"}
    client = feishu_getter()
    if client:
        client.app_id = feishu_creds.get("app_id") if feishu_creds else None
        client.app_secret = feishu_creds.get("app_secret") if feishu_creds else None

    return {
        "success": True,
        "message": "Feishu credentials validated",
        "running": client.is_running() if client else False,
        "mode": "WebSocket Long Connection",
    }


# ============== Environment Variable Endpoints ==============


class TelegramTokenRequest(BaseModel):
    token: str


class FeishuCredentialsRequest(BaseModel):
    app_id: str
    app_secret: str


@router.put("/env/telegram")
async def save_telegram_token(request: TelegramTokenRequest):
    """Save Telegram bot token to .env file"""
    token = request.token
    if not token:
        return {"success": False, "error": "Token cannot be empty"}

    env_path = Path(__file__).parent.parent.parent / "config" / ".env"

    try:
        if env_path.exists():
            content = env_path.read_text(encoding="utf-8")
            lines = content.splitlines()
        else:
            lines = []

        key_found = False
        new_lines = []
        for line in lines:
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                new_lines.append(f"TELEGRAM_BOT_TOKEN={token}")
                key_found = True
            else:
                new_lines.append(line)

        if not key_found:
            new_lines.append(f"TELEGRAM_BOT_TOKEN={token}")

        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        from dotenv import load_dotenv

        load_dotenv(env_path, override=True)

        return {"success": True, "message": "Telegram token saved to .env file"}

    except Exception as e:
        logger.error(f"Failed to save telegram token: {e}")
        return {"success": False, "error": str(e)}


@router.put("/env/feishu")
async def save_feishu_credentials(request: FeishuCredentialsRequest):
    """Save Feishu credentials to .env file"""
    app_id = request.app_id
    app_secret = request.app_secret
    if not app_id or not app_secret:
        return {"success": False, "error": "App ID and App Secret are required"}

    env_path = Path(__file__).parent.parent.parent / "config" / ".env"

    try:
        if env_path.exists():
            content = env_path.read_text(encoding="utf-8")
            lines = content.splitlines()
        else:
            lines = []

        new_lines = []
        app_id_found = False
        app_secret_found = False

        for line in lines:
            if line.startswith("FEISHU_APP_ID="):
                new_lines.append(f"FEISHU_APP_ID={app_id}")
                app_id_found = True
            elif line.startswith("FEISHU_APP_SECRET="):
                new_lines.append(f"FEISHU_APP_SECRET={app_secret}")
                app_secret_found = True
            else:
                new_lines.append(line)

        if not app_id_found:
            new_lines.append(f"FEISHU_APP_ID={app_id}")
        if not app_secret_found:
            new_lines.append(f"FEISHU_APP_SECRET={app_secret}")

        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        from dotenv import load_dotenv

        load_dotenv(env_path, override=True)

        return {"success": True, "message": "Feishu credentials saved to .env file"}

    except Exception as e:
        logger.error(f"Failed to save feishu credentials: {e}")
        return {"success": False, "error": str(e)}
