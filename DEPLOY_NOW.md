# Deploy Your Web App in 5 Minutes ⚡

## What You'll Get

After deployment, you'll have a URL like:
```
https://your-research-assistant.streamlit.app
```

Anyone with this URL can use the app from **any device** (Mac, Windows, iPhone, Android) - no installation needed!

---

## Option 1: Streamlit Community Cloud (Easiest, FREE)

### Step 1: Push to GitHub

1. **Create a new repository** on GitHub: https://github.com/new
   - Name it: `research-assistant`
   - Make it Public or Private
   - Don't initialize with README

2. **Push your code**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/research-assistant.git
   git branch -M main
   git add .
   git commit -m "Research Assistant web app"
   git push -u origin main
   ```

### Step 2: Deploy on Streamlit

1. Go to: https://share.streamlit.io/
2. Click "New app"
3. Connect your GitHub account
4. Select:
   - **Repository:** research-assistant
   - **Branch:** main
   - **Main file path:** web_app.py
5. Click "Deploy"

### Step 3: Share the URL!

You'll get a URL like: `https://your-username-research-assistant.streamlit.app`

Share this URL with anyone - they can use it immediately!

---

## Option 2: Hugging Face Spaces (Also FREE)

### Deploy in 3 Steps:

1. **Go to:** https://huggingface.co/new-space
2. **Configure:**
   - Space name: `research-assistant`
   - SDK: Select "Streamlit"
   - Hardware: CPU Basic (free)
3. **Upload files:**
   - Drag and drop `web_app.py`
   - Drag and drop `requirements.txt`
   - Drag and drop the entire `ra_orchestrator` folder

Your app will be at: `https://huggingface.co/spaces/YOUR_USERNAME/research-assistant`

---

## How Users Access It

### For Desktop Users:
1. Open browser
2. Go to your URL
3. Enter API keys in sidebar (one-time)
4. Start researching!

### For Mobile Users:
1. Open Safari/Chrome on iPhone/Android
2. Go to same URL
3. Works exactly the same!

---

## API Keys

Users enter their own keys (secure):
- **Anthropic:** https://console.anthropic.com/
- **Serper:** https://serper.dev/

Both offer free trials!

---

## Cost

- **Deployment:** FREE forever
- **Running:** FREE (users pay for their own API usage)
- **Hosting:** FREE on both platforms

---

## Updating Your App

After deployment, just push to GitHub:
```bash
git add .
git commit -m "Update"
git push
```

**Streamlit Cloud** auto-updates within minutes!

---

## Need Help?

The app is ready to deploy right now. Just follow Step 1 & 2 above!

**Time:** 5 minutes
**Cost:** $0
**Maintenance:** Automatic
**Platforms:** All of them!
