import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from database import SessionLocal
from models import Article, NewsSource
from news_aggregator import news_aggregator
from data_sources import NewsSourceManager
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class NewsProcessor:
    """ETL pipeline for news data processing"""
    
    def __init__(self):
        self.source_manager = NewsSourceManager()
    
    def fetch_and_process_all(self) -> int:
        """Fetch and process news from all sources"""
        try:
            logger.info("Starting comprehensive news fetch and processing...")
            
            # Use the existing news aggregator
            total_processed = news_aggregator.fetch_and_process_news()
            
            logger.info(f"News processing completed: {total_processed} articles processed")
            return total_processed
            
        except Exception as e:
            logger.error(f"Error in fetch_and_process_all: {e}")
            return 0
    
    def fetch_country_specific_news(self, country_code: str) -> int:
        """Fetch news for a specific country"""
        try:
            logger.info(f"Fetching news for country: {country_code}")
            
            # Fetch country-specific news
            raw_articles = self.source_manager.get_country_specific_news(country_code)
            
            if not raw_articles:
                logger.warning(f"No articles found for country: {country_code}")
                return 0
            
            # Process through the aggregator
            processed_count = news_aggregator._save_articles_to_db(raw_articles)
            
            logger.info(f"Country-specific processing completed: {processed_count} articles for {country_code}")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error fetching country-specific news: {e}")
            return 0
    
    def cleanup_old_articles(self, days: int = 30) -> int:
        """Clean up articles older than specified days"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Count articles to be deleted
            old_articles_count = (db.query(Article)
                                .filter(Article.published_date < cutoff_date)
                                .count())
            
            if old_articles_count == 0:
                logger.info("No old articles to clean up")
                return 0
            
            # Delete old articles
            deleted_count = (db.query(Article)
                           .filter(Article.published_date < cutoff_date)
                           .delete(synchronize_session=False))
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} articles older than {days} days")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old articles: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    def reprocess_articles_without_topics(self) -> int:
        """Reprocess articles that don't have topic classification"""
        db = SessionLocal()
        try:
            # Find articles without primary theme
            articles_without_topics = (db.query(Article)
                                     .filter(Article.primary_theme.is_(None))
                                     .limit(100)  # Process in batches
                                     .all())
            
            if not articles_without_topics:
                logger.info("No articles without topics found")
                return 0
            
            processed_count = 0
            
            for article in articles_without_topics:
                try:
                    # Reprocess topic classification
                    text = f"{article.title} {article.content or ''}"
                    news_aggregator._process_article_topics(article, {"title": article.title, "content": article.content})
                    
                    processed_count += 1
                    
                    # Commit every 10 articles
                    if processed_count % 10 == 0:
                        db.commit()
                        
                except Exception as e:
                    logger.error(f"Error reprocessing article {article.id}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Reprocessed {processed_count} articles for topic classification")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error reprocessing articles: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    def reprocess_articles_without_geography(self) -> int:
        """Reprocess articles that don't have geographic information"""
        db = SessionLocal()
        try:
            # Find articles without country information
            articles_without_geo = (db.query(Article)
                                  .filter(Article.country.is_(None))
                                  .limit(100)  # Process in batches
                                  .all())
            
            if not articles_without_geo:
                logger.info("No articles without geography found")
                return 0
            
            processed_count = 0
            
            for article in articles_without_geo:
                try:
                    # Reprocess geographic information
                    text = f"{article.title} {article.content or ''}"
                    news_aggregator._process_article_geography(article, {"title": article.title, "content": article.content})
                    
                    processed_count += 1
                    
                    # Commit every 10 articles
                    if processed_count % 10 == 0:
                        db.commit()
                        
                except Exception as e:
                    logger.error(f"Error reprocessing article {article.id}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Reprocessed {processed_count} articles for geographic information")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error reprocessing geography: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    def update_source_statistics(self) -> Dict[str, Any]:
        """Update statistics for all news sources"""
        db = SessionLocal()
        try:
            source_stats = {}
            
            # Get all sources
            sources = db.query(NewsSource).all()
            
            for source in sources:
                # Count articles from this source
                article_count = db.query(Article).filter(Article.source_id == source.id).count()
                
                # Count recent articles (last 24 hours)
                recent_cutoff = datetime.now() - timedelta(hours=24)
                recent_count = (db.query(Article)
                              .filter(and_(
                                  Article.source_id == source.id,
                                  Article.scraped_date >= recent_cutoff
                              ))
                              .count())
                
                # Update source last_updated if it has recent articles
                if recent_count > 0:
                    source.last_updated = datetime.now()
                
                source_stats[source.name] = {
                    "total_articles": article_count,
                    "recent_articles_24h": recent_count,
                    "last_updated": source.last_updated.isoformat() if source.last_updated else None
                }
            
            db.commit()
            
            logger.info(f"Updated statistics for {len(sources)} news sources")
            return source_stats
            
        except Exception as e:
            logger.error(f"Error updating source statistics: {e}")
            db.rollback()
            return {}
        finally:
            db.close()
    
    def check_database_health(self) -> bool:
        """Check database connectivity and health"""
        try:
            db = SessionLocal()
            
            # Simple query to test connectivity
            result = db.execute("SELECT 1").fetchone()
            
            # Check if we can access main tables
            article_count = db.query(Article).count()
            source_count = db.query(NewsSource).count()
            
            db.close()
            
            logger.debug(f"Database health check passed: {article_count} articles, {source_count} sources")
            return True
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def check_api_health(self) -> bool:
        """Check external API availability"""
        try:
            # Test RSS feeds
            rss_status = True
            try:
                test_articles = self.source_manager.rss.get_articles_from_feed(
                    "http://feeds.bbci.co.uk/news/rss.xml"
                )
                if not test_articles:
                    rss_status = False
            except:
                rss_status = False
            
            # Test NewsAPI if configured
            newsapi_status = True
            try:
                if self.source_manager.newsapi.client:
                    test_articles = self.source_manager.newsapi.get_top_headlines(page_size=1)
                    if not test_articles:
                        newsapi_status = False
            except:
                newsapi_status = False
            
            # Overall status
            overall_status = rss_status or newsapi_status  # At least one should work
            
            logger.debug(f"API health check: RSS={rss_status}, NewsAPI={newsapi_status}")
            return overall_status
            
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return False
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        db = SessionLocal()
        try:
            stats = {}
            
            # Article statistics
            total_articles = db.query(Article).count()
            
            # Articles by source
            source_counts = (db.query(NewsSource.name, func.count(Article.id).label('count'))
                           .join(Article, NewsSource.id == Article.source_id, isouter=True)
                           .group_by(NewsSource.name)
                           .all())
            
            # Articles by date (last 7 days)
            date_counts = []
            for i in range(7):
                date = datetime.now().date() - timedelta(days=i)
                count = (db.query(Article)
                        .filter(func.date(Article.published_date) == date)
                        .count())
                date_counts.append({"date": date.isoformat(), "count": count})
            
            # Articles with/without classification
            articles_with_topics = db.query(Article).filter(Article.primary_theme.isnot(None)).count()
            articles_with_geography = db.query(Article).filter(Article.country.isnot(None)).count()
            
            stats = {
                "total_articles": total_articles,
                "articles_with_topics": articles_with_topics,
                "articles_with_geography": articles_with_geography,
                "classification_rate": (articles_with_topics / total_articles * 100) if total_articles > 0 else 0,
                "geography_rate": (articles_with_geography / total_articles * 100) if total_articles > 0 else 0,
                "source_distribution": [{"source": name, "count": count} for name, count in source_counts],
                "daily_counts": date_counts
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting processing statistics: {e}")
            return {}
        finally:
            db.close() 