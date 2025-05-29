# TrendPulse Backend - Complete Setup Guide

## 🚀 Quick Setup Checklist

### Required (Core Functionality)

- [x] **Database**: Neon Cloud PostgreSQL
- [x] **Dependencies**: Python packages

### Optional (Enhanced Features)

- [ ] **NewsAPI Key**: For comprehensive news coverage
- [ ] **Guardian API Key**: For high-quality journalism
- [ ] **spaCy Model**: For better geographic detection

---

## 📋 Step-by-Step Setup

### 1. Set Up Neon Database

1. **Create Neon Account**

   - Go to [https://console.neon.tech/](https://console.neon.tech/)
   - Sign up for a free account
   - Create a new project

2. **Get Database Connection String**
   - In your Neon dashboard, go to "Connection Details"
   - Copy the connection string (it looks like this):
   ```
   postgresql://username:password@ep-xxx-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```

### 2. Create Environment File

1. **Copy the example file**:

   ```bash
   cd backend
   cp env_example.txt .env
   ```

2. **Edit `.env` file** with your actual values:

   ```bash
   # Replace with your Neon connection string
   DATABASE_URL=postgresql://your_username:your_password@your_neon_host/your_database?sslmode=require

   # Keep these for now (we'll add API keys later)
   NEWS_API_KEY=
   GUARDIAN_API_KEY=

   # Application settings (you can keep these defaults)
   DEBUG=True
   SECRET_KEY=your-secret-key-here-make-it-long-and-random
   CORS_ORIGINS=http://localhost:3000,http://localhost:8080
   ```

### 3. Install Dependencies

```bash
# Make sure you're in the backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install spaCy language model (optional but recommended)
python -m spacy download en_core_web_sm
```

### 4. Initialize Database

```bash
# Set up database tables and default sources
python run.py setup
```

### 5. Test Basic Functionality

```bash
# Run initial news fetch (uses RSS feeds, no API keys needed)
python run.py fetch

# Start the server
python run.py server
```

The API will be running at `http://localhost:8000`

Test it by visiting:

- `http://localhost:8000/docs` (API documentation)
- `http://localhost:8000/api/v1/health` (health check)
- `http://localhost:8000/api/v1/topics` (available topics)

---

## 🔑 Optional: Add API Keys for Enhanced Features

### NewsAPI Setup (Recommended)

1. **Sign up**: Go to [https://newsapi.org/](https://newsapi.org/)
2. **Get free API key**: Free tier gives you 1,000 requests/day
3. **Add to `.env`**:
   ```
   NEWS_API_KEY=your_actual_newsapi_key_here
   ```

**Benefits**:

- Access to 80,000+ news sources
- Country-specific news filtering
- Categorized news (business, sports, tech, etc.)
- Real-time news updates

### Guardian API Setup (Recommended)

1. **Sign up**: Go to [https://open-platform.theguardian.com/access/](https://open-platform.theguardian.com/access/)
2. **Get free API key**: No daily limits, 12 calls/second
3. **Add to `.env`**:
   ```
   GUARDIAN_API_KEY=your_actual_guardian_key_here
   ```

**Benefits**:

- High-quality journalism
- Detailed article metadata
- Rich tagging system
- International coverage

---

## ⚙️ Configuration Options

### Production Settings

For production deployment, update these in your `.env`:

```bash
DEBUG=False
SECRET_KEY=a-very-long-random-secret-key-for-production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Background Task Intervals

Adjust how often the system fetches news and calculates trends:

```bash
# Fetch news every 30 minutes (instead of 1 hour)
NEWS_FETCH_INTERVAL=1800

# Calculate trends every 3 hours (instead of 6 hours)
TREND_CALCULATION_INTERVAL=10800
```

### ML Model Configuration

```bash
# Use a different model (optional)
MODEL_NAME=distilbert-base-uncased

# Custom cache directory (optional)
HUGGINGFACE_CACHE_DIR=./ml_models
```

---

## 🧪 Testing Your Setup

### 1. Test Database Connection

```bash
python -c "from database import SessionLocal; db = SessionLocal(); print('✅ Database connected!')"
```

### 2. Test News Fetching

```bash
python run.py fetch
```

Should output something like: `News fetch completed: X articles processed`

### 3. Test API Endpoints

```bash
# Test health
curl http://localhost:8000/api/v1/health

# Test topics
curl http://localhost:8000/api/v1/topics

# Test recent articles
curl http://localhost:8000/api/v1/articles/recent
```

### 4. Test Background Scheduler

```bash
# Run scheduler (Ctrl+C to stop)
python run.py scheduler
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Database Connection Error**

```bash
# Check your DATABASE_URL format
# Should be: postgresql://username:password@host/database?sslmode=require
```

**2. Missing Dependencies**

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**3. API Keys Not Working**

- Check for typos in `.env` file
- Verify API keys are active in respective dashboards
- The system works without API keys (uses RSS feeds)

**4. Import Errors**

```bash
# Make sure you're in the backend directory
cd backend
# Make sure virtual environment is activated
source venv/bin/activate
```

**5. TensorFlow Issues**

```bash
# On M1 Macs, you might need:
pip install tensorflow-macos tensorflow-metal
```

---

## 📊 What Works Without API Keys

The system is designed to work even without API keys:

✅ **RSS Feed Sources** (always available):

- BBC News
- CNN
- Reuters
- NPR
- Sky News

✅ **Core Features**:

- Topic classification
- Geographic detection
- Trend calculation
- Predictions
- All API endpoints

❌ **Requires API Keys**:

- Country-specific filtering (NewsAPI)
- Categorized news feeds (NewsAPI)
- Guardian-specific content (Guardian API)

---

## 🚀 Production Deployment

When you're ready to deploy:

1. **Use production database**: Neon, Railway, or other PostgreSQL service
2. **Set environment variables** on your hosting platform
3. **Use production ASGI server**:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```
4. **Set up monitoring** and log aggregation
5. **Configure reverse proxy** (nginx) if needed

---

## 📞 Need Help?

- Check the logs: The application provides detailed logging
- API Documentation: Available at `/docs` when server is running
- Test individual components using the `run.py` commands

The backend is designed to be robust and work with minimal configuration. Start with the basics and add API keys as needed!
