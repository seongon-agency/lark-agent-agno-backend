# Integration Guide: Python Agno Service with Go Bot

This guide explains how to integrate the Python Agno AI service with your existing Go Feishu bot.

## Architecture

```
Feishu User Message
    ↓
Go Bot (Webhook Handler)
    ↓
Python Agno Service (AI Logic)
    ↓
OpenAI API
    ↓
Response back to Go Bot
    ↓
Feishu Card Response
```

## Step 1: Deploy Python Service

### Option A: Local Development

1. Start the Python service:
```bash
cd ai-service
./start.sh   # Linux/Mac
# or
start.bat    # Windows
```

The service will run on `http://localhost:8000`

### Option B: Railway Deployment

1. Create a new Railway project
2. Deploy the `ai-service` directory
3. Add environment variable: `OPENAI_KEY=your_key_here`
4. Note the URL (e.g., `https://your-service.up.railway.app`)

## Step 2: Create Python Service Client in Go

Create a new file: `code/services/agno/client.go`

```go
package agno

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

// AgnoClient wraps the Python Agno AI service
type AgnoClient struct {
	BaseURL    string
	HTTPClient *http.Client
}

// ChatRequest represents the request to the Python service
type ChatRequest struct {
	SessionID    string    `json:"session_id"`
	Message      string    `json:"message"`
	History      []Message `json:"history,omitempty"`
	SystemPrompt string    `json:"system_prompt,omitempty"`
}

// Message represents a chat message
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// ChatResponse represents the response from the Python service
type ChatResponse struct {
	SessionID string `json:"session_id"`
	Response  string `json:"response"`
	Timestamp string `json:"timestamp"`
}

// NewAgnoClient creates a new Agno service client
func NewAgnoClient() *AgnoClient {
	baseURL := os.Getenv("AGNO_SERVICE_URL")
	if baseURL == "" {
		baseURL = "http://localhost:8000"
	}

	return &AgnoClient{
		BaseURL: baseURL,
		HTTPClient: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

// Chat sends a message to the Agno service and returns the response
func (c *AgnoClient) Chat(sessionID, message string, history []Message) (string, error) {
	// Prepare request
	reqBody := ChatRequest{
		SessionID: sessionID,
		Message:   message,
		History:   history,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("failed to marshal request: %w", err)
	}

	// Make HTTP request
	url := fmt.Sprintf("%s/chat", c.BaseURL)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	// Read response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("service returned status %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	var chatResp ChatResponse
	if err := json.Unmarshal(body, &chatResp); err != nil {
		return "", fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return chatResp.Response, nil
}

// Health checks if the Agno service is available
func (c *AgnoClient) Health() error {
	url := fmt.Sprintf("%s/health", c.BaseURL)
	resp, err := c.HTTPClient.Get(url)
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return errors.New("service is not healthy")
	}

	return nil
}

// ClearSession clears the conversation history for a session
func (c *AgnoClient) ClearSession(sessionID string) error {
	url := fmt.Sprintf("%s/clear-session?session_id=%s", c.BaseURL, sessionID)
	req, err := http.NewRequest("POST", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("clear session failed with status %d", resp.StatusCode)
	}

	return nil
}
```

## Step 3: Modify Message Handler

Modify `code/handlers/event_msg_action.go` to use the Python service:

### Original Code (lines 47-81):
```go
func (*MessageAction) Execute(a *ActionInfo) bool {
	if a.handler.config.StreamMode {
		return true
	}
	msg := a.handler.sessionCache.GetMsg(*a.info.sessionId)
	msg = setDefaultPrompt(msg)
	msg = append(msg, openai.Messages{
		Role: "user", Content: a.info.qParsed,
	})

	aiMode := a.handler.sessionCache.GetAIMode(*a.info.sessionId)
	completions, err := a.handler.gpt.Completions(msg, aiMode)
	if err != nil {
		replyMsg(*a.ctx, fmt.Sprintf(
			"🤖️: The message bot encountered an error, please try again later. Error info: %v", err), a.info.msgId)
		return false
	}
	msg = append(msg, completions)
	a.handler.sessionCache.SetMsg(*a.info.sessionId, msg)

	if len(msg) == 3 {
		sendNewTopicCard(*a.ctx, a.info.sessionId, a.info.msgId,
			completions.Content)
	} else {
		sendOldTopicCard(*a.ctx, a.info.sessionId, a.info.msgId,
			completions.Content)
	}
	return false
}
```

### Modified Code (use Python service):
```go
import (
	"start-feishubot/services/agno"  // Add this import
)

func (*MessageAction) Execute(a *ActionInfo) bool {
	if a.handler.config.StreamMode {
		return true
	}

	// Get conversation history
	msg := a.handler.sessionCache.GetMsg(*a.info.sessionId)
	msg = setDefaultPrompt(msg)

	// Convert to Agno format
	var history []agno.Message
	for _, m := range msg {
		history = append(history, agno.Message{
			Role:    m.Role,
			Content: m.Content,
		})
	}

	// Call Python Agno service
	agnoClient := agno.NewAgnoClient()
	response, err := agnoClient.Chat(*a.info.sessionId, a.info.qParsed, history)
	if err != nil {
		replyMsg(*a.ctx, fmt.Sprintf(
			"🤖️: The message bot encountered an error, please try again later. Error info: %v", err), a.info.msgId)
		return false
	}

	// Update message history
	msg = append(msg, openai.Messages{
		Role: "user", Content: a.info.qParsed,
	})
	msg = append(msg, openai.Messages{
		Role: "assistant", Content: response,
	})
	a.handler.sessionCache.SetMsg(*a.info.sessionId, msg)

	// Send response card
	if len(msg) == 3 {
		sendNewTopicCard(*a.ctx, a.info.sessionId, a.info.msgId, response)
	} else {
		sendOldTopicCard(*a.ctx, a.info.sessionId, a.info.msgId, response)
	}
	return false
}
```

## Step 4: Add Environment Variable

Add to your `code/config.yaml`:

```yaml
# Agno Service Configuration
AGNO_SERVICE_URL: "http://localhost:8000"
```

Or set as environment variable:
```bash
export AGNO_SERVICE_URL="https://your-service.up.railway.app"
```

For Railway deployment:
- Go bot service: Add env var `AGNO_SERVICE_URL` pointing to Python service URL
- Python service: Add env var `OPENAI_KEY` with your OpenAI key

## Step 5: Test the Integration

1. **Start Python service:**
```bash
cd ai-service
python main.py
```

2. **Test Python service:**
```bash
cd ai-service
python test_service.py
```

3. **Start Go bot:**
```bash
cd code
go run main.go
```

4. **Send a message in Feishu**
   - The Go bot receives the message
   - Calls Python service
   - Returns AI response

## Architecture Benefits

### Why This Hybrid Approach?

1. **Best of Both Worlds**:
   - Go: Fast Feishu webhook handling, efficient message routing
   - Python: Rich AI ecosystem (Agno, LangChain, vector DBs)

2. **Easy to Extend**:
   - Add RAG: Just modify Python service
   - Add tools: Use Agno's built-in tool system
   - Add MCP: Python has better MCP support

3. **Independent Scaling**:
   - Scale Go bot for webhook volume
   - Scale Python service for AI compute
   - Different resource requirements

4. **Development Flexibility**:
   - You can work in Python (your preferred language)
   - No need to learn Go deeply
   - Keep Go code minimal (just proxying)

## Next Steps

Once this basic integration works, you can enhance the Python service with:

1. **RAG (Retrieval Augmented Generation)**:
   - Add ChromaDB or Pinecone for vector storage
   - Index company knowledge base
   - Retrieve relevant context before answering

2. **Advanced Memory**:
   - Add long-term memory beyond session storage
   - Implement conversation summarization
   - Store user preferences

3. **Tool Use**:
   - Agno supports tools natively
   - Add tools for web search, calculations, database queries
   - Enable function calling

4. **MCP Integration**:
   - Connect to MCP servers
   - Access external data sources
   - Extend agent capabilities

## Troubleshooting

### Python service connection refused
- Ensure Python service is running: `curl http://localhost:8000/health`
- Check firewall settings
- Verify `AGNO_SERVICE_URL` is correct

### OpenAI API errors in Python service
- Check `OPENAI_KEY` is set in Python service environment
- Test: `curl http://localhost:8000/health` should show `openai_configured: true`

### Go bot compilation errors
- Run `go mod tidy` to fetch dependencies
- Ensure `agno` package is in correct path

### Messages work but no AI response
- Check Python service logs: `python main.py` shows request logs
- Verify session_id is being passed correctly
- Test Python service directly with curl

## Example: Complete Flow

```
1. User sends: "Hello, what can you do?"
   ↓
2. Feishu sends webhook to Go bot (port 9000)
   ↓
3. Go bot extracts message, sessionId
   ↓
4. Go bot calls POST http://localhost:8000/chat with:
   {
     "session_id": "chat_abc123",
     "message": "Hello, what can you do?"
   }
   ↓
5. Python Agno service:
   - Creates agent for session "chat_abc123"
   - Calls OpenAI GPT-4
   - Stores conversation in SQLite
   ↓
6. Returns response to Go bot:
   {
     "session_id": "chat_abc123",
     "response": "Hello! I'm SEONGON AI...",
     "timestamp": "2025-10-27T14:00:00"
   }
   ↓
7. Go bot formats response as Feishu card
   ↓
8. User sees response in Feishu
```

## Railway Deployment Example

### Service 1: Go Bot
- **Name**: `feishu-bot`
- **Root Directory**: `/code`
- **Build Command**: `go build -o feishu_chatgpt main.go`
- **Start Command**: `./feishu_chatgpt`
- **Environment Variables**:
  - `APP_ID`: Your Feishu app ID
  - `APP_SECRET`: Your Feishu app secret
  - `APP_VERIFICATION_TOKEN`: Your verification token
  - `APP_ENCRYPT_KEY`: Your encrypt key
  - `AGNO_SERVICE_URL`: `https://agno-service.up.railway.app` (from Service 2)

### Service 2: Python AI Service
- **Name**: `agno-service`
- **Root Directory**: `/ai-service`
- **Build**: Automatically detected (Dockerfile)
- **Environment Variables**:
  - `OPENAI_KEY`: Your OpenAI API key
  - `OPENAI_MODEL`: `gpt-4`

Configure Feishu webhook URL to point to Service 1's Railway URL.

---

For questions or issues, please refer to the main README files in both `code/` and `ai-service/` directories.
