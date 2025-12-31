# 🔍 Research Assistant Web App

AI-powered research tool that works on **any device** - Mac, Windows, Linux, iOS, Android.

## ✨ Features

- **Intelligent Scope Detection** - AI analyzes your question and proposes research scope
- **Interactive Planning** - Review and approve sub-questions before research starts
- **Deep Web Research** - Searches 50+ sources per question
- **Executive Memo** - Professional summary with key findings
- **Excel Reports** - 3-tab workbook with memo, synthesis, and raw data

## 🚀 Try It Now

**Live Demo:** [Your deployed URL will go here]

No installation needed - just open in your browser!

## 📋 Requirements

Users need two API keys (both have free trials):
- **Anthropic API Key** - Get from https://console.anthropic.com/
- **Serper API Key** - Get from https://serper.dev/

## 💻 Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run web_app.py
```

Open http://localhost:8501

## 📱 How It Works

1. **Enter your research question**
2. **Review & approve the scope** - AI detects key entities and focus areas
3. **Review & approve the plan** - See all sub-questions before research starts
4. **Wait 5-10 minutes** - App searches the web and generates insights
5. **Download your Excel report** - Professional 3-tab workbook

## 🌐 Deploy Your Own

See [DEPLOY_NOW.md](DEPLOY_NOW.md) for step-by-step instructions.

Free deployment on:
- Streamlit Community Cloud
- Hugging Face Spaces

## 📊 Example Research Questions

- "What is the market size of electric vehicles in the US in 2024-2025?"
- "What are the latest developments in quantum computing commercialization?"
- "What is the competitive landscape of food delivery apps in Southeast Asia?"

## 🛠️ Built With

- **Streamlit** - Web framework
- **Anthropic Claude Sonnet 4.5** - AI research agent
- **Serper** - Web search API
- **Python 3.12**

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Feel free to open issues or pull requests.
