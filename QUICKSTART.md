# Quick Start Guide: Agno AI Service

This guide will help you get the Agno AI service running in under 5 minutes.

## What You're Building

A Python AI service using the Agno framework that provides intelligent chat capabilities with:
- **Conversation memory** - Agents remember context across messages
- **Session persistence** - SQLite storage for conversation history
- **RESTful API** - Easy integration with any application
- **OpenAI integration** - Powered by GPT-4 or GPT-3.5

## Prerequisites

- Python 3.11 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Step 1: Install Dependencies

### Windows
```bash
cd ai-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Linux/Mac
```bash
cd ai-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Configure Environment

Create a `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4
HOST=0.0.0.0
PORT=8000
STORAGE_DIR=./data
```

## Step 3: Start the Service

### Quick Start (Automated)

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

### Manual Start

```bash
python main.py
```

You should see:
```
==================================================
Starting Agno AI Agent Service
Host: 0.0.0.0
Port: 8000
Storage: ./data
==================================================
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 4: Test the Service

### Option A: Run Test Suite

In a new terminal:
```bash
cd ai-service
python test_service.py
```

This will run comprehensive tests including:
- Health check
- Basic chat
- Conversation memory
- Session clearing

### Option B: Manual Testing

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Send a Message:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_user",
    "message": "Hello, please introduce yourself"
  }'
```

**Test Memory:**
```bash
# First message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "memory_test",
    "message": "My favorite color is blue"
  }'

# Second message - should remember
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "memory_test",
    "message": "What is my favorite color?"
  }'
```

## Step 5: Integrate with Go Bot (Optional)

If you want to integrate this with your Feishu bot:

1. **Copy Go client:**
```bash
mkdir -p ../code/services/agno
cp go-client-example/agno_client.go ../code/services/agno/
```

2. **Set environment variable:**
```bash
export AGNO_SERVICE_URL="http://localhost:8000"
```

3. **Follow integration guide:**
See `INTEGRATION_GUIDE.md` for detailed instructions.

## API Reference

### `POST /chat`

Send a message and get AI response.

**Request:**
```json
{
  "session_id": "user_123",
  "message": "What is the capital of France?",
  "history": [],
  "system_prompt": "You are a helpful assistant"
}
```

**Response:**
```json
{
  "session_id": "user_123",
  "response": "The capital of France is Paris.",
  "timestamp": "2025-10-27T14:30:00"
}
```

### `GET /health`

Check service health.

**Response:**
```json
{
  "status": "healthy",
  "openai_configured": true,
  "storage_path": "./data",
  "timestamp": "2025-10-27T14:30:00"
}
```

### `POST /clear-session?session_id=xxx`

Clear conversation history for a session.

**Response:**
```json
{
  "status": "success",
  "message": "Session xxx cleared",
  "timestamp": "2025-10-27T14:30:00"
}
```

## Project Structure

```
ai-service/
├── main.py              # FastAPI application with Agno agents
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variable template
├── Dockerfile          # Docker deployment
├── test_service.py     # Test suite
├── start.sh           # Linux/Mac quick start
├── start.bat          # Windows quick start
├── README.md          # Comprehensive documentation
├── INTEGRATION_GUIDE.md # Go bot integration guide
├── QUICKSTART.md      # This file
└── go-client-example/  # Go client for integration
    ├── agno_client.go  # Go HTTP client
    └── README.md       # Go client usage
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_KEY` | Your OpenAI API key | **Required** |
| `OPENAI_MODEL` | Model to use | `gpt-4` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `STORAGE_DIR` | Database directory | `./data` |

## Troubleshooting

### "ModuleNotFoundError: No module named 'agno'"

**Solution:**
```bash
pip install -r requirements.txt
```

### "OpenAI API key not configured"

**Solution:**
- Make sure `.env` file exists
- Verify `OPENAI_KEY` is set in `.env`
- Check `.env` is in the same directory as `main.py`

### "Address already in use"

**Solution:**
- Port 8000 is already in use
- Change `PORT` in `.env` to another port (e.g., 8001)
- Or kill the process using port 8000

### Service starts but no response

**Solution:**
- Check OpenAI API key is valid
- Verify you have OpenAI API credits
- Check logs for error messages
- Test with: `curl http://localhost:8000/health`

## Next Steps

Now that your service is running, you can:

1. **Integrate with Feishu Bot**
   - See `INTEGRATION_GUIDE.md`
   - Copy Go client to your bot code
   - Update message handlers

2. **Add RAG Capabilities**
   - Integrate ChromaDB or Pinecone
   - Add document indexing
   - Implement retrieval logic

3. **Enable Tool Use**
   - Add Agno tools for web search
   - Add database query tools
   - Enable function calling

4. **Add Advanced Memory**
   - Implement conversation summarization
   - Store long-term user preferences
   - Add memory retrieval strategies

5. **Deploy to Production**
   - Use Docker: `docker build -t agno-service .`
   - Deploy to Railway, Render, or AWS
   - Configure environment variables

## Example Usage in Python

```python
import requests

# Send a message
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "session_id": "alice_123",
        "message": "Explain quantum computing in simple terms"
    }
)

data = response.json()
print(data["response"])
```

## Example Usage in JavaScript

```javascript
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'user_123',
    message: 'Hello!'
  })
});

const data = await response.json();
console.log(data.response);
```

## Support

- **Full Documentation**: See `README.md`
- **Integration Guide**: See `INTEGRATION_GUIDE.md`
- **Go Client**: See `go-client-example/README.md`
- **Test Suite**: Run `python test_service.py`

## Success Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with valid `OPENAI_KEY`
- [ ] Service starts without errors
- [ ] Health check passes (`curl http://localhost:8000/health`)
- [ ] Test chat message works
- [ ] Conversation memory works (test suite passes)

---

**You're all set!** The Agno AI service is now running and ready to provide intelligent chat capabilities. Start sending messages and explore the possibilities!
