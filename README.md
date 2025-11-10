# Feishu Bot with Agno AI

Minimal Feishu/Lark bot powered by Agno AI framework. Clean, simple, just works.

## Features

- ✅ Text chat with AI (Agno + OpenAI)
- ✅ Message deduplication
- ✅ Encrypted webhook support
- ✅ 168 lines of clean code

## Quick Start

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env`:
```env
APP_ID=cli_xxxxx
APP_SECRET=xxxxx
APP_ENCRYPT_KEY=xxxxx
OPENAI_KEY=sk-xxxxx
```

### 3. Run

```bash
python main.py
```

### 4. Setup Lark Webhooks

In Lark developer console:
- Event webhook: `https://your-domain.com/webhook/event`
- Card webhook: `https://your-domain.com/webhook/card`
- Subscribe to: `im.message.receive_v1`
- Add permission: `im:message`

## Customizing the AI Agent

The agent is created in `main.py` around line 135. Here's how to customize it:

### Basic Customization

**Change the personality:**
```python
agent = Agent(
    model=OpenAIChat(
        id=os.getenv("OPENAI_MODEL", "gpt-4"),
        api_key=os.getenv("OPENAI_KEY")
    ),
    description="You are a friendly customer support agent. Be helpful and professional.",
    markdown=True
)
```

**Use a different model:**
```python
model=OpenAIChat(
    id="gpt-4-turbo",  # or "gpt-3.5-turbo" for faster/cheaper
    api_key=os.getenv("OPENAI_KEY")
)
```

**Adjust temperature (creativity):**
```python
model=OpenAIChat(
    id="gpt-4",
    api_key=os.getenv("OPENAI_KEY"),
    temperature=0.7  # 0 = focused, 2 = creative
)
```

### Advanced Customization

**Add instructions:**
```python
agent = Agent(
    model=OpenAIChat(...),
    description="You are a sales assistant for SEONGON Agency.",
    instructions=[
        "Always be professional and friendly",
        "Keep responses under 100 words",
        "If asked about pricing, direct to contact@seongon.com"
    ],
    markdown=True
)
```

**Add knowledge/context:**
```python
agent = Agent(
    model=OpenAIChat(...),
    description="You are a company expert.",
    instructions=[
        "Company: SEONGON - Vietnamese SEO Agency",
        "Services: SEO, Content Marketing, Link Building",
        "Founded: 2020",
        "Use this information to answer questions"
    ],
    markdown=True
)
```

**Enable tools (web search, code execution, etc):**
```python
from agno.tools.duckduckgo import DuckDuckGo

agent = Agent(
    model=OpenAIChat(...),
    description="You can search the web to answer questions.",
    tools=[DuckDuckGo()],  # Adds web search capability
    markdown=True,
    show_tool_calls=True  # Show when tools are used
)
```

**Add memory (remember across sessions):**
```python
from agno.storage.agent.sqlite import SqlAgentStorage

agent = Agent(
    model=OpenAIChat(...),
    description="You remember user preferences.",
    storage=SqlAgentStorage(
        table_name="agent_sessions",
        db_file="./data/memory.db"
    ),
    markdown=True
)
```

### Practical Examples

**Example 1: Customer Support Bot**
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4", api_key=os.getenv("OPENAI_KEY")),
    description="""You are a customer support agent for SEONGON Agency.
    Be helpful, professional, and concise.""",
    instructions=[
        "For technical issues, collect: browser, OS, error message",
        "For pricing questions, direct to sales@seongon.com",
        "Always ask if the issue is resolved before ending"
    ],
    markdown=True
)
```

**Example 2: Sales Assistant**
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4", api_key=os.getenv("OPENAI_KEY"), temperature=0.8),
    description="""You are a friendly sales assistant.
    You help customers understand our SEO services.""",
    instructions=[
        "Services: SEO Audits, Content Strategy, Link Building, Technical SEO",
        "Always highlight ROI and results",
        "Offer a free consultation: contact@seongon.com",
        "Be enthusiastic but not pushy"
    ],
    markdown=True
)
```

**Example 3: Internal Team Assistant**
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4-turbo", api_key=os.getenv("OPENAI_KEY")),
    description="""You are an internal team assistant.
    Help with tasks, answer questions, boost productivity.""",
    instructions=[
        "You can help with: scheduling, reminders, document summaries",
        "Access to team docs: docs.seongon.com",
        "Be concise - team is busy",
        "Use bullet points for lists"
    ],
    markdown=True
)
```

**Example 4: Multilingual Support**
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4", api_key=os.getenv("OPENAI_KEY")),
    description="""You are a multilingual support agent.
    Detect language and respond in the same language.""",
    instructions=[
        "Supported languages: English, Vietnamese, Chinese",
        "Always match the user's language",
        "If unsure, ask which language they prefer"
    ],
    markdown=True
)
```

### Environment-Based Configuration

Use environment variables for easy customization:

```python
# In main.py
AGENT_PERSONALITY = os.getenv("AGENT_PERSONALITY", "helpful AI assistant")
AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.7"))

agent = Agent(
    model=OpenAIChat(
        id=os.getenv("OPENAI_MODEL", "gpt-4"),
        api_key=os.getenv("OPENAI_KEY"),
        temperature=AGENT_TEMPERATURE
    ),
    description=f"You are a {AGENT_PERSONALITY}. Answer concisely and clearly.",
    markdown=True
)
```

Then in Railway:
```
AGENT_PERSONALITY=friendly sales assistant
AGENT_TEMPERATURE=0.9
```

## Project Structure

```
lark-agent-agno-backend/
├── main.py              # Bot logic (168 lines)
├── requirements.txt     # Dependencies
├── .env.example        # Config template
├── Dockerfile          # Container
├── railway.json        # Railway config
└── README.md          # This file
```

## Key Files

**`main.py`** - Everything is here:
- `is_duplicate()` - Prevents double responses
- `decrypt()` - Handles encrypted webhooks
- `send_message()` - Sends to Lark
- `webhook_event()` - Receives messages
- `process_message()` - AI processing
- Agent creation at line 135 ← **Customize here!**

## Deployment

### Railway (Recommended)

1. Push to GitHub
2. Connect to Railway
3. Set environment variables
4. Deploy automatically

See `DEPLOY_RAILWAY.md` for detailed guide.

### Docker

```bash
docker build -t feishu-bot .
docker run -d -p 8000:8000 --env-file .env feishu-bot
```

## Troubleshooting

**Bot responds twice:**
- Already fixed with `is_duplicate()`

**Challenge verification fails:**
- Check `APP_ENCRYPT_KEY` is set
- Webhook URL must be exact

**No response:**
- Check Railway logs
- Verify event subscription: `im.message.receive_v1`
- Check permissions: `im:message`

**Agent not following instructions:**
- Make instructions specific and clear
- Use examples in the description
- Lower temperature for more consistent behavior

## Performance

- Response time: 2-5 seconds (depends on model)
- Concurrent users: Unlimited (stateless)
- Memory: ~100MB per instance

## Agno Resources

- Docs: https://docs.agno.com
- Tools: https://docs.agno.com/tools
- Examples: https://github.com/agno-ai/agno/tree/main/examples

## License

MIT
