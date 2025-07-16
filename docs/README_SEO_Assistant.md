# 🚀 AI SEO Assistant - YouTube Channel Analysis

A fully private, local AI-powered SEO assistant for YouTube channel analysis. No user accounts, no login, no cloud storage - everything runs locally on your machine.

## ✨ Features

- **Private & Local**: All data stored locally under `strategy_storage/`
- **ChatGPT-like Interface**: Modern, dark theme with rounded edges
- **AI-Powered Analysis**: Leverages existing GeminiClient for SEO insights
- **Strategy Snapshots**: Automatically saves all conversations with timestamps
- **Thread-Safe**: Production-ready with proper error handling
- **No Build Tools**: Pure HTML/CSS/JS frontend

## 🏗️ Architecture

```
├── backend/
│   ├── api.py              # FastAPI server with /ask, /strategies, /timeline
│   ├── ai_pipeline.py      # AI processing pipeline
│   ├── memory.py           # Local file-based strategy storage
│   └── time_tracker.py     # Timestamp utilities
├── frontend/
│   ├── index.html          # ChatGPT-like interface
│   ├── app.js              # Frontend logic
│   └── styles.css          # Modern dark theme
├── strategy_storage/       # JSON files with timestamps
└── run.sh                  # One-click startup script
```

## 🚀 Quick Start

1. **Run the assistant:**
   ```bash
   ./run.sh
   ```

2. **That's it!** The script will:
   - Create a virtual environment
   - Install dependencies
   - Start the FastAPI backend
   - Open your browser to the interface

## 📋 Prerequisites

- Python 3.8 or higher
- pip3 package manager
- Modern web browser

## 🎯 Usage

### Basic Chat
- Type your SEO questions in the chat interface
- Get AI-powered recommendations and strategies
- All conversations are automatically saved

### Strategy Management
- Click the sidebar toggle (☰) to view saved strategies
- Search through your conversation history
- Click any strategy to view the full conversation

### API Endpoints

The backend provides several endpoints:

- `POST /ask` - Send questions to the AI
- `GET /strategies` - List all saved strategies
- `GET /timeline` - Get strategies from last N days
- `GET /health` - Check system status
- `GET /stats` - View storage statistics

### Sample Questions

Try asking questions like:
- "How can I improve my YouTube SEO?"
- "What makes a good thumbnail?"
- "How to optimize video titles for discovery?"
- "Best practices for YouTube descriptions?"
- "How to analyze my competitor's strategy?"

## 🛠️ Configuration

### Environment Variables
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_gemini_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### Storage Configuration
- Default storage: `./strategy_storage/`
- File format: JSON with timestamps
- Naming: `2025-01-15T12:30:00_chat.json`

## 🔧 Development

### Running in Development Mode
```bash
# Start backend only
cd backend
python3 -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload

# Open frontend
open http://127.0.0.1:8000
```

### Installing Dependencies
```bash
# Using requirements_seo.txt
pip install -r requirements_seo.txt

# Or using existing requirements.txt
pip install -r requirements.txt
```

### Testing
```bash
# Run health check
curl http://127.0.0.1:8000/health

# Test ask endpoint
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How to optimize YouTube titles?", "label": "test"}'
```

## 📁 File Structure

### Strategy Storage
Each conversation is saved as a JSON file:
```json
{
  "timestamp": "2025-01-15T12:30:00.123456+00:00",
  "human_time": "2025-01-15 12:30:00 UTC",
  "label": "chat",
  "question": "How to optimize YouTube titles?",
  "ai_response": "To optimize YouTube titles...",
  "metadata": {
    "model": "gemini-pro",
    "processing_time": 2.34
  },
  "version": "1.0"
}
```

### Frontend Structure
- **index.html**: Main interface with ChatGPT-like design
- **app.js**: Handles API calls, message management, sidebar
- **styles.css**: Modern dark theme with CSS variables

## 🛡️ Security & Privacy

- **No External Connections**: All data stays local
- **No User Accounts**: No login or registration required
- **Thread-Safe**: Proper locking for concurrent access
- **Fallback Handling**: Graceful degradation when AI fails
- **Local Storage Only**: Data never leaves your machine

## 🎨 Customization

### Themes
Modify CSS variables in `styles.css`:
```css
:root {
    --primary-bg: #1a1a1a;
    --accent-color: #4a9eff;
    --text-primary: #ffffff;
    /* ... */
}
```

### AI Prompts
Customize SEO context in `backend/ai_pipeline.py`:
```python
self.seo_context = """
You are a YouTube SEO expert. Your role is to:
1. Analyze YouTube channel performance data
2. Provide actionable SEO recommendations
...
"""
```

## 🔧 Troubleshooting

### Common Issues

1. **Port 8000 in use**
   ```bash
   # Find and kill process
   lsof -ti:8000 | xargs kill -9
   ```

2. **Python not found**
   ```bash
   # Install Python 3.8+
   brew install python3  # macOS
   sudo apt install python3  # Ubuntu
   ```

3. **Dependencies fail to install**
   ```bash
   # Upgrade pip
   pip install --upgrade pip
   
   # Install in virtual environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements_seo.txt
   ```

### Debug Mode
Set environment variable for detailed logging:
```bash
export DEBUG=1
./run.sh
```

## 📈 Performance

- **Memory Usage**: ~50MB for backend
- **Storage**: ~1KB per conversation
- **Response Time**: 2-5 seconds (depends on AI model)
- **Concurrent Users**: Supports multiple browser tabs

## 🤝 Contributing

This is a self-contained local application. To modify:

1. Edit backend files in `backend/`
2. Update frontend files in `frontend/`
3. Test with `./run.sh`
4. All changes are local to your machine

## 📄 License

This project is designed for personal use. All AI responses are powered by your own API keys and run locally.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your Gemini API key is configured
3. Ensure Python 3.8+ is installed
4. Try running in a fresh virtual environment

---

**Happy SEO analyzing! 🎯** 