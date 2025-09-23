# Chrome Extension History - V0.5

A Chrome extension that organizes your browsing history into thematic clusters using AI-powered analysis, with a modern React dashboard.

## 🎯 Features

- **AI-Powered Clustering**: LLM-driven thematic analysis of browsing sessions
- **React Dashboard**: Modern UI with real-time state management
- **Session Organization**: Time-based grouping of browsing history
- **Multi-Provider LLM**: Google Gemini, OpenAI, Anthropic, Ollama support
- **Local Processing**: Privacy-first with Docker backend

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Chrome browser
- LLM API Key (Google Gemini recommended)

### 1. Start Backend
```powershell
.\scripts\dev_up.ps1
```

### 2. Load Extension
1. Go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" → select `extension/` folder

### 3. Use Dashboard
1. Click extension icon
2. Click "📊 Dashboard" 
3. Click "Refresh Analysis" to see AI clusters

## 🏗️ Architecture

```
Chrome Extension + React Frontend → FastAPI Backend → LLM Providers
```

- **Frontend**: React + TypeScript with ExtensionBridge pattern
- **Backend**: Python FastAPI with LLM clustering service
- **Data Flow**: Chrome APIs → Session grouping → AI clustering → React UI

## 🔧 Configuration

Set API keys in `docker-compose.yml`:
```yaml
environment:
  - GOOGLE_API_KEY=your_key_here
```

## 🛡️ Privacy

- All processing happens locally
- No browsing data leaves your machine
- Only metadata sent to LLM providers

---

**Version 0.5** - React Frontend Implementation 🚀