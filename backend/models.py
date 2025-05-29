from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid
from datetime import datetime

class NewsSource(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    credibility_score = Column(Float, default=0.8)
    country = Column(String(100))
    language = Column(String(10), default="en")
    last_updated = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationship
    articles = relationship("Article", back_populates="source")

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text)
    url = Column(String(500), unique=True, nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"))
    published_date = Column(DateTime, nullable=False)
    scraped_date = Column(DateTime, default=func.now())
    
    # Geographic information
    country = Column(String(100))
    locations = Column(JSON)  # List of detected locations
    confidence_score = Column(Float, default=0.0)
    
    # Topic classification
    primary_theme = Column(String(100))
    secondary_themes = Column(JSON)  # List of secondary themes
    theme_confidence = Column(Float, default=0.0)
    
    # Content analysis
    sentiment_score = Column(Float)  # -1 to 1
    keywords = Column(JSON)  # List of extracted keywords
    
    # Metadata
    language = Column(String(10), default="en")
    word_count = Column(Integer)
    
    # Relationships
    source = relationship("NewsSource", back_populates="articles")

class TopicTrend(Base):
    __tablename__ = "topic_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    theme = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    date = Column(DateTime, nullable=False)
    
    # Trend metrics
    article_count = Column(Integer, default=0)
    trend_score = Column(Float, default=0.0)
    prediction_confidence = Column(Float, default=0.0)
    
    # Additional metrics
    sentiment_avg = Column(Float)
    engagement_score = Column(Float)
    
    created_at = Column(DateTime, default=func.now())

class TopicPrediction(Base):
    __tablename__ = "topic_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    theme = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    prediction_date = Column(DateTime, nullable=False)
    predicted_trend_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(50))
    
    created_at = Column(DateTime, default=func.now()) 