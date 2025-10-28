"""
Agno AI Agent Service for Feishu Bot
A simple FastAPI service that provides AI chat capabilities using Agno framework
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.agent.sqlite import SqlAgentStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agno AI Agent Service",
    description="AI Agent service for Feishu chatbot with memory and context",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: Optional[List[Message]] = []
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str
    timestamp: str

# Agent storage for persistence
STORAGE_DIR = os.getenv("STORAGE_DIR", "./data")
os.makedirs(STORAGE_DIR, exist_ok=True)

agent_storage = SqlAgentStorage(
    table_name="agent_sessions",
    db_file=f"{STORAGE_DIR}/agents.db"
)

def create_agent(session_id: str, system_prompt: Optional[str] = None) -> Agent:
    """
    Create an Agno agent with OpenAI model and session storage

    Args:
        session_id: Unique identifier for the chat session
        system_prompt: Optional custom system prompt

    Returns:
        Configured Agent instance
    """
    default_prompt = """You are SEONGON AI, an AI Agent developed by SEONGON, a Vietnamese SEO Agency.

You are helpful, professional, and provide concise answers. You can:
- Answer questions on various topics
- Have natural conversations with context awareness
- Remember previous messages in the conversation

Always be respectful and provide accurate information."""

    prompt = system_prompt if system_prompt else default_prompt

    agent = Agent(
        session_id=session_id,
        model=OpenAIChat(
            id=os.getenv("OPENAI_MODEL", "gpt-4"),
            api_key=os.getenv("OPENAI_KEY"),
        ),
        storage=agent_storage,
        description=prompt,
        instructions=[
            "Respond concisely and clearly",
            "Remember the conversation context",
            "Be helpful and professional"
        ],
        markdown=True,
        show_tool_calls=False,
        add_history_to_messages=True,
    )

    return agent

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Agno AI Agent Service",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "openai_configured": bool(os.getenv("OPENAI_KEY")),
        "storage_path": STORAGE_DIR,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - processes messages and returns AI responses

    Args:
        request: ChatRequest with session_id, message, and optional history

    Returns:
        ChatResponse with AI-generated response
    """
    try:
        logger.info(f"Chat request for session: {request.session_id}")
        logger.debug(f"Message: {request.message}")

        # Validate OpenAI key
        if not os.getenv("OPENAI_KEY"):
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured"
            )

        # Create agent for this session
        agent = create_agent(
            session_id=request.session_id,
            system_prompt=request.system_prompt
        )

        # Generate response using Agno
        logger.info(f"Generating response for session: {request.session_id}")
        response = agent.run(request.message)

        # Extract response content
        if hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)

        logger.info(f"Response generated successfully for session: {request.session_id}")

        return ChatResponse(
            session_id=request.session_id,
            response=response_text,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )

@app.post("/clear-session")
async def clear_session(session_id: str):
    """
    Clear chat history for a specific session

    Args:
        session_id: Session identifier to clear

    Returns:
        Success message
    """
    try:
        # Create agent and clear its memory
        agent = create_agent(session_id=session_id)

        # Clear the session from storage
        if hasattr(agent_storage, 'delete_session'):
            agent_storage.delete_session(session_id)

        logger.info(f"Session cleared: {session_id}")
        return {
            "status": "success",
            "message": f"Session {session_id} cleared",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing session: {str(e)}"
        )

@app.get("/sessions")
async def list_sessions():
    """
    List all active sessions (for debugging/monitoring)

    Returns:
        List of session IDs
    """
    try:
        # This would need to be implemented based on storage backend
        return {
            "message": "Session listing not implemented yet",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing sessions: {str(e)}"
        )

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    logger.info("=" * 50)
    logger.info("Starting Agno AI Agent Service")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Storage: {STORAGE_DIR}")
    logger.info("=" * 50)

    # Run the FastAPI app
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
