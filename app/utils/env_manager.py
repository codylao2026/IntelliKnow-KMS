"""
.env File Manager - Read and write credentials to .env file
"""

import os
import re
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ENV_FILE_PATH = Path(__file__).parent.parent / "config" / ".env"


def load_env():
    """Load .env file into environment variables"""
    if ENV_FILE_PATH.exists():
        load_dotenv(ENV_FILE_PATH, override=True)


def save_env_var(key: str, value: str) -> bool:
    """
    Save or update an environment variable in .env file

    Args:
        key: Environment variable name (e.g., "FEISHU_APP_ID")
        value: Environment variable value

    Returns:
        True if successful, False otherwise
    """
    try:
        env_path = ENV_FILE_PATH

        # Read existing content
        if env_path.exists():
            content = env_path.read_text(encoding="utf-8")
            lines = content.splitlines()
        else:
            lines = []

        # Check if key exists
        key_pattern = re.compile(f"^{re.escape(key)}=", re.MULTILINE)
        key_found = False

        new_lines = []
        for line in lines:
            if key_pattern.match(line):
                new_lines.append(f"{key}={value}")
                key_found = True
            else:
                new_lines.append(line)

        if not key_found:
            new_lines.append(f"{key}={value}")

        # Write back
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        # Reload environment variables
        load_dotenv(env_path, override=True)

        logger.info(f"Saved {key} to .env file")
        return True

    except Exception as e:
        logger.error(f"Failed to save {key} to .env: {e}")
        return False


def read_env_var(key: str, default: str = "") -> str:
    """
    Read an environment variable

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)


def get_all_credentials() -> dict:
    """
    Get all frontend credentials

    Returns:
        Dict with frontend type as key and credentials as value
    """
    credentials = {}

    # Feishu
    feishu_id = os.getenv("FEISHU_APP_ID", "")
    feishu_secret = os.getenv("FEISHU_APP_SECRET", "")
    if feishu_id and feishu_secret:
        credentials["feishu"] = {"app_id": feishu_id, "app_secret": feishu_secret}

    # Telegram
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if telegram_token:
        credentials["telegram"] = {"bot_token": telegram_token}

    return credentials
