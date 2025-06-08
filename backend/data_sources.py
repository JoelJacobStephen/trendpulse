import os
from typing import List, Dict, Any, Optional
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

    def get_historical_articles(self, 
                              from_date: datetime, 
                              to_date: datetime, 
                              query: str = None,
                              sources: str = None,
                              page_size: int = 100,
                              page: int = 1) -> List[Dict]:
        """Fetch historical articles from NewsAPI using /everything endpoint"""
        if not self.client:
            logger.warning("NewsAPI key not configured")
            return []
            
        try:
            # Format dates for NewsAPI (ISO 8601)
            from_param = from_date.strftime('%Y-%m-%dT%H:%M:%S')
            to_param = to_date.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Use get_everything for historical data
            response = self.client.get_everything(
                q=query,
                sources=sources,
                from_param=from_param,
                to=to_param,
                language='en',
                sort_by='publishedAt',
                page_size=page_size,
                page=page
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
            
            logger.info(f"Fetched {len(articles)} historical articles from NewsAPI ({from_param} to {to_param})")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching historical articles from NewsAPI: {e}")
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

    def get_historical_articles(self, 
                              from_date: datetime, 
                              to_date: datetime,
                              section: str = None,
                              query: str = None,
                              page_size: int = 50,
                              page: int = 1) -> List[Dict]:
        """Fetch historical articles from Guardian API with date range"""
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
                'order-by': 'newest',
                'from-date': from_date.strftime('%Y-%m-%d'),
                'to-date': to_date.strftime('%Y-%m-%d'),
                'page': page
            }
            
            if section:
                params['section'] = section
            if query:
                params['q'] = query
                
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
            
            logger.info(f"Fetched {len(articles)} historical articles from Guardian ({from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')})")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching historical articles from Guardian: {e}")
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

    def fetch_historical_news(self, 
                            from_date: datetime, 
                            to_date: datetime,
                            query: str = None,
                            sources: str = None) -> List[Dict]:
        """Fetch historical news from all available sources with API keys"""
        all_articles = []
        
        # Fetch historical data from NewsAPI (requires API key)
        if self.newsapi.client:
            try:
                # Fetch in chunks to handle large date ranges
                current_date = from_date
                while current_date < to_date:
                    chunk_end = min(current_date + timedelta(days=7), to_date)
                    
                    newsapi_articles = self.newsapi.get_historical_articles(
                        from_date=current_date,
                        to_date=chunk_end,
                        query=query,
                        sources=sources,
                        page_size=100
                    )
                    
                    for article in newsapi_articles:
                        article['source_type'] = 'newsapi_historical'
                    all_articles.extend(newsapi_articles)
                    
                    current_date = chunk_end + timedelta(days=1)
                    
                logger.info(f"Fetched {len([a for a in all_articles if a['source_type'] == 'newsapi_historical'])} historical articles from NewsAPI")
            except Exception as e:
                logger.error(f"Error fetching historical NewsAPI data: {e}")
        
        # Fetch historical data from Guardian (requires API key)
        if self.guardian.api_key:
            try:
                guardian_articles = self.guardian.get_historical_articles(
                    from_date=from_date,
                    to_date=to_date,
                    query=query,
                    page_size=50
                )
                
                for article in guardian_articles:
                    article['source_type'] = 'guardian_historical'
                all_articles.extend(guardian_articles)
                
                logger.info(f"Fetched {len([a for a in all_articles if a['source_type'] == 'guardian_historical'])} historical articles from Guardian")
            except Exception as e:
                logger.error(f"Error fetching historical Guardian data: {e}")
        
        # RSS feeds cannot provide historical data beyond what's in current feeds
        logger.info(f"Total historical articles fetched: {len(all_articles)}")
        return all_articles
    
    def get_country_specific_news(self, country_code: str) -> List[Dict]:
        """Get news specific to a country"""
        return self.newsapi.get_top_headlines(country=country_code)
    
    def get_category_news(self, category: str) -> List[Dict]:
        """Get news by category"""
        return self.newsapi.get_top_headlines(category=category)

    def bulk_fetch_historical_data(self, days_back: int = 30, batch_size: int = 7) -> int:
        """Bulk fetch historical data for the past N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Starting bulk historical fetch for {days_back} days ({start_date} to {end_date})")
        
        total_articles = 0
        current_date = start_date
        
        while current_date < end_date:
            batch_end = min(current_date + timedelta(days=batch_size), end_date)
            
            logger.info(f"Fetching batch: {current_date} to {batch_end}")
            articles = self.fetch_historical_news(
                from_date=current_date,
                to_date=batch_end
            )
            
            if articles:
                # Process and save articles (you would integrate this with news_aggregator)
                total_articles += len(articles)
                logger.info(f"Batch completed: {len(articles)} articles")
            
            current_date = batch_end
        
        logger.info(f"Bulk historical fetch completed: {total_articles} total articles")
        return total_articles 