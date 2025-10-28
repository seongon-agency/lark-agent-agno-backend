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

	"start-feishubot/logger"
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

// HealthResponse represents the health check response
type HealthResponse struct {
	Status           string `json:"status"`
	OpenAIConfigured bool   `json:"openai_configured"`
	StoragePath      string `json:"storage_path"`
	Timestamp        string `json:"timestamp"`
}

// NewAgnoClient creates a new Agno service client
func NewAgnoClient() *AgnoClient {
	baseURL := os.Getenv("AGNO_SERVICE_URL")
	if baseURL == "" {
		baseURL = "http://localhost:8000"
		logger.Warn("AGNO_SERVICE_URL not set, using default: http://localhost:8000")
	}

	logger.Info("Initializing Agno client with URL:", baseURL)

	return &AgnoClient{
		BaseURL: baseURL,
		HTTPClient: &http.Client{
			Timeout: 90 * time.Second, // Increased timeout for AI processing
		},
	}
}

// Chat sends a message to the Agno service and returns the response
func (c *AgnoClient) Chat(sessionID, message string, history []Message) (string, error) {
	logger.Debugf("Agno Chat - SessionID: %s, Message: %s", sessionID, message)

	// Prepare request
	reqBody := ChatRequest{
		SessionID: sessionID,
		Message:   message,
		History:   history,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		logger.Errorf("Failed to marshal Agno request: %v", err)
		return "", fmt.Errorf("failed to marshal request: %w", err)
	}

	// Make HTTP request
	url := fmt.Sprintf("%s/chat", c.BaseURL)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		logger.Errorf("Failed to create Agno request: %v", err)
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	logger.Debug("Sending request to Agno service...")
	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		logger.Errorf("Failed to send request to Agno service: %v", err)
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	// Read response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		logger.Errorf("Failed to read Agno response: %v", err)
		return "", fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		logger.Errorf("Agno service returned status %d: %s", resp.StatusCode, string(body))
		return "", fmt.Errorf("service returned status %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	var chatResp ChatResponse
	if err := json.Unmarshal(body, &chatResp); err != nil {
		logger.Errorf("Failed to unmarshal Agno response: %v", err)
		return "", fmt.Errorf("failed to unmarshal response: %w", err)
	}

	logger.Debugf("Agno response received - SessionID: %s, Response length: %d", chatResp.SessionID, len(chatResp.Response))

	return chatResp.Response, nil
}

// Health checks if the Agno service is available
func (c *AgnoClient) Health() (*HealthResponse, error) {
	url := fmt.Sprintf("%s/health", c.BaseURL)
	resp, err := c.HTTPClient.Get(url)
	if err != nil {
		logger.Errorf("Agno health check failed: %v", err)
		return nil, fmt.Errorf("health check failed: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read health response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("service is not healthy (status %d): %s", resp.StatusCode, string(body))
	}

	var healthResp HealthResponse
	if err := json.Unmarshal(body, &healthResp); err != nil {
		return nil, fmt.Errorf("failed to unmarshal health response: %w", err)
	}

	return &healthResp, nil
}

// ClearSession clears the conversation history for a session
func (c *AgnoClient) ClearSession(sessionID string) error {
	logger.Infof("Clearing Agno session: %s", sessionID)

	url := fmt.Sprintf("%s/clear-session?session_id=%s", c.BaseURL, sessionID)
	req, err := http.NewRequest("POST", url, nil)
	if err != nil {
		logger.Errorf("Failed to create clear session request: %v", err)
		return fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		logger.Errorf("Failed to send clear session request: %v", err)
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		logger.Errorf("Clear session failed (status %d): %s", resp.StatusCode, string(body))
		return fmt.Errorf("clear session failed with status %d", resp.StatusCode)
	}

	logger.Infof("Session cleared successfully: %s", sessionID)
	return nil
}

// CheckConnection verifies the Agno service is reachable and properly configured
func (c *AgnoClient) CheckConnection() error {
	logger.Info("Checking Agno service connection...")

	health, err := c.Health()
	if err != nil {
		return fmt.Errorf("connection check failed: %w", err)
	}

	if health.Status != "healthy" {
		return errors.New("service status is not healthy")
	}

	if !health.OpenAIConfigured {
		return errors.New("OpenAI is not configured in the Agno service")
	}

	logger.Info("✓ Agno service connection verified")
	logger.Infof("  Status: %s", health.Status)
	logger.Infof("  OpenAI Configured: %v", health.OpenAIConfigured)
	logger.Infof("  Storage Path: %s", health.StoragePath)

	return nil
}
