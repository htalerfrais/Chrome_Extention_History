# Chrome Extension History 🧠

> **🚧 Work in Progress** - This project is actively being developed.

## What is this?

A Chrome extension that acts as your **intelligent navigation assistant**. Ever felt overwhelmed by dozens of open tabs? This extension helps you **close tabs without worry** by automatically organizing your browsing history into thematic clusters (work, hobbies, research, etc.) and making them easily accessible through a friendly dashboard.

Think of it as a smart memory for your browsing sessions—everything you've explored is preserved, organized, and ready to chat about.

## The Goal

Reduce the mental load of managing multiple tabs by providing an intelligent interface that:
- **Organizes** your browsing history into clear thematic groups
- **Preserves** important topics you've explored
- **Lets you chat** with your browsing history naturally (e.g., "What seemed urgent today?")

## Architecture (at a glance)

```
Chrome Extension (React UI) → FastAPI Backend → PostgreSQL + LLM Analysis
```

The extension collects your history, groups it into sessions, and uses AI to cluster pages by theme. Everything is cached for fast access, and you can interact with your history through a conversational interface.

## Understanding the Repo

- `extension/` - Chrome extension code (background worker + React dashboard)
- `backend/` - FastAPI server with clustering and chat services
- `frontend/` - React frontend source (builds into `extension/dashboard-assets/`)
- `.cursor/rules/` - Project documentation (specifications & architecture details)

---

*Still in development, but already useful! 🚀*
