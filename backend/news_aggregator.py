import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db, SessionLocal
from models import Article, NewsSource, TopicTrend
from data_sources import NewsSourceManager
from preprocessing import ArticleProcessor
from geo_detection import GeographicProcessor
from topic_classifier import TopicClassifier
from sentiment_analyzer import sentiment_analyzer
from config import settings

logger = logging.getLogger(__name__)

class NewsAggregator:
    """Main news aggregation service"""
    
    def __init__(self):
        self.source_manager = NewsSourceManager()
        self.article_processor = ArticleProcessor()
        self.geo_processor = GeographicProcessor()
        self.topic_classifier = TopicClassifier()
        self.sentiment_analyzer = sentiment_analyzer
        
    def initialize_sources(self):
        """Initialize default news sources in database"""
        db = SessionLocal()
        try:
            # Check if sources already exist
            existing_sources = db.query(NewsSource).count()
            if existing_sources > 0:
                logger.info(f"Found {existing_sources} existing news sources")
                return
            
            # Default sources configuration
            default_sources = [
                {
                    'name': 'BBC News',
                    'url': 'http://feeds.bbci.co.uk/news/rss.xml',
                    'credibility_score': 0.9,
                    'country': 'UK',
                    'language': 'en'
                },
                {
                    'name': 'CNN',
                    'url': 'https://rss.cnn.com/rss/edition.rss',
                    'credibility_score': 0.8,
                    'country': 'US',
                    'language': 'en'
                },
                {
                    'name': 'Reuters',
                    'url': 'https://feeds.reuters.com/reuters/topNews',
                    'credibility_score': 0.95,
                    'country': 'US',
                    'language': 'en'
                },
                {
                    'name': 'The Guardian',
                    'url': 'https://theguardian.com',
                    'credibility_score': 0.85,
                    'country': 'UK',
                    'language': 'en'
                },
                {
                    'name': 'NPR',
                    'url': 'https://feeds.npr.org/1001/rss.xml',
                    'credibility_score': 0.9,
                    'country': 'US',
                    'language': 'en'
                }
            ]
            
            for source_data in default_sources:
                source = NewsSource(**source_data)
                db.add(source)
            
            db.commit()
            logger.info(f"Initialized {len(default_sources)} default news sources")
            
        except Exception as e:
            logger.error(f"Error initializing sources: {e}")
            db.rollback()
        finally:
            db.close()
    
    def fetch_and_process_news(self, country: str = None) -> int:
        """Fetch news from all sources and process them"""
        logger.info("Starting news fetch and processing")
        
        try:
            # Fetch raw articles from all sources
            raw_articles = self.source_manager.fetch_all_news(country=country)
            
            if not raw_articles:
                logger.warning("No articles fetched from sources")
                return 0
            
            # Process articles
            processed_articles = self.article_processor.batch_process_articles(raw_articles)
            
            if not processed_articles:
                logger.warning("No articles survived processing")
                return 0
            
            # Save to database
            saved_count = self._save_articles_to_db(processed_articles)
            
            logger.info(f"Successfully processed and saved {saved_count} articles")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error in fetch_and_process_news: {e}")
            return 0
    
    def _save_articles_to_db(self, processed_articles: List[Dict[str, Any]]) -> int:
        """Save processed articles to database"""
        db = SessionLocal()
        saved_count = 0
        
        try:
            for article_data in processed_articles:
                try:
                    # Find or create source
                    source = self._get_or_create_source(db, article_data)
                    
                    # Check if article already exists
                    existing = db.query(Article).filter(Article.url == article_data['url']).first()
                    if existing:
                        continue
                    
                    # Create new article
                    article = Article(
                        title=article_data['title'],
                        content=article_data['content'],
                        summary=article_data['summary'],
                        url=article_data['url'],
                        source_id=source.id,
                        published_date=article_data['published_date'],
                        language=article_data['language'],
                        keywords=article_data['keywords'],
                        word_count=article_data['word_count']
                    )
                    
                    # Process geographic information
                    self._process_article_geography(article, article_data)
                    
                    # Process topic classification
                    self._process_article_topics(article, article_data)
                    
                    # Process sentiment analysis
                    self._process_article_sentiment(article, article_data)
                    
                    db.add(article)
                    saved_count += 1
                    
                    # Commit every 10 articles to avoid large transactions
                    if saved_count % 10 == 0:
                        db.commit()
                        
                except IntegrityError:
                    db.rollback()
                    continue
                except Exception as e:
                    logger.error(f"Error saving article: {e}")
                    db.rollback()
                    continue
            
            # Final commit
            db.commit()
            
        except Exception as e:
            logger.error(f"Error in _save_articles_to_db: {e}")
            db.rollback()
        finally:
            db.close()
        
        return saved_count
    
    def _get_or_create_source(self, db: Session, article_data: Dict[str, Any]) -> NewsSource:
        """Get existing source or create new one"""
        source_name = article_data.get('source_name', 'Unknown')
        source_url = article_data.get('source_url', '')
        
        # Try to find existing source
        source = db.query(NewsSource).filter(NewsSource.name == source_name).first()
        
        if not source:
            # Create new source
            source = NewsSource(
                name=source_name,
                url=source_url,
                credibility_score=0.7,  # Default score
                language=article_data.get('language', 'en')
            )
            db.add(source)
            db.flush()  # Get ID without committing
        
        return source
    
    def _process_article_geography(self, article: Article, article_data: Dict[str, Any]):
        """Process geographic information for article"""
        try:
            text = f"{article_data['title']} {article_data['content']}"
            geo_result = self.geo_processor.extract_locations(text)
            
            if geo_result:
                article.locations = geo_result.get('locations', [])
                article.country = geo_result.get('primary_country')
                article.confidence_score = geo_result.get('confidence', 0.0)
            
        except Exception as e:
            logger.error(f"Error processing geography: {e}")
    
    def _process_article_topics(self, article: Article, article_data: Dict[str, Any]):
        """Process topic classification for article"""
        try:
            text = f"{article_data['title']} {article_data['content']}"
            topic_result = self.topic_classifier.classify_text(text)
            
            if topic_result:
                article.primary_theme = topic_result.get('primary_topic')
                article.secondary_themes = topic_result.get('secondary_topics', [])
                article.theme_confidence = topic_result.get('confidence', 0.0)
            
        except Exception as e:
            logger.error(f"Error processing topics: {e}")
    
    def _process_article_sentiment(self, article: Article, article_data: Dict[str, Any]):
        """Process sentiment analysis for article"""
        try:
            # Use the analyze_article method for better title+content analysis
            sentiment_result = self.sentiment_analyzer.analyze_article(
                article_data.get('title', ''), 
                article_data.get('content', '')
            )
            
            if sentiment_result:
                article.sentiment_score = sentiment_result.get('sentiment_score', 0.0)
                # Store additional sentiment metadata in keywords field if needed
                if 'details' in sentiment_result:
                    sentiment_meta = {
                        'sentiment_method': sentiment_result.get('method', 'unknown'),
                        'sentiment_confidence': sentiment_result.get('confidence', 0.0),
                        'sentiment_label': sentiment_result.get('sentiment_label', 'neutral')
                    }
                    
                    # Add to existing keywords if they exist
                    if article_data.get('keywords'):
                        article_data['keywords'].update(sentiment_meta)
                    else:
                        article_data['keywords'] = sentiment_meta
            
        except Exception as e:
            logger.error(f"Error processing sentiment: {e}")
            # Set default neutral sentiment if processing fails
            article.sentiment_score = 0.0
    
    def get_recent_articles(self, hours: int = 24, limit: int = 100) -> List[Article]:
        """Get recent articles from database"""
        db = SessionLocal()
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            articles = (db.query(Article)
                       .filter(Article.published_date >= cutoff_time)
                       .order_by(Article.published_date.desc())
                       .limit(limit)
                       .all())
            return articles
        finally:
            db.close()
    
    def get_articles_by_topic(self, topic: str, limit: int = 50) -> List[Article]:
        """Get articles by topic"""
        db = SessionLocal()
        try:
            articles = (db.query(Article)
                       .filter(Article.primary_theme == topic)
                       .order_by(Article.published_date.desc())
                       .limit(limit)
                       .all())
            return articles
        finally:
            db.close()
    
    def get_articles_by_country(self, country: str, limit: int = 50) -> List[Article]:
        """Get articles by country"""
        db = SessionLocal()
        try:
            articles = (db.query(Article)
                       .filter(Article.country == country)
                       .order_by(Article.published_date.desc())
                       .limit(limit)
                       .all())
            return articles
        finally:
            db.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregation statistics"""
        db = SessionLocal()
        try:
            total_articles = db.query(Article).count()
            total_sources = db.query(NewsSource).count()
            
            # Articles by topic
            topic_counts = {}
            for topic in settings.NEWS_TOPICS:
                count = db.query(Article).filter(Article.primary_theme == topic).count()
                topic_counts[topic] = count
            
            # Recent articles (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_count = db.query(Article).filter(Article.published_date >= cutoff_time).count()
            
            return {
                'total_articles': total_articles,
                'total_sources': total_sources,
                'recent_articles_24h': recent_count,
                'articles_by_topic': topic_counts,
                'last_updated': datetime.now().isoformat()
            }
        finally:
            db.close()

# Global instance
news_aggregator = NewsAggregator() 