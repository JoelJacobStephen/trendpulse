import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from collections import defaultdict, Counter
import numpy as np
from scipy import stats

from database import SessionLocal
from models import Article, TopicTrend, TopicPrediction
from config import settings
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class TrendCalculator:
    """Calculate and analyze topic trends over time and geography"""
    
    def __init__(self):
        self.smoothing_window = 7  # Days for trend smoothing
        self.prediction_days = 7   # Days to predict ahead
    
    def calculate_all_trends(self) -> int:
        """Calculate trends for all topics and countries"""
        logger.info("Starting comprehensive trend calculation...")
        
        total_calculated = 0
        
        try:
            # Get all unique combinations of topics and countries
            db = SessionLocal()
            
            combinations = (db.query(Article.primary_theme, Article.country)
                          .filter(and_(
                              Article.primary_theme.isnot(None),
                              Article.country.isnot(None)
                          ))
                          .distinct()
                          .all())
            
            db.close()
            
            logger.info(f"Found {len(combinations)} topic-country combinations to process")
            
            for topic, country in combinations:
                try:
                    trends_count = self.calculate_topic_country_trends(topic, country)
                    total_calculated += trends_count
                except Exception as e:
                    logger.error(f"Error calculating trends for {topic} in {country}: {e}")
                    continue
            
            logger.info(f"Trend calculation completed: {total_calculated} trends calculated")
            return total_calculated
            
        except Exception as e:
            logger.error(f"Error in calculate_all_trends: {e}")
            return 0
    
    def calculate_topic_country_trends(self, topic: str, country: str, days_back: int = 30) -> int:
        """Calculate trends for a specific topic-country combination"""
        db = SessionLocal()
        try:
            logger.debug(f"Calculating trends for {topic} in {country}")
            
            # Get articles for the topic-country combination
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            articles = (db.query(Article)
                       .filter(and_(
                           Article.primary_theme == topic,
                           Article.country == country,
                           Article.published_date >= start_date,
                           Article.published_date <= end_date
                       ))
                       .order_by(Article.published_date)
                       .all())
            
            if not articles:
                logger.debug(f"No articles found for {topic} in {country}")
                return 0
            
            # Group articles by date
            daily_counts = self._group_articles_by_date(articles)
            
            # Calculate trend scores
            trend_data = self._calculate_trend_scores(daily_counts)
            
            # Calculate sentiment if available
            sentiment_data = self._calculate_sentiment_trends(articles)
            
            # Save trends to database
            saved_count = 0
            for date_str, trend_info in trend_data.items():
                try:
                    # Check if trend already exists
                    existing_trend = (db.query(TopicTrend)
                                    .filter(and_(
                                        TopicTrend.theme == topic,
                                        TopicTrend.country == country,
                                        func.date(TopicTrend.date) == datetime.strptime(date_str, '%Y-%m-%d').date()
                                    ))
                                    .first())
                    
                    if existing_trend:
                        # Update existing trend
                        existing_trend.article_count = trend_info['article_count']
                        existing_trend.trend_score = trend_info['trend_score']
                        existing_trend.sentiment_avg = sentiment_data.get(date_str)
                        existing_trend.created_at = datetime.now()
                    else:
                        # Create new trend
                        trend = TopicTrend(
                            theme=topic,
                            country=country,
                            date=datetime.strptime(date_str, '%Y-%m-%d'),
                            article_count=trend_info['article_count'],
                            trend_score=trend_info['trend_score'],
                            sentiment_avg=sentiment_data.get(date_str),
                            engagement_score=self._calculate_engagement_score(trend_info)
                        )
                        db.add(trend)
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving trend for {date_str}: {e}")
                    continue
            
            db.commit()
            logger.debug(f"Saved {saved_count} trends for {topic} in {country}")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error calculating topic-country trends: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    def _group_articles_by_date(self, articles: List[Article]) -> Dict[str, List[Article]]:
        """Group articles by publication date"""
        daily_groups = defaultdict(list)
        
        for article in articles:
            date_str = article.published_date.strftime('%Y-%m-%d')
            daily_groups[date_str].append(article)
        
        return daily_groups
    
    def _calculate_trend_scores(self, daily_counts: Dict[str, List[Article]]) -> Dict[str, Dict[str, Any]]:
        """Calculate trend scores for daily article counts"""
        trend_data = {}
        
        # Convert to time series
        dates = sorted(daily_counts.keys())
        counts = [len(daily_counts[date]) for date in dates]
        
        if len(counts) < 3:
            # Not enough data for trend calculation
            for date in dates:
                trend_data[date] = {
                    'article_count': len(daily_counts[date]),
                    'trend_score': 0.5,  # Neutral
                    'trend_direction': 'stable'
                }
            return trend_data
        
        # Apply smoothing
        smoothed_counts = self._apply_smoothing(counts)
        
        # Calculate trends
        for i, date in enumerate(dates):
            article_count = len(daily_counts[date])
            
            # Calculate trend score based on recent change
            if i >= 2:
                # Compare with previous days
                recent_avg = np.mean(smoothed_counts[max(0, i-2):i+1])
                older_avg = np.mean(smoothed_counts[max(0, i-6):max(1, i-3)])
                
                if older_avg > 0:
                    trend_score = min(max((recent_avg - older_avg) / older_avg + 0.5, 0), 1)
                else:
                    trend_score = 0.5
                
                # Determine trend direction
                if trend_score > 0.6:
                    direction = 'rising'
                elif trend_score < 0.4:
                    direction = 'falling'
                else:
                    direction = 'stable'
            else:
                trend_score = 0.5
                direction = 'stable'
            
            trend_data[date] = {
                'article_count': article_count,
                'trend_score': trend_score,
                'trend_direction': direction
            }
        
        return trend_data
    
    def _apply_smoothing(self, values: List[float], window: Optional[int] = None) -> List[float]:
        """Apply moving average smoothing"""
        if window is None:
            window = min(self.smoothing_window, len(values) // 3)
        
        if window <= 1:
            return values
        
        smoothed = []
        for i in range(len(values)):
            start_idx = max(0, i - window // 2)
            end_idx = min(len(values), i + window // 2 + 1)
            smoothed.append(np.mean(values[start_idx:end_idx]))
        
        return smoothed
    
    def _calculate_sentiment_trends(self, articles: List[Article]) -> Dict[str, float]:
        """Calculate average sentiment by date"""
        daily_sentiment = defaultdict(list)
        
        for article in articles:
            if article.sentiment_score is not None:
                date_str = article.published_date.strftime('%Y-%m-%d')
                daily_sentiment[date_str].append(article.sentiment_score)
        
        # Calculate averages
        sentiment_averages = {}
        for date_str, sentiments in daily_sentiment.items():
            if sentiments:
                sentiment_averages[date_str] = np.mean(sentiments)
        
        return sentiment_averages
    
    def _calculate_engagement_score(self, trend_info: Dict[str, Any]) -> float:
        """Calculate engagement score based on various factors"""
        # Simplified engagement score based on article count and trend
        article_count = trend_info['article_count']
        trend_score = trend_info['trend_score']
        
        # Normalize article count (assuming max 100 articles per day per topic)
        normalized_count = min(article_count / 10.0, 1.0)
        
        # Combine with trend score
        engagement = (normalized_count * 0.7) + (trend_score * 0.3)
        
        return min(max(engagement, 0.0), 1.0)
    
    def generate_trend_predictions(self, topic: str, country: str, days_ahead: int = 7) -> Optional[Dict[str, Any]]:
        """Generate predictions for future trends"""
        db = SessionLocal()
        try:
            # Get historical trend data
            historical_trends = (db.query(TopicTrend)
                                .filter(and_(
                                    TopicTrend.theme == topic,
                                    TopicTrend.country == country
                                ))
                                .order_by(TopicTrend.date)
                                .limit(30)  # Last 30 data points
                                .all())
            
            if len(historical_trends) < 7:
                logger.warning(f"Insufficient data for prediction: {topic} in {country}")
                return None
            
            # Extract time series data
            dates = [trend.date for trend in historical_trends]
            scores = [trend.trend_score for trend in historical_trends]
            
            # Simple linear regression for prediction
            x = np.arange(len(scores))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, scores)
            
            # Predict future value
            future_x = len(scores) + days_ahead
            predicted_score = slope * future_x + intercept
            
            # Ensure prediction is within bounds
            predicted_score = min(max(predicted_score, 0.0), 1.0)
            
            # Calculate confidence based on R-squared
            confidence = max(0.1, r_value ** 2)  # R-squared as confidence
            
            # Save prediction to database
            prediction_date = dates[-1] + timedelta(days=days_ahead)
            
            prediction = TopicPrediction(
                theme=topic,
                country=country,
                prediction_date=prediction_date,
                predicted_trend_score=predicted_score,
                confidence=confidence,
                model_version="linear_regression_v1"
            )
            
            db.add(prediction)
            db.commit()
            
            logger.debug(f"Generated prediction for {topic} in {country}: {predicted_score:.3f} (confidence: {confidence:.3f})")
            
            return {
                'topic': topic,
                'country': country,
                'prediction_date': prediction_date,
                'predicted_score': predicted_score,
                'confidence': confidence,
                'current_score': scores[-1],
                'trend_direction': 'rising' if slope > 0 else 'falling' if slope < 0 else 'stable'
            }
            
        except Exception as e:
            logger.error(f"Error generating prediction for {topic} in {country}: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def calculate_global_trends(self) -> Dict[str, Any]:
        """Calculate global trend statistics across all topics and countries"""
        db = SessionLocal()
        try:
            # Get recent trends (last 7 days)
            recent_cutoff = datetime.now() - timedelta(days=7)
            
            recent_trends = (db.query(TopicTrend)
                           .filter(TopicTrend.date >= recent_cutoff)
                           .all())
            
            if not recent_trends:
                return {}
            
            # Calculate global statistics
            topic_averages = defaultdict(list)
            country_averages = defaultdict(list)
            all_scores = []
            
            for trend in recent_trends:
                topic_averages[trend.theme].append(trend.trend_score)
                country_averages[trend.country].append(trend.trend_score)
                all_scores.append(trend.trend_score)
            
            # Calculate averages
            global_stats = {
                'overall_trend': np.mean(all_scores) if all_scores else 0.5,
                'trend_volatility': np.std(all_scores) if all_scores else 0.0,
                'top_trending_topics': self._get_top_trending(topic_averages),
                'top_trending_countries': self._get_top_trending(country_averages),
                'calculation_date': datetime.now().isoformat(),
                'data_points': len(recent_trends)
            }
            
            return global_stats
            
        except Exception as e:
            logger.error(f"Error calculating global trends: {e}")
            return {}
        finally:
            db.close()
    
    def _get_top_trending(self, category_scores: Dict[str, List[float]], top_n: int = 5) -> List[Dict[str, Any]]:
        """Get top trending items from category scores"""
        trending = []
        
        for category, scores in category_scores.items():
            if scores:
                avg_score = np.mean(scores)
                trending.append({
                    'name': category,
                    'average_score': avg_score,
                    'data_points': len(scores)
                })
        
        # Sort by average score and return top N
        trending.sort(key=lambda x: x['average_score'], reverse=True)
        return trending[:top_n]
    
    def cleanup_old_trends(self, days: int = 90) -> int:
        """Clean up trend data older than specified days"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Count trends to be deleted
            old_trends_count = (db.query(TopicTrend)
                              .filter(TopicTrend.date < cutoff_date)
                              .count())
            
            if old_trends_count == 0:
                logger.info("No old trends to clean up")
                return 0
            
            # Delete old trends
            deleted_count = (db.query(TopicTrend)
                           .filter(TopicTrend.date < cutoff_date)
                           .delete(synchronize_session=False))
            
            # Also clean up old predictions
            old_predictions_count = (db.query(TopicPrediction)
                                   .filter(TopicPrediction.prediction_date < cutoff_date)
                                   .delete(synchronize_session=False))
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} trends and {old_predictions_count} predictions older than {days} days")
            return deleted_count + old_predictions_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old trends: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    def get_trend_statistics(self) -> Dict[str, Any]:
        """Get comprehensive trend statistics"""
        db = SessionLocal()
        try:
            # Basic counts
            total_trends = db.query(TopicTrend).count()
            total_predictions = db.query(TopicPrediction).count()
            
            # Recent activity
            recent_cutoff = datetime.now() - timedelta(days=7)
            recent_trends = db.query(TopicTrend).filter(TopicTrend.created_at >= recent_cutoff).count()
            
            # Topic coverage
            topics_with_trends = (db.query(TopicTrend.theme)
                                .distinct()
                                .count())
            
            countries_with_trends = (db.query(TopicTrend.country)
                                   .distinct()
                                   .count())
            
            # Date range
            oldest_trend = (db.query(TopicTrend)
                          .order_by(TopicTrend.date)
                          .first())
            
            newest_trend = (db.query(TopicTrend)
                          .order_by(desc(TopicTrend.date))
                          .first())
            
            stats = {
                'total_trends': total_trends,
                'total_predictions': total_predictions,
                'recent_trends_7d': recent_trends,
                'topics_covered': topics_with_trends,
                'countries_covered': countries_with_trends,
                'date_range': {
                    'oldest': oldest_trend.date.isoformat() if oldest_trend else None,
                    'newest': newest_trend.date.isoformat() if newest_trend else None
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting trend statistics: {e}")
            return {}
        finally:
            db.close() 