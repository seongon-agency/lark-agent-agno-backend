"""
Minimal Feishu Bot with Agno AI
Simple chat bot - nothing more, nothing less
"""

import os
import json
import logging
import base64
import hashlib
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from agno.agent import Agent
from agno.models.openai import OpenAIChat

import lark_oapi as lark
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Feishu Agno Bot")

# Feishu client
feishu_client = lark.Client.builder() \
    .app_id(os.getenv("APP_ID")) \
    .app_secret(os.getenv("APP_SECRET")) \
    .build()


def decrypt_lark_data(encrypt_str: str, encrypt_key: str) -> dict:
    """Decrypt Lark encrypted webhook data using AES-256-CBC"""
    try:
        # Decode base64
        cipher_text = base64.b64decode(encrypt_str)

        # Create key from encrypt_key using SHA256
        key = hashlib.sha256(encrypt_key.encode()).digest()

        # Extract IV (first 16 bytes) and encrypted data
        iv = cipher_text[:16]
        encrypted_data = cipher_text[16:]

        # Decrypt using AES CBC mode
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)

        # Parse JSON
        return json.loads(decrypted.decode('utf-8'))
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise


def create_agent(session_id: str) -> Agent:
    """Create Agno agent for chat"""
    return Agent(
        model=OpenAIChat(
            id=os.getenv("OPENAI_MODEL", "gpt-4"),
            api_key=os.getenv("OPENAI_KEY"),
        ),
        description="You are a helpful AI assistant. Answer concisely and clearly.",
        markdown=True,
    )


def send_text_message(chat_id: str, text: str):
    """Send text message back to Feishu"""
    try:
        request = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(
                CreateMessageRequestBody.builder()
                .receive_id(chat_id)
                .msg_type("text")
                .content(json.dumps({"text": text}))
                .build()
            ).build()

        response = feishu_client.im.v1.message.create(request)

        if not response.success():
            logger.error(f"Failed to send message: {response.code} - {response.msg}")
        else:
            logger.info("Message sent successfully")

    except Exception as e:
        logger.error(f"Error sending message: {e}")


@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Feishu Agno Bot",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/webhook/card")
async def handle_card(request: Request):
    """Handle Feishu card action webhooks"""
    try:
        body = await request.body()
        body_str = body.decode('utf-8')

        logger.info(f"Received card webhook request: {body_str[:200]}")

        data = json.loads(body_str)

        # Check if encrypted
        if "encrypt" in data:
            encrypt_key = os.getenv("APP_ENCRYPT_KEY")
            if not encrypt_key:
                logger.error("APP_ENCRYPT_KEY not set but received encrypted payload")
                return {"error": "Encryption key not configured"}

            logger.info("Decrypting card webhook payload...")
            data = decrypt_lark_data(data["encrypt"], encrypt_key)
            logger.info(f"Decrypted card data: {json.dumps(data)[:200]}")

        # Handle URL verification challenge (v1 format)
        if "challenge" in data:
            challenge = data["challenge"]
            logger.info(f"Card webhook - Received challenge: {challenge}")
            return {"challenge": challenge}

        # Handle URL verification challenge (v2 format)
        if "type" in data and data["type"] == "url_verification":
            challenge = data.get("challenge", "")
            logger.info(f"Card webhook - Received v2 challenge: {challenge}")
            return {"challenge": challenge}

        # For now, just acknowledge card actions
        logger.info(f"Card action received: {data.get('action', {}).get('value', 'unknown')}")
        return {"success": True}

    except Exception as e:
        logger.error(f"Error handling card webhook: {e}", exc_info=True)
        logger.error(f"Request body: {body_str if 'body_str' in locals() else 'N/A'}")
        return {"error": str(e)}


@app.post("/webhook/event")
async def handle_event(request: Request):
    """Handle Feishu webhook events"""
    try:
        body = await request.body()
        body_str = body.decode('utf-8')

        logger.info(f"Received webhook request: {body_str[:200]}")

        data = json.loads(body_str)

        # Check if encrypted
        if "encrypt" in data:
            encrypt_key = os.getenv("APP_ENCRYPT_KEY")
            if not encrypt_key:
                logger.error("APP_ENCRYPT_KEY not set but received encrypted payload")
                return {"error": "Encryption key not configured"}

            logger.info("Decrypting webhook payload...")
            data = decrypt_lark_data(data["encrypt"], encrypt_key)
            logger.info(f"Decrypted data: {json.dumps(data)[:200]}")

        # Handle URL verification challenge (v1 format)
        if "challenge" in data:
            challenge = data["challenge"]
            logger.info(f"Received challenge: {challenge}")
            return {"challenge": challenge}

        # Handle URL verification challenge (v2 format)
        if "type" in data and data["type"] == "url_verification":
            challenge = data.get("challenge", "")
            logger.info(f"Received v2 challenge: {challenge}")
            return {"challenge": challenge}

        # Handle message events (v2 format)
        if "header" in data and "event" in data:
            event_type = data["header"].get("event_type")
            logger.info(f"Received event: {event_type}")

            # Only handle text messages
            if event_type == "im.message.receive_v1":
                await handle_message(data["event"])

        # Handle message events (v1 format - backward compatibility)
        elif "event" in data:
            event = data["event"]
            event_type = data.get("type") or event.get("type")
            logger.info(f"Received v1 event: {event_type}")

            if "message" in event:
                await handle_message(event)

        return {"success": True}

    except Exception as e:
        logger.error(f"Error handling event: {e}", exc_info=True)
        logger.error(f"Request body: {body_str if 'body_str' in locals() else 'N/A'}")
        return {"error": str(e)}


async def handle_message(event: dict):
    """Process incoming message and respond"""
    try:
        # Extract message info
        message = event.get("message", {})
        msg_type = message.get("message_type")
        chat_id = message.get("chat_id")
        content_str = message.get("content", "{}")

        # Only handle text messages
        if msg_type != "text":
            logger.info(f"Ignoring non-text message type: {msg_type}")
            return

        # Parse message content
        content = json.loads(content_str)
        user_text = content.get("text", "").strip()

        if not user_text:
            return

        logger.info(f"User message: {user_text}")

        # Use message_id as session_id for conversation continuity
        # In group chats, use chat_id; in private chats, use sender.sender_id
        sender_id = event.get("sender", {}).get("sender_id", {}).get("user_id", "")
        session_id = f"{chat_id}_{sender_id}"

        # Generate AI response using Agno
        agent = create_agent(session_id)
        response = agent.run(user_text)

        # Extract response text
        if hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)

        logger.info(f"AI response: {response_text[:100]}...")

        # Send response back to Feishu
        send_text_message(chat_id, response_text)

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        # Send error message to user
        try:
            send_text_message(chat_id, "Sorry, I encountered an error. Please try again.")
        except:
            pass


if __name__ == "__main__":
    # Validate configuration
    required_vars = ["APP_ID", "APP_SECRET", "OPENAI_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please set them in .env file")
        exit(1)

    logger.info("=" * 50)
    logger.info("Starting Feishu Agno Bot")
    logger.info("=" * 50)

    # Run server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
