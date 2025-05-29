# Comprehensive Sentiment Analysis Implementation

## Overview

This project implements a sophisticated sentiment analysis system using **TensorFlow** and transformer models for analyzing news article sentiment and integrating it with trend analysis. The system combines neural networks with rule-based approaches for robust sentiment detection.

## Architecture

### Core Components

1. **SentimentAnalyzer (`backend/sentiment_analyzer.py`)**

   - TensorFlow-based neural sentiment analysis
   - Rule-based fallback system
   - Hybrid blended approach
   - Article-level sentiment analysis

2. **TrendAnalyzer (`backend/trend_analyzer.py`)**

   - TensorFlow LSTM model for trend prediction
   - Sentiment-integrated trend analysis
   - Multi-dimensional trend metrics

3. **API Layer (`backend/api/sentiment_api.py`)**
   - RESTful endpoints for sentiment analysis
   - Real-time sentiment processing
   - Batch analysis capabilities

## TensorFlow Implementation Details

### Neural Sentiment Model Architecture

```python
# Model Structure
tf.keras.Sequential([
    # Base transformer model (DistilBERT)
    TFAutoModel.from_pretrained("distilbert-base-uncased"),

    # Multi-strategy pooling
    - CLS token extraction
    - Global average pooling
    - Global max pooling
    - Concatenation layer

    # Classification head
    Dense(512, activation='relu'),
    Dropout(0.3),
    BatchNormalization(),
    Dense(256, activation='relu'),
    Dropout(0.2),
    BatchNormalization(),
    Dense(128, activation='relu'),
    Dropout(0.1),

    # Dual outputs
    Dense(1, activation='tanh', name='sentiment_score'),  # -1 to +1
    Dense(1, activation='sigmoid', name='confidence')     # 0 to 1
])
```

### Features

- **Input Processing**: 512 token maximum sequence length
- **Multi-Output**: Sentiment score (-1 to +1) and confidence (0 to 1)
- **Pooling Strategies**: Combines CLS token, mean, and max pooling
- **Regularization**: Dropout and batch normalization for stability

### Trend Prediction Model

```python
# LSTM Architecture for Trend Prediction
tf.keras.Sequential([
    LSTM(64, return_sequences=True, input_shape=(7, 6)),  # 7 days, 6 features
    Dropout(0.2),
    LSTM(32, return_sequences=False),
    Dropout(0.2),
    Dense(16, activation='relu'),
    Dense(1, activation='linear')  # Trend direction prediction
])
```

**Input Features (per day)**:

1. Article count
2. Average word count (normalized)
3. Average sentiment score
4. Sentiment variance
5. Source diversity
6. Geographic spread

## Multi-Method Approach

### 1. Neural Analysis (`analyze_with_model`)

- Uses fine-tuned transformer model
- Confidence-based output
- Fallback to rule-based if confidence < threshold

### 2. Rule-Based Analysis (`analyze_with_rules`)

- Keyword matching with sentiment lexicon
- Negation handling
- Context-aware scoring
- Normalized by text length

### 3. Blended Analysis (`analyze_text`)

- Automatically selects best method
- Weighted combination when both methods available
- Confidence-driven decision making

## Sentiment Keywords Database

### Positive Keywords (33 total)

```
'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'outstanding',
'success', 'achievement', 'victory', 'win', 'progress', 'improvement', 'growth',
'beneficial', 'advantage', 'positive', 'optimistic', 'hopeful', 'promising',
'breakthrough', 'innovation', 'solution', 'opportunity', 'boost', 'rise',
'celebrate', 'joy', 'happy', 'pleased', 'satisfied', 'thrilled', 'excited'
```

### Negative Keywords (32 total)

```
'bad', 'terrible', 'awful', 'horrible', 'disaster', 'crisis', 'problem',
'failure', 'defeat', 'loss', 'decline', 'worsen', 'deteriorate', 'collapse',
'harmful', 'dangerous', 'threat', 'risk', 'concern', 'worry', 'fear',
'violence', 'war', 'conflict', 'attack', 'damage', 'destruction', 'death',
'sad', 'angry', 'frustrated', 'disappointed', 'concerned', 'alarmed'
```

## API Endpoints

### Core Sentiment Analysis

```bash
# Analyze single text
POST /api/sentiment/analyze
{
  "text": "This is a wonderful breakthrough in technology!",
  "method": "auto"  # "neural", "rules", or "auto"
}

# Analyze article (title + content)
POST /api/sentiment/analyze-article
{
  "title": "Major Scientific Discovery",
  "content": "Scientists have made an amazing breakthrough..."
}

# Batch analysis
POST /api/sentiment/batch-analyze
{
  "texts": ["Text 1", "Text 2", "Text 3"]
}
```

### Trend & Distribution Analysis

```bash
# Get sentiment distribution across topics
GET /api/sentiment/distribution?days=7

# Get sentiment trends with TensorFlow predictions
GET /api/sentiment/trends?days=30&min_articles=5

# Get topic-specific sentiment analysis
GET /api/sentiment/topic/Technology%20%26%20Innovation?days=7

# Get trending topics (volume + sentiment weighted)
GET /api/sentiment/trending?hours=24&min_articles=3
```

### Model Information

```bash
# Get model configuration and status
GET /api/sentiment/model-info
```

## Integration with News Processing

### Article Processing Pipeline

1. **Raw Article Input** → Article fetched from news sources
2. **Content Processing** → Text cleaning and preprocessing
3. **Sentiment Analysis** → Multi-method sentiment scoring
4. **Database Storage** → Sentiment score and metadata stored
5. **Trend Analysis** → TensorFlow-powered trend prediction

### Database Integration

```python
# Article model includes sentiment fields
class Article:
    sentiment_score: float  # -1.0 to 1.0
    keywords: dict         # Includes sentiment metadata
```

### Metadata Storage

Sentiment analysis results include:

- `sentiment_score`: Numerical score (-1 to 1)
- `sentiment_label`: 'positive', 'negative', or 'neutral'
- `confidence`: Model confidence (0 to 1)
- `method`: 'neural', 'rule-based', or 'blended'
- `details`: Additional analysis metadata

## Running Sentiment Analysis

### 1. Process Existing Articles

```bash
cd backend
python process_sentiment.py --batch-size 50

# Analyze distribution
python process_sentiment.py --analyze

# Update existing scores
python process_sentiment.py --update
```

### 2. Test the System

```bash
cd backend
python test_sentiment.py
```

### 3. Start API Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

## Performance Optimization

### Model Loading Strategy

- **Lazy Loading**: Model loads on first use
- **Caching**: Models cached after first load
- **Fallback**: Rule-based analysis if neural model fails

### Batch Processing

- **Vectorized Operations**: NumPy for efficient computation
- **Database Batching**: Commits every 10 articles
- **Memory Management**: Processes in configurable batches

### TensorFlow Optimizations

- **GPU Support**: Automatically uses GPU if available
- **Model Quantization**: Reduced precision for faster inference
- **Batch Inference**: Processes multiple texts simultaneously

## Trend Analysis Integration

### Sentiment-Enhanced Trends

The trend analyzer incorporates sentiment in multiple ways:

1. **Volume Weighting**: Positive sentiment boosts trend scores
2. **Volatility Metrics**: Sentiment variance indicates topic stability
3. **Prediction Features**: Sentiment included in TensorFlow LSTM inputs
4. **Trending Topics**: Sentiment influences trending topic rankings

### Trend Metrics

```python
# Daily metrics include sentiment data
{
    'article_count': int,
    'avg_sentiment': float,
    'sentiment_variance': float,
    'trend_direction': str,  # 'increasing', 'decreasing', 'stable'
    'predicted_change': float  # TensorFlow LSTM prediction
}
```

## Configuration

### Environment Variables

```bash
# Model Configuration
HUGGINGFACE_CACHE_DIR=./models_cache
MODEL_NAME=distilbert-base-uncased

# Database
DATABASE_URL=postgresql://localhost:5432/trendpulse

# API Keys (for data sources)
NEWS_API_KEY=your_news_api_key
GUARDIAN_API_KEY=your_guardian_api_key
```

### Model Files

The system automatically downloads and caches:

- **DistilBERT tokenizer**: For text preprocessing
- **DistilBERT model**: Base transformer for sentiment analysis
- **Custom sentiment head**: Fine-tuned classification layers

## Error Handling & Fallbacks

### Graceful Degradation

1. Neural model fails → Rule-based analysis
2. Rule-based fails → Neutral sentiment (0.0)
3. Text too short → Skip or neutral
4. Invalid input → HTTP 400 with clear message

### Logging & Monitoring

- Comprehensive error logging
- Performance metrics tracking
- Model confidence monitoring
- API usage statistics

## Future Enhancements

### Model Improvements

- **Fine-tuning**: Train on news-specific datasets
- **Multi-language**: Support for non-English news
- **Domain Adaptation**: Specialized models for different news categories

### Advanced Features

- **Emotion Detection**: Beyond positive/negative/neutral
- **Aspect-based Sentiment**: Entity-specific sentiment
- **Real-time Learning**: Continuous model updates
- **Explainable AI**: Sentiment reasoning explanations

## Dependencies

### Core Libraries

```python
tensorflow>=2.14.0
transformers>=4.33.0
torch>=2.0.0  # For transformers
huggingface-hub>=0.16.0
scikit-learn>=1.3.0
numpy>=1.24.0
pandas>=2.0.0
```

### API & Database

```python
fastapi>=0.104.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
```

This implementation provides a production-ready, scalable sentiment analysis system that seamlessly integrates with your news aggregation and trend analysis pipeline, leveraging the power of TensorFlow and modern NLP techniques.
