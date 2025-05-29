import os
from typing import List, Dict, Any
import requests
import feedparser
from newsapi import NewsApiClient
from config import settings
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NewsAPISource:
    """NewsAPI.org integration"""
    
    def __init__(self):
        self.client = NewsApiClient(api_key=settings.NEWS_API_KEY) if settings.NEWS_API_KEY else None
        
    def get_top_headlines(self, country: str = None, category: str = None, page_size: int = 100) -> List[Dict]:
        """Fetch top headlines from NewsAPI"""
        if not self.client:
            logger.warning("NewsAPI key not configured")
            return []
            
        try:
            response = self.client.get_top_headlines(
                country=country,
                category=category,
                page_size=page_size,
                language='en'
            )
            
            articles = []
            for article in response.get('articles', []):
                articles.append({
                    'title': article.get('title', ''),
                    'content': article.get('content', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'published_date': article.get('publishedAt', ''),
                    'source_name': article.get('source', {}).get('name', ''),
                    'source_url': article.get('url', ''),
                    'author': article.get('author', ''),
                    'image_url': article.get('urlToImage', '')
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
            return []

class GuardianAPISource:
    """The Guardian API integration"""
    
    def __init__(self):
        self.api_key = settings.GUARDIAN_API_KEY
        self.base_url = "https://content.guardianapis.com"
        
    def get_articles(self, section: str = None, page_size: int = 50) -> List[Dict]:
        """Fetch articles from Guardian API"""
        if not self.api_key:
            logger.warning("Guardian API key not configured")
            return []
            
        try:
            url = f"{self.base_url}/search"
            params = {
                'api-key': self.api_key,
                'page-size': page_size,
                'show-fields': 'all',
                'show-tags': 'keyword',
                'order-by': 'newest'
            }
            
            if section:
                params['section'] = section
                
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for item in data.get('response', {}).get('results', []):
                fields = item.get('fields', {})
                articles.append({
                    'title': item.get('webTitle', ''),
                    'content': fields.get('bodyText', ''),
                    'description': fields.get('trailText', ''),
                    'url': item.get('webUrl', ''),
                    'published_date': item.get('webPublicationDate', ''),
                    'source_name': 'The Guardian',
                    'source_url': 'https://theguardian.com',
                    'section': item.get('sectionName', ''),
                    'tags': [tag.get('webTitle', '') for tag in item.get('tags', [])]
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching from Guardian API: {e}")
            return []

class RSSFeedSource:
    """RSS feed integration for various news sources"""
    
    def __init__(self):
        self.feeds = settings.RSS_FEEDS
        
    def get_articles_from_feed(self, feed_url: str) -> List[Dict]:
        """Fetch articles from a single RSS feed"""
        try:
            feed = feedparser.parse(feed_url)
            articles = []
            
            for entry in feed.entries:
                articles.append({
                    'title': entry.get('title', ''),
                    'content': entry.get('description', ''),
                    'description': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'published_date': entry.get('published', ''),
                    'source_name': feed.feed.get('title', ''),
                    'source_url': feed_url,
                    'author': entry.get('author', ''),
                    'tags': [tag.term for tag in entry.get('tags', [])]
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
            return []
    
    def get_all_articles(self) -> List[Dict]:
        """Fetch articles from all configured RSS feeds"""
        all_articles = []
        
        for feed_url in self.feeds:
            articles = self.get_articles_from_feed(feed_url)
            all_articles.extend(articles)
            
        return all_articles

class NewsSourceManager:
    """Main class to manage all news sources"""
    
    def __init__(self):
        self.newsapi = NewsAPISource()
        self.guardian = GuardianAPISource()
        self.rss = RSSFeedSource()
        
    def fetch_all_news(self, country: str = None) -> List[Dict]:
        """Fetch news from all available sources"""
        all_articles = []
        
        # Fetch from NewsAPI
        newsapi_articles = self.newsapi.get_top_headlines(country=country)
        for article in newsapi_articles:
            article['source_type'] = 'newsapi'
        all_articles.extend(newsapi_articles)
        
        # Fetch from Guardian
        guardian_articles = self.guardian.get_articles()
        for article in guardian_articles:
            article['source_type'] = 'guardian'
        all_articles.extend(guardian_articles)
        
        # Fetch from RSS feeds
        rss_articles = self.rss.get_all_articles()
        for article in rss_articles:
            article['source_type'] = 'rss'
        all_articles.extend(rss_articles)
        
        logger.info(f"Fetched {len(all_articles)} articles from all sources")
        return all_articles
    
    def get_country_specific_news(self, country_code: str) -> List[Dict]:
        """Get news specific to a country"""
        return self.newsapi.get_top_headlines(country=country_code)
    
    def get_category_news(self, category: str) -> List[Dict]:
        """Get news by category"""
        return self.newsapi.get_top_headlines(category=category) 