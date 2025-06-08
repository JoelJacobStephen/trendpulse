import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost:5432/trendpulse")
    
    # API Keys
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    GUARDIAN_API_KEY: str = os.getenv("GUARDIAN_API_KEY", "")
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
    
    # ML Models
    HUGGINGFACE_CACHE_DIR: str = os.getenv("HUGGINGFACE_CACHE_DIR", "./models_cache")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "distilbert-base-uncased")
    
    # Background Tasks
    NEWS_FETCH_INTERVAL: int = int(os.getenv("NEWS_FETCH_INTERVAL", "3600"))
    TREND_CALCULATION_INTERVAL: int = int(os.getenv("TREND_CALCULATION_INTERVAL", "86400"))
    
    # Data Retention
    ARTICLE_RETENTION_DAYS: int = int(os.getenv("ARTICLE_RETENTION_DAYS", "30"))
    TREND_RETENTION_DAYS: int = int(os.getenv("TREND_RETENTION_DAYS", "90"))
    
    # News Sources
    RSS_FEEDS = [
        "http://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.cnn.com/rss/edition.rss",
        "https://feeds.reuters.com/reuters/topNews",
        "https://feeds.npr.org/1001/rss.xml",
        "https://feeds.skynews.com/feeds/rss/world.xml"
    ]
    
    # Topic Categories (adapted from poetry themes)
    NEWS_TOPICS = [
        "Politics & Elections",
        "Technology & Innovation", 
        "Climate & Environment",
        "Health & Medicine",
        "Business & Economy",
        "Sports & Entertainment",
        "War & International",
        "Society & Culture",
        "Science & Research",
        "Crime & Justice"
    ]

settings = Settings() 