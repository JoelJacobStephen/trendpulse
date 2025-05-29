import os
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from database import SessionLocal
from models import Article, TopicTrend, NewsSource
from sentiment_analyzer import sentiment_analyzer
from config import settings

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    """Comprehensive trend analysis using TensorFlow and sentiment analysis"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.trend_model = None
        self.sentiment_weights = {
            'positive': 1.2,
            'neutral': 1.0,
            'negative': 0.8
        }
        self._initialize_trend_model()
    
    def _initialize_trend_model(self):
        """Initialize TensorFlow model for trend prediction"""
        try:
            # Simple LSTM model for trend prediction
            self.trend_model = tf.keras.Sequential([
                tf.keras.layers.LSTM(64, return_sequences=True, input_shape=(7, 6)),  # 7 days, 6 features
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.LSTM(32, return_sequences=False),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(16, activation='relu'),
                tf.keras.layers.Dense(1, activation='linear')  # Predict trend direction
            ])
            
            self.trend_model.compile(
                optimizer='adam',
                loss='mse',
                metrics=['mae']
            )
            
            logger.info("Initialized TensorFlow trend prediction model")
            
        except Exception as e:
            logger.error(f"Error initializing trend model: {e}")
            self.trend_model = None
    
    def analyze_topic_trends(self, days: int = 30, min_articles: int = 5) -> Dict[str, Any]:
        """Analyze trends for all topics with sentiment integration"""
        db = SessionLocal()
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get articles from the specified period
            articles = db.query(Article).filter(
                Article.published_date >= cutoff_date,
                Article.primary_theme.is_not(None)
            ).all()
            
            if not articles:
                return {"error": "No articles found for analysis"}
            
            # Group articles by topic and date
            topic_data = defaultdict(lambda: defaultdict(list))
            
            for article in articles:
                date_key = article.published_date.date()
                topic = article.primary_theme
                topic_data[topic][date_key].append(article)
            
            trend_results = {}
            
            for topic, date_articles in topic_data.items():
                if sum(len(articles) for articles in date_articles.values()) < min_articles:
                    continue
                
                # Analyze trend for this topic
                trend_result = self._analyze_single_topic_trend(topic, date_articles, days)
                if trend_result:
                    trend_results[topic] = trend_result
            
            # Calculate overall trends
            overall_analysis = self._calculate_overall_trends(trend_results)
            
            return {
                'period_days': days,
                'total_topics': len(trend_results),
                'topics': trend_results,
                'overall': overall_analysis,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing topic trends: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    def _analyze_single_topic_trend(self, topic: str, date_articles: Dict, days: int) -> Optional[Dict[str, Any]]:
        """Analyze trend for a single topic"""
        try:
            # Create time series data
            dates = sorted(date_articles.keys())
            if len(dates) < 3:  # Need at least 3 data points
                return None
            
            # Calculate daily metrics
            daily_metrics = []
            sentiment_scores = []
            
            for date in dates:
                articles = date_articles[date]
                
                # Basic metrics
                article_count = len(articles)
                total_word_count = sum(article.word_count or 0 for article in articles)
                avg_word_count = total_word_count / article_count if article_count > 0 else 0
                
                # Sentiment analysis
                article_sentiments = []
                for article in articles:
                    if hasattr(article, 'sentiment_score') and article.sentiment_score is not None:
                        article_sentiments.append(article.sentiment_score)
                    else:
                        # Analyze sentiment if not available
                        sentiment_result = sentiment_analyzer.analyze_article(
                            article.title or '', 
                            article.content or ''
                        )
                        if sentiment_result:
                            article_sentiments.append(sentiment_result.get('sentiment_score', 0.0))
                
                avg_sentiment = np.mean(article_sentiments) if article_sentiments else 0.0
                sentiment_variance = np.var(article_sentiments) if len(article_sentiments) > 1 else 0.0
                
                # Source diversity
                unique_sources = len(set(article.source_id for article in articles))
                
                # Geographic spread
                unique_countries = len(set(article.country for article in articles if article.country))
                
                daily_metrics.append({
                    'date': date,
                    'article_count': article_count,
                    'avg_word_count': avg_word_count,
                    'avg_sentiment': avg_sentiment,
                    'sentiment_variance': sentiment_variance,
                    'source_diversity': unique_sources,
                    'geographic_spread': unique_countries
                })
                
                sentiment_scores.append(avg_sentiment)
            
            # Calculate trend metrics
            trend_analysis = self._calculate_trend_metrics(daily_metrics)
            
            # Sentiment trend analysis
            sentiment_trend = self._calculate_sentiment_trend(sentiment_scores)
            
            # Use TensorFlow model for prediction if available
            ml_prediction = self._predict_trend_with_model(daily_metrics)
            
            return {
                'topic': topic,
                'analysis_period': {
                    'start_date': str(dates[0]),
                    'end_date': str(dates[-1]),
                    'days_analyzed': len(dates)
                },
                'volume_trend': trend_analysis['volume_trend'],
                'sentiment_trend': sentiment_trend,
                'prediction': ml_prediction,
                'daily_metrics': daily_metrics[-7:],  # Last 7 days only
                'summary': {
                    'total_articles': sum(m['article_count'] for m in daily_metrics),
                    'avg_daily_articles': np.mean([m['article_count'] for m in daily_metrics]),
                    'trend_direction': trend_analysis['direction'],
                    'trend_strength': trend_analysis['strength'],
                    'overall_sentiment': np.mean(sentiment_scores),
                    'sentiment_volatility': np.std(sentiment_scores)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend for topic {topic}: {e}")
            return None
    
    def _calculate_trend_metrics(self, daily_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trend metrics from daily data"""
        try:
            article_counts = [m['article_count'] for m in daily_metrics]
            
            if len(article_counts) < 2:
                return {'direction': 'insufficient_data', 'strength': 0.0, 'volume_trend': 0.0}
            
            # Linear regression for trend direction
            x = np.arange(len(article_counts))
            y = np.array(article_counts)
            
            # Calculate slope
            slope = np.polyfit(x, y, 1)[0]
            
            # Calculate correlation coefficient for trend strength
            correlation = np.corrcoef(x, y)[0, 1] if len(x) > 1 else 0.0
            
            # Determine direction
            if slope > 0.1:
                direction = 'increasing'
            elif slope < -0.1:
                direction = 'decreasing'
            else:
                direction = 'stable'
            
            # Calculate moving averages
            if len(article_counts) >= 7:
                recent_avg = np.mean(article_counts[-3:])  # Last 3 days
                earlier_avg = np.mean(article_counts[-7:-4])  # 4-7 days ago
                volume_trend = (recent_avg - earlier_avg) / max(earlier_avg, 1)
            else:
                volume_trend = slope / max(np.mean(article_counts), 1)
            
            return {
                'direction': direction,
                'strength': abs(correlation),
                'volume_trend': volume_trend,
                'slope': slope,
                'correlation': correlation
            }
            
        except Exception as e:
            logger.error(f"Error calculating trend metrics: {e}")
            return {'direction': 'error', 'strength': 0.0, 'volume_trend': 0.0}
    
    def _calculate_sentiment_trend(self, sentiment_scores: List[float]) -> Dict[str, Any]:
        """Calculate sentiment trend metrics"""
        try:
            if len(sentiment_scores) < 2:
                return {'direction': 'insufficient_data', 'change': 0.0}
            
            # Calculate sentiment trend
            x = np.arange(len(sentiment_scores))
            y = np.array(sentiment_scores)
            
            slope = np.polyfit(x, y, 1)[0]
            
            # Recent vs earlier sentiment
            recent_sentiment = np.mean(sentiment_scores[-3:]) if len(sentiment_scores) >= 3 else sentiment_scores[-1]
            earlier_sentiment = np.mean(sentiment_scores[:-3]) if len(sentiment_scores) > 3 else sentiment_scores[0]
            
            sentiment_change = recent_sentiment - earlier_sentiment
            
            # Determine direction
            if sentiment_change > 0.05:
                direction = 'improving'
            elif sentiment_change < -0.05:
                direction = 'deteriorating'
            else:
                direction = 'stable'
            
            return {
                'direction': direction,
                'change': sentiment_change,
                'current_sentiment': recent_sentiment,
                'sentiment_slope': slope,
                'volatility': np.std(sentiment_scores)
            }
            
        except Exception as e:
            logger.error(f"Error calculating sentiment trend: {e}")
            return {'direction': 'error', 'change': 0.0}
    
    def _predict_trend_with_model(self, daily_metrics: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Use TensorFlow model to predict future trends"""
        if not self.trend_model or len(daily_metrics) < 7:
            return None
        
        try:
            # Prepare features for the last 7 days
            features = []
            for metric in daily_metrics[-7:]:
                feature_vector = [
                    metric['article_count'],
                    metric['avg_word_count'] / 1000,  # Normalize
                    metric['avg_sentiment'],
                    metric['sentiment_variance'],
                    metric['source_diversity'],
                    metric['geographic_spread']
                ]
                features.append(feature_vector)
            
            # Ensure we have exactly 7 days
            while len(features) < 7:
                features.insert(0, features[0])  # Pad with first available data
            
            # Normalize features
            features_array = np.array(features).reshape(1, 7, 6)
            
            # Make prediction
            prediction = self.trend_model.predict(features_array, verbose=0)[0][0]
            
            # Interpret prediction
            if prediction > 0.1:
                predicted_direction = 'increasing'
            elif prediction < -0.1:
                predicted_direction = 'decreasing'
            else:
                predicted_direction = 'stable'
            
            return {
                'predicted_direction': predicted_direction,
                'predicted_change': float(prediction),
                'confidence': min(abs(prediction), 1.0),
                'method': 'tensorflow_lstm'
            }
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            return None
    
    def _calculate_overall_trends(self, topic_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall trends across all topics"""
        try:
            if not topic_results:
                return {}
            
            # Aggregate metrics
            total_articles = sum(result['summary']['total_articles'] for result in topic_results.values())
            
            # Topic direction distribution
            directions = [result['summary']['trend_direction'] for result in topic_results.values()]
            direction_counts = Counter(directions)
            
            # Sentiment distribution
            sentiments = [result['summary']['overall_sentiment'] for result in topic_results.values()]
            avg_sentiment = np.mean(sentiments)
            
            # Most active topics
            most_active = sorted(
                topic_results.items(),
                key=lambda x: x[1]['summary']['total_articles'],
                reverse=True
            )[:5]
            
            # Most trending topics (by volume change)
            most_trending = sorted(
                topic_results.items(),
                key=lambda x: x[1]['volume_trend']['volume_trend'],
                reverse=True
            )[:5]
            
            return {
                'total_articles_analyzed': total_articles,
                'average_sentiment': avg_sentiment,
                'sentiment_distribution': {
                    'positive_topics': sum(1 for s in sentiments if s > 0.1),
                    'neutral_topics': sum(1 for s in sentiments if -0.1 <= s <= 0.1),
                    'negative_topics': sum(1 for s in sentiments if s < -0.1)
                },
                'trend_directions': dict(direction_counts),
                'most_active_topics': [{'topic': topic, 'articles': result['summary']['total_articles']} 
                                     for topic, result in most_active],
                'most_trending_topics': [{'topic': topic, 'trend': result['volume_trend']['volume_trend']} 
                                       for topic, result in most_trending]
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall trends: {e}")
            return {}
    
    def analyze_sentiment_distribution(self, days: int = 7) -> Dict[str, Any]:
        """Analyze sentiment distribution across topics and time"""
        db = SessionLocal()
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get articles with sentiment data
            articles = db.query(Article).filter(
                Article.published_date >= cutoff_date,
                Article.sentiment_score.is_not(None)
            ).all()
            
            if not articles:
                return {"error": "No articles with sentiment data found"}
            
            # Analyze by topic
            topic_sentiments = defaultdict(list)
            daily_sentiments = defaultdict(list)
            
            for article in articles:
                if article.primary_theme:
                    topic_sentiments[article.primary_theme].append(article.sentiment_score)
                
                date_key = article.published_date.date()
                daily_sentiments[date_key].append(article.sentiment_score)
            
            # Calculate topic-wise sentiment
            topic_analysis = {}
            for topic, scores in topic_sentiments.items():
                if len(scores) >= 3:  # Minimum threshold
                    topic_analysis[topic] = {
                        'average_sentiment': np.mean(scores),
                        'sentiment_std': np.std(scores),
                        'article_count': len(scores),
                        'positive_ratio': sum(1 for s in scores if s > 0.1) / len(scores),
                        'negative_ratio': sum(1 for s in scores if s < -0.1) / len(scores),
                        'neutral_ratio': sum(1 for s in scores if -0.1 <= s <= 0.1) / len(scores)
                    }
            
            # Calculate daily sentiment trends
            daily_analysis = {}
            for date, scores in daily_sentiments.items():
                daily_analysis[str(date)] = {
                    'average_sentiment': np.mean(scores),
                    'article_count': len(scores),
                    'sentiment_range': [float(np.min(scores)), float(np.max(scores))]
                }
            
            return {
                'analysis_period': days,
                'total_articles': len(articles),
                'overall_sentiment': np.mean([article.sentiment_score for article in articles]),
                'topic_sentiment': topic_analysis,
                'daily_sentiment': daily_analysis,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment distribution: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    def get_trending_topics(self, hours: int = 24, min_articles: int = 3) -> List[Dict[str, Any]]:
        """Get currently trending topics based on volume and sentiment"""
        db = SessionLocal()
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Get recent articles
            recent_articles = db.query(Article).filter(
                Article.published_date >= cutoff_time,
                Article.primary_theme.is_not(None)
            ).all()
            
            if not recent_articles:
                return []
            
            # Group by topic
            topic_groups = defaultdict(list)
            for article in recent_articles:
                topic_groups[article.primary_theme].append(article)
            
            trending_topics = []
            
            for topic, articles in topic_groups.items():
                if len(articles) < min_articles:
                    continue
                
                # Calculate metrics
                article_count = len(articles)
                avg_sentiment = np.mean([
                    article.sentiment_score for article in articles 
                    if article.sentiment_score is not None
                ]) if any(article.sentiment_score is not None for article in articles) else 0.0
                
                # Calculate trend score (volume + sentiment weighted)
                volume_score = min(article_count / 10, 1.0)  # Normalize volume
                sentiment_boost = 1.0 + (avg_sentiment * 0.5)  # Positive sentiment boost
                trend_score = volume_score * sentiment_boost
                
                trending_topics.append({
                    'topic': topic,
                    'article_count': article_count,
                    'average_sentiment': avg_sentiment,
                    'trend_score': trend_score,
                    'recent_articles': [
                        {
                            'title': article.title,
                            'sentiment_score': article.sentiment_score,
                            'published_date': article.published_date.isoformat()
                        }
                        for article in sorted(articles, key=lambda x: x.published_date, reverse=True)[:3]
                    ]
                })
            
            # Sort by trend score
            trending_topics.sort(key=lambda x: x['trend_score'], reverse=True)
            
            return trending_topics[:10]  # Top 10 trending topics
            
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return []
        finally:
            db.close()

# Global instance
trend_analyzer = TrendAnalyzer() 