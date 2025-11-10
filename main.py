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
from agno.models.anthropic import Claude
from agno.tools.mcp import MultiMCPTools

# Larksuite SDK Imports
import lark_oapi as lark
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

# Database
from agno.db.postgres import PostgresDb

load_dotenv()

# Setup logging first
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Get Supabase credentials from environment
SUPABASE_PROJECT = os.getenv("SUPABASE_PROJECT")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")
SUPABASE_REGION = os.getenv("SUPABASE_REGION", "ap-southeast-1")

# Initialize database
SUPABASE_DB_URL = f"postgresql://postgres.{SUPABASE_PROJECT}:{SUPABASE_PASSWORD}@aws-1-{SUPABASE_REGION}.pooler.supabase.com:5432/postgres"
db = PostgresDb(db_url=SUPABASE_DB_URL)
logger.info(f"Using Supabase PostgreSQL (region: {SUPABASE_REGION})")

# Message deduplication
processed_messages = {}

# Global MCP and agent - will be initialized in setup function
lark_mcp = None
lark_base_agent_template = None


def setup_agent():
    """Initialize MCP tools and agent template - called once at startup"""
    global lark_mcp, lark_base_agent_template

    logger.info("Setting up Lark MCP tools...")

    # Initialize MCP tools
    lark_mcp = MultiMCPTools(
        commands=[
            f"npx -y @larksuiteoapi/lark-mcp mcp -a {os.getenv('APP_ID')} -s {os.getenv('APP_SECRET')} -d https://open.larksuite.com/ --oauth"
        ],
        timeout_seconds=120,
        allow_partial_failure=True
    )

    # Give it a moment to initialize
    import time
    logger.info("Waiting 5 seconds for MCP to fully initialize...")
    time.sleep(5)

    # Debug: Check what we got
    logger.info(f"MCP object type: {type(lark_mcp)}")
    logger.info(f"MCP has 'functions': {hasattr(lark_mcp, 'functions')}")
    logger.info(f"MCP has 'tools': {hasattr(lark_mcp, 'tools')}")

    if hasattr(lark_mcp, 'functions'):
        logger.info(f"MCP.functions type: {type(lark_mcp.functions)}")
        logger.info(f"MCP.functions value: {lark_mcp.functions}")
        if lark_mcp.functions:
            for func in lark_mcp.functions:
                logger.info(f"  - Tool: {func.name if hasattr(func, 'name') else func}")

    if hasattr(lark_mcp, 'tools'):
        logger.info(f"MCP.tools type: {type(lark_mcp.tools)}")
        logger.info(f"MCP.tools value: {lark_mcp.tools}")

    # Check all attributes
    logger.info(f"MCP attributes: {dir(lark_mcp)}")

    logger.info("✓ Lark MCP tools setup complete")


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
    feishu_client = lark.Client.builder() \
        .app_id(os.getenv("APP_ID")) \
        .app_secret(os.getenv("APP_SECRET")) \
        .build()

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


# Create FastAPI app
app = FastAPI(title="Lark Agno Bot")


@app.on_event("startup")
async def startup_event():
    """Initialize MCP tools when the app starts"""
    setup_agent()


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

        # Get session info
        sender = event.get("sender", {}).get("sender_id", {}).get("user_id", "")
        chat_id = msg.get("chat_id")
        session = f"{chat_id}_{sender}"

        # Create agent for this session (MCP tools already initialized)
        agent = Agent(
            session_id=session,
            name="Lark Task Management Agent",
            role="Manage Lark Tasks within a Lark Base using Lark MCP",
            model=Claude(
                id="claude-sonnet-4-5-20250929",
                api_key=os.getenv("ANTHROPIC_API_KEY"),
            ),
            description="You are a task management assistant with REAL access to Lark Base via MCP tools. You can actually create, read, update, and delete tasks.",
            instructions=[
                "IMPORTANT: You have actual, working Lark MCP tools available. Use them to interact with Lark Base.",
                f"The Lark Base ID is: {os.getenv('LARK_BASE_ID', 'Q9gVbS1j1anjh7sP56Dln1xFgdG')}",
                "When the user asks to create, list, update, or delete tasks - USE THE MCP TOOLS to actually do it.",
                "Do NOT say you cannot access Lark Base - you can and should use the tools provided.",
                "After using a tool, describe what action was taken based on the tool's response.",
                "If a tool call fails, explain the error to the user."
            ],
            tools=[lark_mcp] if lark_mcp else [],
            db=db,
            add_history_to_context=True,
            read_chat_history=True,
            num_history_runs=3,
            search_session_history=True,
            markdown=True,
            debug_mode=True,
            cache_session=True
        )

        logger.info(f"Using session: {session}")
        response = agent.run(text)
        reply = response.content if hasattr(response, 'content') else str(response)

        logger.info(f"AI: {reply[:80]}...")
        send_message(chat_id, reply)

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            send_message(msg.get("chat_id"), "Sorry, an error occurred.")
        except:
            pass


if __name__ == "__main__":
    required = ["APP_ID", "APP_SECRET", "ANTHROPIC_API_KEY"]
    missing = [v for v in required if not os.getenv(v)]

    if missing:
        logger.error(f"Missing env vars: {', '.join(missing)}")
        exit(1)

    logger.info("Starting Lark Agno Bot")
    uvicorn.run("main:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8000")), reload=False)
