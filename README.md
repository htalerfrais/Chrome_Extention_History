# Chrome Extension History - V0.2

A Chrome extension that organizes your browsing history into thematic clusters using NLP processing, providing a structured dashboard view of your browsing patterns.

## 🎯 Features

### V0.2 - Session Clustering & Dashboard
- **Dockerized FastAPI Backend**: Local NLP processing with clustering algorithms
- **Session-based Organization**: Groups browsing history into time-based sessions
- **Thematic Clustering**: Identifies browsing topics and themes automatically
- **Interactive Dashboard**: Dedicated page showing clustered browsing history
- **Real-time Analysis**: Processes your Chrome history and displays insights

## 🏗️ Project Structure

```
Chrome_Extension_History/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI application
│   │   ├── models/            # Pydantic models
│   │   └── services/          # Clustering logic
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
- Groups browsing history by time gaps (default: 30 minutes)
- Filters out sessions with too few items

### 2. Clustering Algorithm
- Analyzes URLs and page titles for themes
- Uses domain-specific keywords and patterns
- Groups similar browsing activities together

### 3. Theme Detection
- **Development**: GitHub, Stack Overflow, documentation sites
- **Social Media**: Twitter, Reddit, Facebook, etc.
- **Shopping**: Amazon, e-commerce sites
- **Learning**: Educational content, tutorials
- **Entertainment**: YouTube, Netflix, media sites
- **And more...**

### 4. Dashboard Display
- Shows confidence scores for each cluster
- Displays most visited domains
- Provides session statistics and date ranges

## 🔧 Configuration

### Backend Configuration
Environment variables can be set in `docker-compose.yml`:

```yaml
environment:
  - LOG_LEVEL=info
  - MAX_CLUSTERS=10
  - MIN_CLUSTER_SIZE=2
```

### Extension Configuration
Edit `extension/utils/config.js` to:
- Switch between development/production APIs
- Adjust clustering parameters
- Configure request timeouts

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
Clusters browsing sessions into themes
- **Input**: Array of browsing sessions
- **Output**: Object with clusters array and statistics


## 🛡️ Privacy & Security

- **Local Processing**: All analysis happens locally via Docker
- **No Data Transmission**: Your browsing history never leaves your machine
- **Chrome Permissions**: Only accesses history data when you explicitly request analysis

## 🎨 Customization

### Adding New Themes
Edit `backend/app/services/clustering_service.py`:

```python
self.theme_patterns = {
    'Your Theme': ['keyword1', 'keyword2', 'keyword3'],
    # ... existing themes
}
```

### Styling the Dashboard
Modify `extension/styles/dashboard.css` to customize the appearance.

## 🚧 Roadmap

- [ ] Advanced NLP with spaCy/transformers
- [ ] Export functionality (PDF, CSV)
- [ ] Time-based filtering
- [ ] Custom theme creation
- [ ] Cloud deployment option
- [ ] Multi-language support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Version 0.2** - Session Clustering & Dashboard Implementation