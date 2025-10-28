# Agno AI Agent Service

A Python-based AI service using the Agno framework to provide intelligent chat capabilities with memory and context for the Feishu bot.

## Features

- **AI Chat with Context**: Powered by Agno framework and OpenAI models
- **Session Management**: Persistent conversation history using SQLite storage
- **RESTful API**: FastAPI-based endpoints for easy integration
- **Memory**: Agents remember conversation context across messages
- **Configurable**: Support for custom system prompts and models

## Prerequisites

- Python 3.11+
- OpenAI API key

## Installation

### Local Development

1. **Install dependencies**:
```bash
cd ai-service
pip install -r requirements.txt
```

2. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

3. **Run the service**:
```bash
python main.py
```

The service will start on `http://localhost:8000`

### Docker Deployment

1. **Build the image**:
```bash
docker build -t agno-ai-service .
```

2. **Run the container**:
```bash
docker run -d \
  -p 8000:8000 \
  -e OPENAI_KEY=your_key_here \
  -e OPENAI_MODEL=gpt-4 \
  -v $(pwd)/data:/app/data \
  --name agno-ai \
  agno-ai-service
```

## API Endpoints

### `GET /`
Health check endpoint
```bash
curl http://localhost:8000/
```

### `POST /chat`
Send a message and get AI response

**Request**:
```json
{
  "session_id": "user_123",
  "message": "Hello, how are you?",
  "history": [],
  "system_prompt": "You are a helpful assistant"
}
```

**Response**:
```json
{
  "session_id": "user_123",
  "response": "I'm doing well, thank you! How can I help you today?",
  "timestamp": "2025-10-27T10:30:00"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session",
    "message": "What is the capital of France?"
  }'
```

### `POST /clear-session`
Clear conversation history for a session

**Request**:
```bash
curl -X POST "http://localhost:8000/clear-session?session_id=user_123"
```

### `GET /health`
Detailed health check
```bash
curl http://localhost:8000/health
```

## Integration with Go Bot

To integrate this Python service with your Go Feishu bot, modify the OpenAI client in your Go code to call this service instead:

```go
// In services/openai/gpt.go or similar

func (gpt *ChatGPT) Completions(messages []Messages, aiMode string) (Messages, error) {
    // Instead of calling OpenAI directly, call our Python service
    pythonServiceURL := os.Getenv("PYTHON_AI_SERVICE_URL") // e.g., "http://localhost:8000"

    // Convert messages to request format
    requestBody := map[string]interface{}{
        "session_id": "session_id_here",
        "message": messages[len(messages)-1].Content,
        "history": messages[:len(messages)-1],
    }

    // Make HTTP request to Python service
    response, err := makeHTTPRequest(pythonServiceURL + "/chat", requestBody)
    if err != nil {
        return Messages{}, err
    }

    return Messages{
        Role: "assistant",
        Content: response.Response,
    }, nil
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `STORAGE_DIR` | Directory for SQLite database | `./data` |

## Storage

The service uses SQLite to store agent sessions and conversation history. The database file is created in the `STORAGE_DIR` directory (default: `./data/agents.db`).

## Logging

The service logs all requests and errors. Logs are output to stdout in the format:
```
[INFO] 2025-10-27 10:30:00 - Chat request for session: user_123
[INFO] 2025-10-27 10:30:01 - Response generated successfully
```

## Deployment on Railway

1. Create a new project in Railway
2. Add this service from your repository
3. Set environment variables:
   - `OPENAI_KEY`: Your OpenAI API key
   - `OPENAI_MODEL`: `gpt-4` or `gpt-3.5-turbo`
4. Railway will automatically detect the Dockerfile and deploy

## Testing

Test the service is working:

```bash
# Health check
curl http://localhost:8000/health

# Send a test message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test",
    "message": "Hello, please introduce yourself"
  }'
```

## Troubleshooting

### "OpenAI API key not configured"
- Make sure `OPENAI_KEY` environment variable is set
- Check `.env` file exists and contains valid key

### Database errors
- Ensure `STORAGE_DIR` exists and is writable
- Check disk space availability

### Connection refused
- Verify the service is running: `curl http://localhost:8000/`
- Check if port 8000 is available

## Next Steps

This is a simple implementation. You can enhance it with:
- **RAG (Retrieval Augmented Generation)**: Add vector database for knowledge retrieval
- **Tool Use**: Enable agents to use external tools and APIs
- **MCP Integration**: Connect with Model Context Protocol servers
- **Advanced Memory**: Implement more sophisticated conversation memory
- **Multi-model Support**: Add support for other LLM providers

## License

Same as the parent project
