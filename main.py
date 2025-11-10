# Basic imports
import os
import json
import logging
import base64
import hashlib
from datetime import datetime, timedelta

# FastAPI and Encryption
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# Agno Imports
from agno.agent import Agent
# from agno.models.openai import OpenAIChat
from agno.models.xai import xAI
from agno.tools.mcp import MultiMCPTools


# Larksuite SDK Imports
import lark_oapi as lark
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

# Storage (for agent sessions)
from agno.storage.postgres import PostgresStorage

load_dotenv()

# Setup logging first
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Get Supabase credentials from environment
SUPABASE_PROJECT = os.getenv("SUPABASE_PROJECT")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")
SUPABASE_REGION = os.getenv("SUPABASE_REGION", "ap-southeast-1")  # Default region

# Initialize storage - using Supabase connection pooler for Railway
# Use Supabase connection pooler (required for Railway/serverless)
# Format: postgresql://postgres.{PROJECT_REF}:{PASSWORD}@aws-0-{REGION}.pooler.supabase.com:6543/postgres
SUPABASE_DB_URL = f"postgresql://postgres.{SUPABASE_PROJECT}:{SUPABASE_PASSWORD}@aws-1-{SUPABASE_REGION}.pooler.supabase.com:5432/postgres"
storage = PostgresStorage(
    table_name="agent_sessions",
    db_url=SUPABASE_DB_URL
)
logger.info(f"Using Supabase PostgreSQL storage (region: {SUPABASE_REGION})")
logger.info("Agent sessions will be stored in 'agent_sessions' table")


app = FastAPI(title="Lark Agno Bot")

feishu_client = lark.Client.builder() \
    .app_id(os.getenv("APP_ID")) \
    .app_secret(os.getenv("APP_SECRET")) \
    .build()

# Message deduplication
processed_messages = {}


def is_duplicate(msg_id: str) -> bool:
    now = datetime.now()
    # Clean old entries
    expired = [k for k, v in processed_messages.items() if now - v > timedelta(minutes=30)]
    for k in expired:
        del processed_messages[k]

    if msg_id in processed_messages:
        return True
    processed_messages[msg_id] = now
    return False


def decrypt(encrypted: str) -> dict:
    key = hashlib.sha256(os.getenv("APP_ENCRYPT_KEY").encode()).digest()
    data = base64.b64decode(encrypted)
    cipher = AES.new(key, AES.MODE_CBC, data[:16])
    return json.loads(unpad(cipher.decrypt(data[16:]), AES.block_size))


def send_message(chat_id: str, text: str):
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
    if response.success():
        logger.info("Message sent")
    else:
        logger.error(f"Send failed: {response.code}")


@app.get("/")
async def health():
    return {"service": "Feishu Agno Bot", "status": "running"}


@app.post("/webhook/card")
async def webhook_card(request: Request):
    body = await request.body()
    data = json.loads(body)

    if "encrypt" in data:
        data = decrypt(data["encrypt"])

    if "challenge" in data:
        return {"challenge": data["challenge"]}

    return {"success": True}


@app.post("/webhook/event")
async def webhook_event(request: Request):
    body = await request.body()
    data = json.loads(body)

    if "encrypt" in data:
        data = decrypt(data["encrypt"])

    if "challenge" in data:
        return {"challenge": data["challenge"]}

    if "header" in data and data["header"].get("event_type") == "im.message.receive_v1":
        await process_message(data["event"])

    return {"success": True}


async def process_message(event: dict):
    try:
        msg = event.get("message", {})
        msg_id = msg.get("message_id")

        if is_duplicate(msg_id):
            return

        if msg.get("message_type") != "text":
            return

        content = json.loads(msg.get("content", "{}"))
        text = content.get("text", "").strip()

        if not text:
            return

        logger.info(f"User: {text}")

        # Create AI agent
        sender = event.get("sender", {}).get("sender_id", {}).get("user_id", "")
        chat_id = msg.get("chat_id")
        session = f"{chat_id}_{sender}"

        # Configure MCP
        lark_mcp = MultiMCPTools(
            commands=[
                f"npx -y @larksuiteoapi/lark-mcp mcp -a {os.getenv('APP_ID')} -s {os.getenv('APP_SECRET')} -d https://open.larksuite.com/ --oauth"
            ],
            timeout_seconds=60,
            allow_partial_failure=True
        )

        lark_base_agent = Agent(
            session_id=session,
            name="Lark Task Management Agent",
            role="Manage Lark Tasks within a Lark Base using Lark MCP",
            model=xAI(
                id="grok-2-1212",
                api_key=os.getenv("XAI_API_KEY"),
            ),
            description="You are a task management assistant that helps users manage their tasks in Lark Base using Lark MCP. You can create, update, delete, and retrieve tasks based on user requests.",
            instructions=[
                f"Use the Lark MCP tool to interact with Lark Base. The specific base id is '{os.getenv('LARK_BASE_ID', 'Q9gVbS1j1anjh7sP56Dln1xFgdG')}'.",
                "When creating or updating tasks, ensure to include all necessary fields such as title, description, due date, and status.",
                "Always confirm actions with the user before making changes to their tasks.",
                "Provide clear and concise responses to the user regarding their task management requests."
            ],
            tools=[lark_mcp],
            storage=storage,
            add_history_to_context=True,
            read_chat_history=True,
            num_history_runs=3,
            search_session_history=True,
            markdown=True,
            debug_mode=True
        )

        logger.info(f"Using session: {session}")
        response = lark_base_agent.run(text)
        reply = response.content if hasattr(response, 'content') else str(response)

        logger.info(f"AI: {reply[:80]}...")
        send_message(chat_id, reply)

    except Exception as e:
        logger.error(f"Error: {e}")
        try:
            send_message(msg.get("chat_id"), "Sorry, an error occurred.")
        except:
            pass


if __name__ == "__main__":
    required = ["APP_ID", "APP_SECRET", "XAI_API_KEY"]
    missing = [v for v in required if not os.getenv(v)]

    if missing:
        logger.error(f"Missing env vars: {', '.join(missing)}")
        exit(1)

    logger.info("Starting Lark Agno Bot")
    uvicorn.run("main:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8000")), reload=True)
