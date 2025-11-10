# Simple Feishu Bot Setup

A minimal Feishu bot with Agno AI - just chat, nothing more.

## What You Need

1. **Feishu/Lark Bot** - Create at https://open.feishu.cn/
2. **OpenAI API Key** - Get at https://platform.openai.com/api-keys
3. **Python 3.11+**

## Quick Start

### 1. Install Dependencies

```bash
cd lark-agent-agno-backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```env
APP_ID=cli_xxxxxx              # From Feishu bot backend
APP_SECRET=xxxxxxxxxxxxxx      # From Feishu bot backend
OPENAI_KEY=sk-xxxxxxxxxx       # Your OpenAI API key
```

### 3. Run the Bot

```bash
python main.py
```

You should see:
```
==================================================
Starting Feishu Agno Bot
Storage: ./data
==================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4. Configure Feishu Webhook

1. Go to your Feishu bot backend: https://open.feishu.cn/
2. Navigate to **事件订阅** (Event Subscriptions)
3. Set **请求地址** (Request URL) to: `http://YOUR_SERVER:8000/webhook/event`
4. Subscribe to these events:
   - `im.message.receive_v1` - Receive messages

### 5. Test It

Send a message to your bot in Feishu/Lark. It should respond!

## How It Works

```
User sends message → Feishu → Your Bot → Agno AI → OpenAI → Response → Feishu → User
```

**That's it!** Super simple.

## Features

- ✅ Text chat with AI
- ✅ Conversation memory (remembers context)
- ✅ Works in private chats and groups
- ❌ No images, audio, or fancy cards
- ❌ No special commands

## Troubleshooting

### "Missing required environment variables"
- Make sure `.env` file exists
- Check `APP_ID`, `APP_SECRET`, and `OPENAI_KEY` are set

### "Bot doesn't respond"
- Check webhook is configured correctly in Feishu
- Check bot has permission: `im:message` in Feishu backend
- Check logs with `python main.py` for errors

### "Failed to send message"
- Verify `APP_ID` and `APP_SECRET` are correct
- Check bot is added to the conversation

## Deploy to Production

### Option 1: Railway
1. Push to GitHub
2. Connect Railway to your repo
3. Set environment variables in Railway dashboard
4. Use Railway URL for Feishu webhook

### Option 2: Docker
```bash
docker build -t feishu-bot .
docker run -d -p 8000:8000 --env-file .env feishu-bot
```

### Option 3: Any VPS
```bash
# Install dependencies
pip install -r requirements.txt

# Run with screen or tmux
screen -S bot
python main.py
# Ctrl+A, D to detach
```

## File Structure

```
lark-agent-agno-backend/
├── main.py              # The bot (200 lines)
├── requirements.txt     # Dependencies
├── .env.example        # Config template
└── data/               # SQLite storage (auto-created)
    └── agents.db       # Conversation history
```

## Code Overview

The entire bot is ~200 lines:

- **Lines 37-40**: Initialize Feishu client
- **Lines 52-64**: Create Agno agent with memory
- **Lines 67-88**: Send messages to Feishu
- **Lines 101-128**: Handle incoming webhooks
- **Lines 131-180**: Process messages and generate responses

## License

Same as parent project.
