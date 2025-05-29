# TrendPulse: Real-Time News Topic Trend Analysis

A comprehensive data-driven platform that tracks and analyzes news topic trends across time and geography, providing insights into how global events and themes evolve and spread across different regions.

## Table of Contents

- [Project Overview](#project-overview)
- [Demo](#demo)
- [Project Structure](#project-structure)
- [Features](#features)
- [Installation & Setup](#installation--setup)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Architecture](#architecture)
- [Data Sources](#data-sources)
- [Technology Stack](#technology-stack)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

TrendPulse is an intelligent news trend analysis platform that aggregates news from multiple sources, classifies articles by topic using machine learning, and tracks how different themes evolve over time and across geographical regions. The platform provides real-time insights into global news patterns, helping users understand the ebb and flow of public discourse.

Key capabilities include:

- **Multi-source News Aggregation**: Collects news from RSS feeds, NewsAPI, and The Guardian API
- **AI-powered Topic Classification**: Uses TensorFlow and transformer models for accurate topic categorization
- **Geographic Analysis**: Extracts and analyzes geographic information from news content
- **Trend Prediction**: ML-based forecasting of topic trends
- **Real-time Visualization**: Interactive dashboards showing trend evolution
- **Historical Analysis**: Track how topics have evolved over time

## Demo

<!-- **Live Demo**: [TrendPulse Application](https://trendpulse.vercel.app) -->

The interactive platform allows you to:

1. View real-time trending topics across different regions
2. Analyze historical trend data with interactive time controls
3. Compare topic prevalence between different countries
4. Access predictive analytics for emerging trends
5. Search and filter news articles by topic, location, and time

## Project Structure

```
trendpulse/
├── backend/                   # FastAPI backend server
│   ├── api/                   # API route handlers
│   ├── etl/                   # Extract, Transform, Load processes
│   │   ├── scheduler.py       # Background task scheduling
│   │   └── trend_calculator.py # Trend analysis algorithms
│   ├── ml/                    # Machine learning models
│   │   ├── topic_classifier.py # Topic classification
│   │   ├── geo_detection.py   # Geographic entity extraction
│   │   └── preprocessing.py   # Text preprocessing
│   ├── models_cache/          # Cached ML models
│   ├── config.py              # Application configuration
│   ├── database.py            # Database connection and models
│   ├── data_sources.py        # News source integrations
│   ├── news_aggregator.py     # News collection coordinator
│   ├── run.py                 # Single entry point for all operations
│   └── requirements.txt       # Python dependencies
├── frontend/                  # Vue.js frontend application
│   ├── public/                # Static assets
│   └── src/                   # Frontend source code
│       ├── components/        # Vue components
│       ├── services/          # API service layer
│       ├── store/             # State management
│       └── assets/            # Frontend assets
├── docs/                      # Documentation
├── .gitignore
└── README.md                  # Project documentation
```

## Features

### Core Functionality

- **Real-time News Monitoring**: Continuous collection from multiple news sources
- **Intelligent Topic Classification**: 10+ news categories with ML-based classification
- **Geographic Trend Analysis**: Location-based trend tracking and visualization
- **Predictive Analytics**: Machine learning models for trend forecasting
- **Search & Discovery**: Advanced filtering and search capabilities
- **Interactive Visualizations**: Time-series charts, geographic maps, and trend comparisons

### News Sources

- **RSS Feeds**: BBC, CNN, Reuters, NPR, Sky News
- **NewsAPI**: Access to thousands of global news sources
- **The Guardian API**: High-quality journalism with detailed metadata
- **Extensible Architecture**: Easy integration of additional sources

### Machine Learning Features

- **Topic Classification**: TensorFlow-based classification with transformer models
- **Named Entity Recognition**: Geographic location extraction using spaCy
- **Trend Analysis**: Time-series analysis and pattern recognition
- **Predictive Modeling**: ML-based trend forecasting

## Installation & Setup

### Prerequisites

- Python 3.8-3.11
- PostgreSQL database
- Node.js 14+ (for frontend)
- Git

### Backend Setup

1. Clone the repository:

```bash
git clone https://github.com/your-username/trendpulse.git
cd trendpulse
```

2. Set up the backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

3. Configure environment variables:

```bash
# Create .env file
echo "DATABASE_URL=postgresql://username:password@localhost:5432/trendpulse" > .env
echo "NEWS_API_KEY=your_newsapi_key_here" >> .env
echo "GUARDIAN_API_KEY=your_guardian_api_key_here" >> .env
```

4. Set up the database:

```bash
createdb trendpulse
python run.py setup
```

### Frontend Setup

1. Navigate to frontend directory:

```bash
cd ../frontend
```

2. Install dependencies:

```bash
npm install
```

## Quick Start

### Backend (Development)

**Single Entry Point**: Use `run.py` for all backend operations:

```bash
cd backend

# Start development server
python run.py server
# or simply
python run.py

# View all available commands
python run.py help

# Start background processing
python run.py scheduler

# Fetch news manually
python run.py fetch

# Calculate trends
python run.py trend
```

### Frontend (Development)

```bash
cd frontend

# Start development server
npm run serve

# Build for production
npm run build
```

Access the application at:

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## API Documentation

### Core Endpoints

- `GET /api/v1/topics` - List all available topics
- `GET /api/v1/trends/{topic}` - Get trend data for a specific topic
- `GET /api/v1/countries/{country}/topics` - Get topics by country
- `GET /api/v1/live` - Get real-time trending topics
- `GET /api/v1/predictions` - Get ML trend predictions

### Search & Discovery

- `GET /api/v1/articles/search` - Search articles with filters
- `GET /api/v1/articles/recent` - Get recent articles
- `GET /api/v1/statistics` - Get system statistics

### Administrative

- `POST /api/v1/refresh` - Manually trigger news refresh
- `GET /api/v1/health` - Health check endpoint

Interactive API documentation available at `/docs` when running the server.

## Architecture

### Backend Architecture

- **FastAPI Framework**: High-performance async Python web framework
- **PostgreSQL Database**: Robust data storage with SQLAlchemy ORM
- **Background Tasks**: Automated news fetching and trend calculation
- **Machine Learning Pipeline**: TensorFlow and spaCy for content analysis
- **RESTful API**: Clean, documented API for frontend integration

### Frontend Architecture

- **Vue.js Framework**: Progressive JavaScript framework
- **Component-based Design**: Modular, reusable UI components
- **State Management**: Centralized application state
- **Responsive Design**: Mobile-first, responsive user interface

### Data Pipeline

1. **Collection**: Multi-source news aggregation
2. **Processing**: Text preprocessing and cleaning
3. **Classification**: ML-based topic classification
4. **Analysis**: Trend calculation and geographic analysis
5. **Storage**: Structured data storage in PostgreSQL
6. **API**: RESTful API for data access
7. **Visualization**: Interactive frontend dashboards

## Data Sources

### RSS Feeds (Always Available)

- BBC News, CNN, Reuters, NPR, Sky News
- Real-time updates without API key requirements

### NewsAPI (Optional - API Key Required)

- Access to thousands of news sources worldwide
- Free tier: 1,000 requests/day
- Get your key at [newsapi.org](https://newsapi.org/)

### The Guardian API (Optional - API Key Required)

- High-quality journalism with rich metadata
- Free tier available
- Get your key at [open-platform.theguardian.com](https://open-platform.theguardian.com/)

## Technology Stack

### Backend

- **Python 3.8-3.11**
- **FastAPI** - Web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **TensorFlow** - Machine learning
- **spaCy** - Natural language processing
- **Transformers** - Pre-trained models
- **Pandas** - Data analysis
- **Schedule** - Background tasks

### Frontend

- **Vue.js 3** - Frontend framework
- **Vue Router** - Routing
- **Vuex** - State management
- **Chart.js** - Data visualization
- **Tailwind CSS** - Styling
- **Axios** - HTTP client

### Infrastructure

- **Docker** - Containerization (optional)
- **Gunicorn** - WSGI server
- **Nginx** - Reverse proxy (production)

## Deployment

### Development Deployment

```bash
# Backend
cd backend
python run.py server

# Frontend (separate terminal)
cd frontend
npm run serve
```

### Production Deployment

```bash
# Backend production server
cd backend
python run.py prod

# Frontend build
cd frontend
npm run build
```

### Docker Deployment (Optional)

```bash
# Build and run with Docker
docker build -t trendpulse-backend ./backend
docker run -p 8000:8000 -e DATABASE_URL="postgresql://..." trendpulse-backend
```

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Follow code style**: PEP 8 for Python, ESLint for JavaScript
3. **Add tests** for new features
4. **Update documentation** as needed
5. **Submit a pull request** with a clear description

### Development Workflow

1. Set up development environment
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes and test thoroughly
4. Update documentation if needed
5. Submit pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**TrendPulse** - Tracking the pulse of global news trends with AI-powered analytics.
