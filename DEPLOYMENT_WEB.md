# Web App Deployment - Works on ALL Platforms! 🌍

Your Research Assistant as a web app works on **Mac, Windows, Linux, iOS, Android** - anywhere with a web browser!

## 🚀 Quick Start (Local Testing)

```bash
streamlit run web_app.py
```

Then open http://localhost:8501 in your browser.

---

## ☁️ Deploy to Cloud (Free Options)

### Option 1: Streamlit Community Cloud (Recommended)

**100% Free, easiest deployment!**

1. **Push code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Research Assistant web app"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/research-assistant.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to https://streamlit.io/cloud
   - Click "New app"
   - Connect your GitHub account
   - Select your repository
   - Set main file: `web_app.py`
   - Click "Deploy"

3. **Share the URL**:
   - You'll get a URL like: `https://your-app.streamlit.app`
   - Anyone can access it from any device!
   - Users enter their own API keys

**Pros:**
- ✅ Free forever
- ✅ Auto-updates when you push to GitHub
- ✅ Works on all platforms
- ✅ HTTPS included
- ✅ No server management

---

### Option 2: Hugging Face Spaces (Also Free)

1. **Create a Space**:
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Choose "Streamlit" as SDK
   - Name it "research-assistant"

2. **Upload files**:
   - Upload `web_app.py`
   - Upload `requirements.txt`
   - Upload entire `ra_orchestrator` folder

3. **Access**:
   - URL: `https://huggingface.co/spaces/YOUR_USERNAME/research-assistant`

---

### Option 3: Render (Free Tier)

1. **Push to GitHub** (same as Option 1)

2. **Deploy on Render**:
   - Go to https://render.com/
   - Click "New Web Service"
   - Connect GitHub repo
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run web_app.py --server.port $PORT --server.address 0.0.0.0`
   - Click "Create Web Service"

---

## 📱 How Users Access It

### Desktop (Mac/Windows/Linux):
1. Open browser
2. Go to your deployment URL
3. Enter API keys in sidebar
4. Start researching!

### Mobile (iOS/Android):
1. Open browser (Safari/Chrome)
2. Go to deployment URL
3. Works exactly the same!

---

## 🔒 Security Notes

**API Keys:**
- Users enter their own keys
- Keys are NOT stored
- Keys are only in browser memory

**For trusted team (optional):**
You can pre-configure API keys using Streamlit Secrets:

1. In Streamlit Cloud, go to App Settings → Secrets
2. Add:
   ```toml
   ANTHROPIC_API_KEY = "your-key-here"
   SERPER_API_KEY = "your-key-here"
   ```
3. Update `web_app.py` to use `st.secrets` as fallback

---

## 📦 What to Share with Users

**Public deployment:**
```
🔍 Research Assistant - AI-Powered Research Tool

Access here: https://your-app.streamlit.app

What you need:
- Anthropic API Key: https://console.anthropic.com/
- Serper API Key: https://serper.dev/

Both offer free trials!

Works on any device - Mac, Windows, Linux, iPhone, Android.
```

---

## 🔧 Advanced: Custom Domain

If you want `research.yourcompany.com` instead of `.streamlit.app`:

1. **Streamlit Cloud** (paid):
   - Upgrade to Teams plan
   - Add custom domain in settings

2. **Render** (free with some setup):
   - Add custom domain in Render dashboard
   - Update DNS records

---

## ✅ Advantages of Web App vs Desktop App

| Feature | Desktop App | Web App |
|---------|------------|---------|
| Works on Mac | ❌ Requires signing | ✅ Yes |
| Works on Windows | ✅ Yes | ✅ Yes |
| Works on iOS/Android | ❌ No | ✅ Yes |
| Distribution | Send large .exe | Send URL |
| Updates | Rebuild & resend | Auto-update |
| Size | 67 MB download | 0 MB download |
| Maintenance | Manual | Automatic |

---

## 🎯 Recommendation

**Deploy to Streamlit Community Cloud:**
1. Free
2. Works everywhere
3. Easy to share (just a URL)
4. Auto-updates
5. No Mac code-signing issues

It takes 5 minutes to deploy and solves all your cross-platform problems!
