from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class NewsTopicEnum(str, Enum):
    POLITICS = "Politics & Elections"
    TECHNOLOGY = "Technology & Innovation"
    CLIMATE = "Climate & Environment"
    HEALTH = "Health & Medicine"
    BUSINESS = "Business & Economy"
    SPORTS = "Sports & Entertainment"
    WAR = "War & International"
    SOCIETY = "Society & Culture"
    SCIENCE = "Science & Research"
    CRIME = "Crime & Justice"

# News Source Schemas
class NewsSourceBase(BaseModel):
    name: str
    url: HttpUrl
    credibility_score: float = 0.8
    country: Optional[str] = None
    language: str = "en"
    is_active: bool = True

class NewsSourceCreate(NewsSourceBase):
    pass

class NewsSourceResponse(NewsSourceBase):
    id: int
    last_updated: datetime
    article_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

# Article Schemas
class ArticleBase(BaseModel):
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    url: HttpUrl
    published_date: datetime
    country: Optional[str] = None
    primary_theme: Optional[str] = None
    language: str = "en"

class ArticleCreate(ArticleBase):
    source_id: int

class ArticleResponse(ArticleBase):
    id: int
    source_id: int
    source_name: Optional[str] = None
    scraped_date: datetime
    locations: Optional[List[str]] = []
    confidence_score: float = 0.0
    secondary_themes: Optional[List[str]] = []
    theme_confidence: float = 0.0
    sentiment_score: Optional[float] = None
    keywords: Optional[List[str]] = []
    word_count: Optional[int] = None
    
    class Config:
        from_attributes = True

# Topic Trend Schemas
class TopicTrendBase(BaseModel):
    theme: str
    country: str
    date: datetime
    article_count: int = 0
    trend_score: float = 0.0

class TopicTrendCreate(TopicTrendBase):
    prediction_confidence: float = 0.0
    sentiment_avg: Optional[float] = None
    engagement_score: Optional[float] = None

class TopicTrendResponse(TopicTrendBase):
    id: int
    prediction_confidence: float
    sentiment_avg: Optional[float]
    engagement_score: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

# API Response Schemas
class TopicListResponse(BaseModel):
    topics: List[str]
    total_count: int

class CountryTopicsResponse(BaseModel):
    country: str
    topics: List[TopicTrendResponse]
    date_range: Dict[str, datetime]

class LiveTrendsResponse(BaseModel):
    trending_topics: List[Dict[str, Any]]
    last_updated: datetime
    update_interval: int

class PredictionResponse(BaseModel):
    theme: str
    country: str
    current_trend: float
    predicted_trend: float
    confidence: float
    prediction_date: datetime

# Request Schemas
class TrendQuery(BaseModel):
    topic: Optional[str] = None
    country: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)

class NewsSearchQuery(BaseModel):
    query: Optional[str] = None
    topics: Optional[List[str]] = []
    countries: Optional[List[str]] = []
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=20, le=100)
    offset: int = Field(default=0, ge=0) 