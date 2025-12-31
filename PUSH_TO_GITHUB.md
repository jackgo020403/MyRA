# Push to GitHub - Step by Step

## Step 1: Set Your Git Identity (One-time setup)

Replace with YOUR email and name:

```bash
git config --global user.email "your-email@gmail.com"
git config --global user.name "Your Name"
```

## Step 2: Create GitHub Repository

1. Go to: https://github.com/new
2. **Repository name:** `research-assistant`
3. **Description:** "AI-Powered Research Assistant Web App"
4. **Visibility:** Public or Private (your choice)
5. **DON'T** check any boxes (no README, no .gitignore, no license)
6. Click **"Create repository"**

## Step 3: Commit Your Code

```bash
cd c:\project\local\MyRA

# Commit the files
git commit -m "Initial commit: Research Assistant web app"

# Switch to main branch
git branch -M main
```

## Step 4: Connect to GitHub

Replace `YOUR_USERNAME` with your actual GitHub username:

```bash
git remote add origin https://github.com/YOUR_USERNAME/research-assistant.git
```

## Step 5: Push to GitHub

```bash
git push -u origin main
```

If GitHub asks for credentials:
- **Username:** Your GitHub username
- **Password:** Use a **Personal Access Token** (not your password)

### How to create Personal Access Token:
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: "Research Assistant"
4. Check: `repo` (full control of private repositories)
5. Click "Generate token"
6. **Copy the token** and use it as password when pushing

## Step 6: Verify

Go to your GitHub repository:
```
https://github.com/YOUR_USERNAME/research-assistant
```

You should see all your files!

## Step 7: Deploy to Streamlit (Next!)

Once your code is on GitHub:

1. Go to: https://share.streamlit.io/
2. Click "New app"
3. Sign in with GitHub
4. Select your repository: `research-assistant`
5. Main file: `web_app.py`
6. Click "Deploy"

**Done!** You'll get a URL to share with anyone!

---

## Quick Commands Summary

```bash
# 1. Set identity (once)
git config --global user.email "your-email@gmail.com"
git config --global user.name "Your Name"

# 2. Commit
git commit -m "Initial commit: Research Assistant web app"

# 3. Switch to main
git branch -M main

# 4. Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/research-assistant.git

# 5. Push
git push -u origin main
```

---

## Troubleshooting

### "Authentication failed"
- Use Personal Access Token as password
- Get it from: https://github.com/settings/tokens

### "Repository not found"
- Make sure you created the repo on GitHub first
- Check the username in the URL is correct

### "Permission denied"
- Make sure the Personal Access Token has `repo` scope
- Try creating a new token

---

## What's Next?

After pushing to GitHub, follow **DEPLOY_NOW.md** to deploy to Streamlit Cloud!
