# Chrome Extension History - V0.4

A Chrome extension that organizes your browsing history into thematic clusters using AI-powered LLM processing, providing a structured dashboard view of your browsing patterns.

## 🎯 Features

### V0.4 - AI-Powered Session Clustering & Dashboard
- **Dockerized FastAPI Backend**: Local AI processing with LLM-powered clustering
- **Session-based Organization**: Groups browsing history into time-based sessions
- **AI-Driven Thematic Clustering**: Uses LLM to intelligently identify browsing topics and themes
- **Interactive Dashboard**: Dedicated page showing AI-generated clustered browsing history
- **Real-time Analysis**: Processes your Chrome history and displays AI-powered insights
- **Multi-Provider LLM Support**: Google Gemini, OpenAI GPT, Anthropic Claude, and Ollama

## 🏗️ Project Structure

```
Chrome_Extension_History/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI application
│   │   ├── models/            # Pydantic models
│   │   └── services/          # LLM clustering & AI services
│   │       └── providers/     # LLM provider implementations
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend container
├── extension/                 # Chrome extension
│   ├── manifest.json         # Extension manifest
│   ├── popup.html/js         # Extension popup
│   ├── dashboard.html        # Main dashboard page
│   ├── scripts/dashboard.js  # Dashboard logic
│   ├── utils/                # Utilities
│   │   ├── config.js         # API configuration
│   │   └── api_client.js     # Backend communication
│   └── styles/               # CSS styles
├── scripts/                  # Development scripts
│   ├── dev_up.ps1           # Start development environment
│   ├── dev_down.ps1         # Stop services
│   └── test_api.ps1         # Test API endpoints
└── docker-compose.yml       # Orchestration
```

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Chrome browser
- PowerShell (Windows) or adapt scripts for your shell
- **LLM API Key** (Google Gemini recommended, see Configuration section)

### 1. Start the Backend

```powershell
# Start the development environment
.\scripts\dev_up.ps1

# The backend will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 2. Load the Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" and select the `extension/` folder
4. The extension icon should appear in your toolbar

### 3. Use the Dashboard

1. Click the extension icon in Chrome toolbar
2. Click the "📊 Dashboard" button
3. The dashboard will analyze your browsing history and show thematic clusters

## 🛠️ Development

### Backend Development

The backend runs in Docker with hot reload enabled:

```powershell
# View logs
docker-compose logs -f backend

# Rebuild backend
.\scripts\build_backend.ps1

# Test API endpoints
.\scripts\test_api.ps1
```

### Extension Development

The extension files are loaded directly from the `extension/` folder. After making changes:

1. Go to `chrome://extensions/`
2. Click the refresh icon on your extension
3. Test your changes

### API Configuration

The extension can work with different backend environments:

- **Development**: `http://localhost:8000` (default)
- **Production**: Configure in `extension/utils/config.js`

## 📊 How It Works

### 1. Session Creation
- Groups browsing history by time gaps (default: 120 minutes)
- Filters out sessions with too few items
- Each session processed independently for personalized clustering

### 2. AI-Powered Clustering Process
The system uses a sophisticated two-phase LLM-driven approach:

#### **Phase 1: Cluster Identification**
- Sends simplified browsing data to LLM (titles, domains, paths, search queries)
- LLM analyzes patterns and proposes 3-8 thematic clusters
- Each cluster gets a unique ID, theme name, and descriptive summary

#### **Phase 2: Intelligent Item Assignment**
- Items processed in batches of 20 for efficiency
- LLM assigns each item to the most appropriate cluster
- Robust error handling ensures all items are categorized

### 3. AI Theme Detection
The LLM intelligently identifies themes such as:
- **Development**: Coding, GitHub, Stack Overflow, documentation
- **Social Media**: Twitter, Reddit, Facebook, LinkedIn
- **Shopping**: E-commerce, product research, reviews
- **Learning**: Educational content, tutorials, courses
- **Entertainment**: YouTube, Netflix, media consumption
- **Research**: Academic papers, news, information gathering
- **And many more** based on actual browsing patterns

### 4. Dashboard Display
- Shows AI-generated cluster themes with descriptive summaries
- Displays browsing items with favicons and metadata
- Provides session statistics and intelligent categorization
- Real-time analysis with fallback mechanisms for reliability

## 🔧 Configuration

### Backend Configuration
Environment variables can be set in `docker-compose.yml`:

```yaml
environment:
  - LOG_LEVEL=info
  - GOOGLE_API_KEY=your_google_gemini_api_key
  - OPENAI_API_KEY=your_openai_api_key  # Optional
  - ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional
  - OLLAMA_BASE_URL=http://localhost:11434  # Optional for local LLM
```

**Required**: At least one LLM API key. Google Gemini is recommended for best performance and cost efficiency.

### Extension Configuration
Edit `extension/utils/config.js` to:
- Switch between development/production APIs
- Configure request timeouts
- Adjust session grouping parameters

## 🧪 Testing

### Test the API
```powershell
.\scripts\test_api.ps1
```

### Manual Testing
1. Browse different types of websites
2. Wait a few minutes
3. Open the dashboard to see clustering results

## 📝 API Endpoints

### `GET /health`
Health check endpoint

### `POST /cluster`
AI-powered clustering of browsing sessions into themes
- **Input**: Array of browsing sessions
- **Output**: Object with AI-generated clusters array and statistics

### `POST /llm/generate`
Direct LLM text generation endpoint
- **Input**: LLM request with prompt and provider settings
- **Output**: Generated text with metadata and usage information


## 🛡️ Privacy & Security

- **Local Processing**: All analysis happens locally via Docker
- **No Data Transmission**: Your browsing history never leaves your machine
- **Chrome Permissions**: Only accesses history data when you explicitly request analysis
- **LLM API Usage**: Only simplified metadata (titles, domains) sent to LLM providers
- **Secure API Keys**: Environment-based configuration for LLM access

## 🎨 Customization

### LLM Provider Configuration
The system supports multiple LLM providers. Configure in `docker-compose.yml`:

- **Google Gemini** (Recommended): Fast, cost-effective, excellent clustering results
- **OpenAI GPT**: High-quality results with GPT-3.5/GPT-4 models
- **Anthropic Claude**: Advanced reasoning capabilities
- **Ollama**: Local LLM models for complete privacy

### Customizing Clustering Behavior
Edit `backend/app/services/clustering_service.py` to:
- Adjust batch sizes for item assignment
- Modify LLM prompts for different clustering approaches
- Configure fallback mechanisms
- Customize error handling strategies

### Styling the Dashboard
Modify `extension/styles/dashboard.css` to customize the appearance.

## 🚧 Roadmap

- [ ] Enhanced LLM prompt engineering for better clustering
- [ ] Export functionality (PDF, CSV)
- [ ] Time-based filtering and session management
- [ ] Custom clustering strategies per user preferences
- [ ] Cloud deployment option with secure API key management
- [ ] Multi-language support for international browsing patterns
- [ ] Advanced analytics and browsing insights
- [ ] Integration with more LLM providers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Version 0.4** - AI-Powered LLM Clustering Implementation 🚀