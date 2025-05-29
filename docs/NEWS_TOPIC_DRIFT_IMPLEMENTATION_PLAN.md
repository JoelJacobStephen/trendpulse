# TrendPulse - Implementation Plan

Transform the existing poetry meta-patterns project into a real-time TrendPulse analysis tool.

## Project Overview

Convert the current poetry thematic analysis system into a news aggregation and topic trending platform that:

- Automatically gathers news stories from global sources
- Groups articles into broad themes using TensorFlow/ML
- Visualizes topic popularity changes over time and geography
- Provides real-time updates and trend predictions
- Features an interactive map showing topic prevalence by country

## Phase 1: Backend Infrastructure Setup

### 1.1 Create News Data Pipeline

**Files to Create:**

- `backend/news_aggregator.py` - Main news collection service
- `backend/data_sources.py` - Configuration for news APIs
- `backend/models.py` - SQLAlchemy/Pydantic models for news articles
- `backend/preprocessing.py` - Text cleaning and standardization
- `backend/database.py` - PostgreSQL database connection and session management

**Dependencies to Add:**

```python
# requirements.txt additions
newsapi-python==0.2.6
requests==2.31.0
beautifulsoup4==4.12.2
tensorflow==2.13.0
transformers==4.33.2
pandas==2.0.3
numpy==1.24.3
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.20
psycopg2-binary==2.9.7
alembic==1.12.1
python-dotenv==1.0.0
spacy==3.6.1
geopy==2.4.0
schedule==1.2.0
pydantic==2.4.2
```

**Implementation Steps:**

1. Set up NewsAPI, Guardian API, Reuters API integration
2. Create RSS feed parsers for major news outlets
3. Implement web scraping for additional sources
4. Build article deduplication system
5. Create database schema for storing articles

### 1.2 ML Topic Classification System

**Files to Create:**

- `backend/topic_classifier.py` - TensorFlow-based topic classification
- `backend/theme_mapping.py` - Map news topics to broad themes
- `backend/embedding_service.py` - Text embedding generation

**Implementation Steps:**

1. Adapt existing poetry themes to news categories:

   - Politics & Elections → Society & Politics
   - Technology & Innovation → New theme
   - Climate & Environment → Nature & Environment
   - Health & Medicine → Body & Health
   - Business & Economy → New theme
   - Sports & Entertainment → Arts & Culture
   - War & International → War & Conflict

2. Fine-tune BERT/RoBERTa model for news classification
3. Implement TensorFlow Serving for real-time inference
4. Create topic confidence scoring system

### 1.3 Geographic Detection Service

**Files to Create:**

- `backend/geo_detection.py` - Extract geographic mentions from articles
- `backend/country_mapping.py` - Map locations to countries

**Implementation Steps:**

1. Use spaCy NER for location extraction
2. Implement geopy for coordinate resolution
3. Create country relevance scoring algorithm
4. Handle multi-country news stories

## Phase 2: Database and API Layer

### 2.1 Database Schema Design

**Files to Modify/Create:**

- `backend/database.py` - PostgreSQL connection and ORM setup
- `backend/migrations/` - Alembic database migration scripts

**Schema Structure (PostgreSQL):**

```sql
articles (
  id, title, content, url, source,
  published_date, country, confidence_score,
  primary_theme, secondary_themes
)

topic_trends (
  theme, country, date, article_count,
  trend_score, prediction_confidence
)

sources (
  id, name, url, credibility_score,
  country, language, last_updated
)
```

### 2.2 REST API Development

**Files to Create:**

- `backend/api/routes.py` - FastAPI router endpoints
- `backend/api/schemas.py` - Pydantic response/request schemas
- `backend/api/dependencies.py` - FastAPI dependencies (auth, DB sessions)
- `backend/main.py` - FastAPI application entry point

**API Endpoints:**

- `GET /api/topics` - List all available topics
- `GET /api/trends/{topic}` - Get trend data for specific topic
- `GET /api/countries/{country}/topics` - Topics by country
- `GET /api/live` - Real-time trending topics
- `GET /api/predictions` - ML trend predictions

## Phase 3: Frontend Transformation

### 3.1 Component Architecture Redesign

**Files to Modify:**

- `frontend/src/components/ThemeSelector.vue` → `TopicSelector.vue`
- `frontend/src/components/YearSlider.vue` → `DateRangeSlider.vue`
- `frontend/src/components/ThemeVisualization.vue` → `WorldMapVisualization.vue`
- `frontend/src/components/SummarySection.vue` → `TrendAnalysis.vue`

**New Components to Create:**

- `frontend/src/components/LiveFeed.vue` - Real-time news updates
- `frontend/src/components/PredictionPanel.vue` - Trend predictions
- `frontend/src/components/CountryDetail.vue` - Country-specific view
- `frontend/src/components/TopicTimeline.vue` - Topic evolution over time

### 3.2 Interactive World Map

**Dependencies to Add:**

```json
"dependencies": {
  "leaflet": "^1.9.4",
  "vue3-leaflet": "^0.8.0",
  "d3": "^7.8.5",
  "chart.js": "^4.4.0",
  "vue-chartjs": "^5.2.0"
}
```

**Implementation:**

1. Replace static country comparison with interactive world map
2. Implement color-coded intensity mapping
3. Add hover tooltips with detailed statistics
4. Create zoom functionality for regional analysis

### 3.3 Real-time Data Integration

**Files to Create:**

- `frontend/src/services/WebSocketService.js` - Real-time updates
- `frontend/src/services/APIService.js` - HTTP API calls
- `frontend/src/store/index.js` - Vuex state management

**Implementation:**

1. Start with simple HTTP polling for updates (upgrade to WebSockets later)
2. Implement auto-refresh for trending topics every 5 minutes
3. Add notification system for significant topic spikes
4. Create basic caching with browser storage (upgrade to Redis later)

## Phase 4: Advanced Analytics and ML

### 4.1 TensorFlow Integration

**Files to Create:**

- `backend/ml/trend_predictor.py` - LSTM model for trend prediction
- `backend/ml/anomaly_detector.py` - Detect unusual topic spikes
- `backend/ml/similarity_engine.py` - Find related topics/countries

**TensorFlow Models:**

1. **Topic Classification Model:**

   ```python
   # Use pre-trained transformer + custom classification head
   base_model = TFAutoModel.from_pretrained('distilbert-base-uncased')
   classification_head = tf.keras.Sequential([
       tf.keras.layers.Dense(512, activation='relu'),
       tf.keras.layers.Dropout(0.3),
       tf.keras.layers.Dense(len(NEWS_TOPICS), activation='softmax')
   ])
   ```

2. **Trend Prediction Model:**
   ```python
   # LSTM for time series forecasting
   model = tf.keras.Sequential([
       tf.keras.layers.LSTM(128, return_sequences=True),
       tf.keras.layers.LSTM(64),
       tf.keras.layers.Dense(32, activation='relu'),
       tf.keras.layers.Dense(1, activation='linear')
   ])
   ```

### 4.2 Data Processing Pipeline

**Files to Create:**

- `backend/etl/news_processor.py` - ETL pipeline for news data
- `backend/etl/trend_calculator.py` - Calculate trending scores
- `backend/etl/scheduler.py` - Simple Python scheduling with `schedule` library

**Processing Steps:**

1. Hourly news collection from all sources using simple Python scheduler
2. Real-time topic classification
3. Geographic relevance scoring
4. Trend calculation and storage
5. Prediction model updates (run daily instead of real-time initially)

## Phase 5: Simple Deployment Setup

### 5.1 Basic Production Setup

**Files to Create:**

- `backend/requirements.txt` - Python dependencies
- `backend/config.py` - Configuration management
- `backend/run.py` - Application entry point
- `.env` - Environment variables for development

**Simple Deployment Strategy:**

- Use PostgreSQL from the start (cloud-hosted: Supabase, PlanetScale, or Railway)
- Run background tasks with simple Python scheduling (no Celery initially)
- Deploy FastAPI backend to Railway, Render, or Heroku
- Deploy frontend to Vercel or Netlify
- Use in-memory caching initially (Redis can be added later)

### 5.2 Environment Setup

**Development Environment:**

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Database setup (using cloud PostgreSQL or local)
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Run FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend setup
cd frontend
npm install
npm run serve
```

**Production Environment:**

- Deploy frontend to Vercel/Netlify (static hosting)
- Deploy FastAPI backend to Railway/Render/Heroku
- Use cloud PostgreSQL services (Supabase, Railway, or AWS RDS)
- Environment variables for database connection and API keys

## Phase 6: Data Migration and Testing

### 6.1 Data Structure Migration

**Migration Steps:**

1. Export existing poetry themes as reference
2. Create news topic taxonomy based on common themes
3. Set up initial news data collection (last 30 days)
4. Validate topic classification accuracy
5. Generate initial trend calculations

### 6.2 Testing Strategy

**Files to Create:**

- `tests/unit/` - Unit tests for all modules
- `tests/integration/` - API and database tests
- `tests/e2e/` - Frontend automation tests

**Test Coverage:**

- News aggregation accuracy
- Topic classification precision/recall
- Geographic detection accuracy
- Real-time update performance
- Frontend responsiveness

## Implementation Timeline

**Week 1-2:** Backend infrastructure and news aggregation (PostgreSQL + FastAPI)
**Week 3-4:** ML models and topic classification (basic TensorFlow models)
**Week 5-6:** Database setup and API development (FastAPI REST API)
**Week 7-8:** Frontend transformation and map integration
**Week 9-10:** Basic real-time features (polling instead of WebSockets initially)
**Week 11-12:** Advanced analytics and prediction models
**Week 13-14:** Testing, optimization, and simple deployment (Heroku/Vercel)

## Success Metrics

1. **Data Quality:**

   - 95%+ topic classification accuracy
   - 90%+ geographic detection precision
   - <5 minute data freshness

2. **Performance:**

   - <2 second page load times
   - <500ms API response times
   - 99.9% uptime

3. **User Engagement:**
   - Interactive map usage metrics
   - Real-time feature adoption
   - Prediction accuracy feedback

## Risk Mitigation

1. **API Rate Limits:** Implement rotating API keys and basic caching
2. **Data Quality:** Multiple validation layers and human oversight
3. **Scalability:** Start simple, add complexity as needed (polling → WebSockets, single instance → load balancing)
4. **Legal Compliance:** Respect robots.txt and fair use policies

## Simplified Architecture Benefits

1. **Faster Development:** No complex infrastructure setup needed
2. **Lower Costs:** Free tier deployments for initial testing
3. **Easier Debugging:** Simpler stack means fewer moving parts
4. **Gradual Scaling:** Add complexity only when needed

This simplified implementation plan provides a comprehensive roadmap for transforming the poetry analysis project into a TrendPulse analysis tool while starting simple and scaling up gradually.
