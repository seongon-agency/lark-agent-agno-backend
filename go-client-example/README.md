# Go Client for Agno Service

This directory contains a ready-to-use Go client for integrating with the Python Agno AI service.

## Installation

1. **Copy the client to your Go project**:
```bash
# From the ai-service directory
mkdir -p ../code/services/agno
cp go-client-example/agno_client.go ../code/services/agno/
```

2. **The client is now available at**: `code/services/agno/agno_client.go`

## Usage

### Basic Example

```go
package main

import (
	"fmt"
	"start-feishubot/services/agno"
)

func main() {
	// Create client (reads AGNO_SERVICE_URL from environment)
	client := agno.NewAgnoClient()

	// Check connection
	if err := client.CheckConnection(); err != nil {
		panic(err)
	}

	// Send a message
	response, err := client.Chat(
		"user_123",           // session ID
		"Hello, who are you?", // message
		nil,                   // history (can be nil for new conversation)
	)
	if err != nil {
		panic(err)
	}

	fmt.Println("AI Response:", response)
}
```

### With Message History

```go
// Prepare conversation history
history := []agno.Message{
	{Role: "system", Content: "You are a helpful assistant"},
	{Role: "user", Content: "My name is Alice"},
	{Role: "assistant", Content: "Nice to meet you, Alice!"},
}

// Send new message with context
response, err := client.Chat(
	"user_123",
	"What's my name?",
	history,
)
```

### Clear Session

```go
client := agno.NewAgnoClient()
err := client.ClearSession("user_123")
if err != nil {
	fmt.Println("Failed to clear session:", err)
}
```

### Health Check

```go
client := agno.NewAgnoClient()
health, err := client.Health()
if err != nil {
	panic(err)
}

fmt.Printf("Status: %s\n", health.Status)
fmt.Printf("OpenAI Configured: %v\n", health.OpenAIConfigured)
```

## Integration with Existing Bot

To integrate with the existing Feishu bot, modify `handlers/event_msg_action.go`:

### Step 1: Add Import

```go
import (
	// ... existing imports
	"start-feishubot/services/agno"
)
```

### Step 2: Modify MessageAction.Execute()

Replace the OpenAI completion call with Agno client call:

```go
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

	// Call Agno service
	agnoClient := agno.NewAgnoClient()
	response, err := agnoClient.Chat(*a.info.sessionId, a.info.qParsed, history)
	if err != nil {
		replyMsg(*a.ctx, fmt.Sprintf(
			"🤖️: Error: %v", err), a.info.msgId)
		return false
	}

	// Update history
	msg = append(msg, openai.Messages{
		Role: "user", Content: a.info.qParsed,
	})
	msg = append(msg, openai.Messages{
		Role: "assistant", Content: response,
	})
	a.handler.sessionCache.SetMsg(*a.info.sessionId, msg)

	// Send response
	if len(msg) == 3 {
		sendNewTopicCard(*a.ctx, a.info.sessionId, a.info.msgId, response)
	} else {
		sendOldTopicCard(*a.ctx, a.info.sessionId, a.info.msgId, response)
	}
	return false
}
```

### Step 3: Set Environment Variable

```bash
export AGNO_SERVICE_URL="http://localhost:8000"
# or for production
export AGNO_SERVICE_URL="https://your-agno-service.up.railway.app"
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AGNO_SERVICE_URL` | Base URL of the Python Agno service | `http://localhost:8000` |

## Error Handling

The client includes comprehensive error handling:

- **Connection errors**: Returns error if service is unreachable
- **HTTP errors**: Returns detailed error with status code and body
- **Timeout**: 90-second timeout for AI processing (configurable)
- **Logging**: All operations are logged via the bot's logger

## Testing

Before integrating, test the client:

```go
package main

import (
	"start-feishubot/services/agno"
	"start-feishubot/logger"
)

func main() {
	client := agno.NewAgnoClient()

	// Test connection
	if err := client.CheckConnection(); err != nil {
		logger.Error("Connection test failed:", err)
		return
	}

	// Test chat
	response, err := client.Chat("test", "Hello!", nil)
	if err != nil {
		logger.Error("Chat test failed:", err)
		return
	}

	logger.Info("Chat test passed! Response:", response)

	// Test clear session
	if err := client.ClearSession("test"); err != nil {
		logger.Error("Clear session test failed:", err)
		return
	}

	logger.Info("All tests passed!")
}
```

## Troubleshooting

### "connection refused"
- Ensure Python service is running
- Check `AGNO_SERVICE_URL` is correct
- Verify firewall allows connection

### "service is not healthy"
- Check Python service logs
- Verify `OPENAI_KEY` is set in Python service
- Test: `curl http://localhost:8000/health`

### Timeout errors
- Increase timeout in `NewAgnoClient()` if needed
- Check Python service performance
- Verify OpenAI API is responding

## Advanced Usage

### Custom Timeout

```go
client := agno.NewAgnoClient()
client.HTTPClient.Timeout = 120 * time.Second // 2 minutes
```

### Retry Logic

```go
func chatWithRetry(client *agno.AgnoClient, sessionID, message string, maxRetries int) (string, error) {
	var lastErr error
	for i := 0; i < maxRetries; i++ {
		response, err := client.Chat(sessionID, message, nil)
		if err == nil {
			return response, nil
		}
		lastErr = err
		time.Sleep(time.Second * time.Duration(i+1))
	}
	return "", fmt.Errorf("failed after %d retries: %w", maxRetries, lastErr)
}
```

## Next Steps

Once basic integration works:

1. **Add Streaming Support**: Modify Python service to support SSE
2. **Add Tools**: Enable Agno tools in Python service
3. **Add RAG**: Integrate vector database in Python service
4. **Add MCP**: Connect to MCP servers via Python service

See `../INTEGRATION_GUIDE.md` for detailed integration instructions.
