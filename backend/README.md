# TrendPulse - Backend API

FastAPI-based backend for the TrendPulse application that tracks news topic trends across time and geography.

## Single Entry Point

**`run.py` is the ONLY script you need to run the backend.** All functionality is accessible through this single script with different commands.

```bash
# Show all available commands
python run.py help

# Start development server (default command)
python run.py server
# or simply
python run.py

# Start production server
python run.py prod

# Set up database
python run.py setup

# Run background scheduler
python run.py scheduler

# Run one-time news fetch
python run.py fetch

# Calculate trends
python run.py trend

# Reset database
python run.py reset

# Test API endpoints
python run.py test
```

## Features

- **News Aggregation**: Collects news from multiple sources (RSS feeds, NewsAPI, Guardian API)
- **Topic Classification**: Uses TensorFlow and transformers for automated topic classification
- **Geographic Detection**: Extracts geographic information from news articles
- **Trend Analysis**: Calculates topic trends over time and geography
- **Predictive Analytics**: ML-based trend predictions
- **RESTful API**: Complete API for frontend integration
- **Background Processing**: Automated news fetching and trend calculation

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Database

Make sure you have PostgreSQL running, then:

```bash
# Create database
createdb trendpulse

# Set database URL
export DATABASE_URL="postgresql://username:password@localhost:5432/trendpulse"
```

### 3. Initialize and Start

```bash
# Set up database tables and default sources
python run.py setup

# Start the development server
python run.py
```

The API will be available at `http://localhost:8000` with automatic documentation at `http://localhost:8000/docs`.

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/trendpulse

# API Keys (optional but recommended)
NEWS_API_KEY=your_newsapi_key_here
GUARDIAN_API_KEY=your_guardian_api_key_here

# Application Settings
DEBUG=True
SECRET_KEY=your_secret_key_here
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Background Task Settings
NEWS_FETCH_INTERVAL=3600
TREND_CALCULATION_INTERVAL=21600
```

### News Sources

The application uses multiple news sources:

1. **RSS Feeds** (always available):

   - BBC News
   - CNN
   - Reuters
   - NPR
   - Sky News

2. **NewsAPI.org** (requires API key):

   - Get a free key at [newsapi.org](https://newsapi.org/)
   - Provides access to thousands of news sources

3. **The Guardian API** (requires API key):
   - Get a free key at [open-platform.theguardian.com](https://open-platform.theguardian.com/)
   - High-quality journalism with detailed metadata

## API Endpoints

### Core Endpoints

- `GET /api/v1/topics` - List all available topics
- `GET /api/v1/trends/{topic}` - Get trend data for a specific topic
- `GET /api/v1/countries/{country}/topics` - Get topics by country
- `GET /api/v1/live` - Get real-time trending topics
- `GET /api/v1/predictions` - Get ML trend predictions

### Article Endpoints

- `GET /api/v1/articles/search` - Search articles with filters
- `GET /api/v1/articles/recent` - Get recent articles
- `GET /api/v1/statistics` - Get system statistics

### Admin Endpoints

- `POST /api/v1/refresh` - Manually trigger news refresh
- `GET /api/v1/health` - Health check

## Architecture

### Components

1. **News Aggregation** (`news_aggregator.py`)

   - Coordinates news collection from all sources
   - Handles article processing and deduplication

2. **Data Sources** (`data_sources.py`)

   - NewsAPI integration
   - Guardian API integration
   - RSS feed processing

3. **Text Processing** (`preprocessing.py`)

   - Article cleaning and normalization
   - Keyword extraction
   - Text preprocessing for ML models

4. **Topic Classification** (`topic_classifier.py`)

   - TensorFlow-based topic classification
   - Rule-based fallback system
   - Support for 10 news categories

5. **Geographic Detection** (`geo_detection.py`)

   - Location extraction using spaCy NER
   - Country resolution with geopy
   - Geographic confidence scoring

6. **Trend Analysis** (`etl/trend_calculator.py`)

   - Time series analysis
   - Trend score calculation
   - Predictive modeling

7. **Background Tasks** (`etl/scheduler.py`)
   - Automated news fetching
   - Periodic trend calculation
   - Data cleanup and maintenance

### Database Schema

- **Articles**: News articles with metadata
- **News Sources**: Source configuration and statistics
- **Topic Trends**: Calculated trend data over time
- **Topic Predictions**: ML-generated trend predictions

## Development

### All Development Tasks via run.py

Remember: **use `run.py` for ALL backend operations**. Here are the most common commands:

```bash
# Development server with auto-reload
python run.py server

# Background processing only
python run.py scheduler

# One-time operations
python run.py fetch      # Fetch news once
python run.py trend      # Calculate trends once
python run.py setup      # Initialize database
python run.py reset      # Reset all data

# Testing
python run.py test       # Test API endpoints
```

### Testing

```bash
# Test API endpoints (requires server to be running)
python run.py test

# Or manually test specific endpoints
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/topics
curl http://localhost:8000/api/v1/live
```

### Adding New News Sources

1. Extend `data_sources.py` with new source class
2. Add source to `NewsSourceManager.fetch_all_news()`
3. Update `news_aggregator.initialize_sources()` with default configuration

### Customizing Topics

1. Update `settings.NEWS_TOPICS` in `config.py`
2. Add keywords to `topic_classifier.topic_keywords`
3. Re-run topic classification: `POST /api/v1/refresh`

## Deployment

### Using Docker (Optional)

```bash
# Build image
docker build -t trendpulse-backend .

# Run container
docker run -p 8000:8000 -e DATABASE_URL="postgresql://..." trendpulse-backend
```

### Production Deployment

1. Use the production server command:

   ```bash
   # Recommended: use the built-in production command
   python run.py prod

   # Or manually with gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
   ```

2. Set up proper environment variables
3. Use a reverse proxy (nginx)
4. Set up monitoring and logging
5. Configure automatic backups

## Monitoring

### Health Checks

- `GET /api/v1/health` - Basic health check
- Database connectivity is monitored automatically
- External API status is checked periodically

### Logging

Logs are written to stdout with structured formatting. In production, use a log aggregation service.

### Metrics

- Article processing rates
- Topic classification accuracy
- API response times
- Background job status

## Troubleshooting

### Common Issues

1. **Database Connection Errors**

   - Check PostgreSQL is running
   - Verify DATABASE_URL is correct
   - Ensure database exists

2. **Missing Dependencies**

   - Run `pip install -r requirements.txt`
   - For spaCy: `python -m spacy download en_core_web_sm`

3. **API Key Issues**

   - NewsAPI and Guardian API keys are optional
   - RSS feeds work without API keys
   - Check API key validity and rate limits

4. **TensorFlow Issues**
   - Ensure compatible Python version (3.8-3.11)
   - For M1 Macs: use `tensorflow-macos`

### Performance Tuning

- Increase database connection pool size
- Adjust background task intervals
- Use Redis for caching (optional)
- Scale horizontally with load balancer

## Contributing

1. Follow PEP 8 style guidelines
2. Add tests for new features
3. Update documentation
4. Ensure backward compatibility

## License

[Add your license information here]
