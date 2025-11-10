# Deploy to Railway - Step by Step

Railway is the easiest way to deploy your bot. Takes 5 minutes!

## Prerequisites

- GitHub account
- Railway account (sign up at https://railway.app with GitHub)
- Feishu bot credentials (APP_ID, APP_SECRET)
- OpenAI API key

## Step 1: Push Code to GitHub

```bash
cd lark-agent-agno-backend

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit: Feishu Agno bot"

# Create a new repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy to Railway

### Option A: Via Railway Dashboard (Easiest)

1. **Go to Railway**: https://railway.app/new

2. **Click "Deploy from GitHub repo"**

3. **Select your repository** (authorize GitHub if needed)

4. **Railway will auto-detect**:
   - Dockerfile
   - railway.json configuration
   - And start building!

### Option B: Using Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

## Step 3: Configure Environment Variables

In Railway dashboard:

1. **Click your project**
2. **Go to "Variables" tab**
3. **Add these variables**:

```
APP_ID=cli_xxxxxxxxxxxxxx
APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4
```

**Important**: Don't set `HOST` or `PORT` - Railway handles these automatically!

## Step 4: Get Your Railway URL

1. In Railway dashboard, go to **Settings** tab
2. Under **Networking**, click **Generate Domain**
3. You'll get a URL like: `https://your-app.up.railway.app`

**Test it**: Visit `https://your-app.up.railway.app/` - you should see:
```json
{
  "service": "Feishu Agno Bot",
  "status": "running",
  "timestamp": "2025-..."
}
```

## Step 5: Configure Feishu Webhook

1. **Go to Feishu Open Platform**: https://open.feishu.cn/

2. **Navigate to your bot** → **事件订阅** (Event Subscriptions)

3. **Set Request URL**:
   ```
   https://your-app.up.railway.app/webhook/event
   ```

4. **Subscribe to events**:
   - ✅ `im.message.receive_v1` - Receive messages

5. **Add Permissions** (权限管理):
   - ✅ `im:message` - Send messages
   - ✅ `im:message:send_as_bot` - Send as bot

6. **Click "Save" and verify** the webhook (Feishu will send a challenge)

## Step 6: Test Your Bot! 🎉

1. Open Feishu/Lark app
2. Find your bot
3. Send a message: "Hello!"
4. Bot should respond within seconds

## Monitoring & Logs

### View Logs in Railway:
1. Go to your Railway project
2. Click **"View Logs"**
3. Watch real-time logs as messages come in

### Check Health:
Visit `https://your-app.up.railway.app/` anytime to verify bot is running

## Troubleshooting

### "503 Service Unavailable"
- **Check**: Deployment succeeded in Railway
- **Check**: Logs for errors (missing env vars?)
- **Fix**: Make sure all 3 env vars are set (APP_ID, APP_SECRET, OPENAI_KEY)

### "Bot doesn't respond"
- **Check**: Webhook URL is correct in Feishu
- **Check**: Events are subscribed (`im.message.receive_v1`)
- **Check**: Bot has permissions (`im:message`)
- **Check**: Railway logs show incoming requests

### "Failed to send message"
- **Check**: APP_ID and APP_SECRET are correct
- **Check**: Bot is added to the conversation
- **Check**: Permissions are granted in Feishu backend

### "Challenge verification failed"
- **Check**: Webhook URL ends with `/webhook/event` (no trailing slash)
- **Check**: Bot is deployed and running (visit root URL)
- **Try**: Delete and re-add webhook URL

## Updating Your Bot

After making code changes:

```bash
git add .
git commit -m "Update bot"
git push

# Railway auto-deploys! Wait ~2 minutes.
```

## Cost

Railway free tier includes:
- ✅ $5 free credit per month
- ✅ 500 hours of runtime
- ✅ Enough for testing and small bots

For production/heavy use, upgrade to Pro ($5/month minimum).

## Environment Variables Reference

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `APP_ID` | ✅ Yes | `cli_a1b2c3d4` | Feishu app ID |
| `APP_SECRET` | ✅ Yes | `abc123xyz789` | Feishu app secret |
| `OPENAI_KEY` | ✅ Yes | `sk-proj-xxx` | OpenAI API key |
| `OPENAI_MODEL` | ❌ No | `gpt-4` | OpenAI model (default: gpt-4) |
| `STORAGE_DIR` | ❌ No | `/app/data` | SQLite storage path (auto-set) |
| `HOST` | ❌ No | `0.0.0.0` | Server host (Railway handles) |
| `PORT` | ❌ No | `8000` | Server port (Railway handles) |

## Next Steps

Your bot is live! 🚀

Want to add features?
- Add `/clear` command to reset conversation
- Add support for images
- Add custom system prompts
- Connect to external APIs

Check out the Agno docs: https://docs.agno.com

## Support

Having issues? Check:
1. Railway logs first
2. Feishu event subscription status
3. Environment variables are set correctly

Still stuck? The logs usually tell you exactly what's wrong!
