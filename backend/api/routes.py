from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from database import get_db
from models import Article, NewsSource, TopicTrend, TopicPrediction
from api.schemas import (
    ArticleResponse, NewsSearchQuery, TrendQuery,
    TopicListResponse, CountryTopicsResponse, LiveTrendsResponse,
    PredictionResponse, TopicTrendResponse
)
from news_aggregator import news_aggregator
from api.sentiment_api import router as sentiment_router
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Include sentiment analysis routes under /sentiment
router.include_router(sentiment_router, prefix="/sentiment")

@router.get("/topics", response_model=TopicListResponse)
async def get_topics(db: Session = Depends(get_db)):
    """Get list of all available topics"""
    try:
        # Always return the configured topics, even if database is not available
        available_topics = settings.NEWS_TOPICS
        
        # Try to get topic counts from database if available
        topic_counts = {}
        try:
            for topic in settings.NEWS_TOPICS:
                count = db.query(Article).filter(Article.primary_theme == topic).count()
                topic_counts[topic] = count
        except Exception as db_error:
            logger.warning(f"Could not get topic counts from database: {db_error}")
            # Set default counts to 0
            topic_counts = {topic: 0 for topic in settings.NEWS_TOPICS}
        
        return TopicListResponse(
            topics=available_topics,
            total_count=len(available_topics)
        )
    except Exception as e:
        logger.error(f"Error getting topics: {e}")
        # Return configured topics as fallback
        return TopicListResponse(
            topics=settings.NEWS_TOPICS,
            total_count=len(settings.NEWS_TOPICS)
        )

@router.get("/trends/{topic}")
async def get_topic_trends(
    topic: str,
    country: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get trend data for a specific topic"""
    try:
        # Validate topic - allow partial matches
        matched_topic = None
        for available_topic in settings.NEWS_TOPICS:
            if topic.lower() in available_topic.lower() or available_topic.lower() in topic.lower():
                matched_topic = available_topic
                break
        
        if not matched_topic:
            raise HTTPException(status_code=404, detail=f"Topic not found. Available topics: {settings.NEWS_TOPICS}")
        
        # Convert date strings to datetime objects
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                # Handle different date formats
                if 'T' in start_date:
                    start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    # Assume it's just a date, add time component
                    start_datetime = datetime.fromisoformat(f"{start_date}T00:00:00")
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}. Use YYYY-MM-DD or ISO format.")
        
        if end_date:
            try:
                # Handle different date formats
                if 'T' in end_date:
                    end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    # Assume it's just a date, add end of day time component
                    end_datetime = datetime.fromisoformat(f"{end_date}T23:59:59")
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}. Use YYYY-MM-DD or ISO format.")
        
        # Try to build query
        try:
            query = db.query(TopicTrend).filter(TopicTrend.theme == matched_topic)
            
            if country:
                query = query.filter(TopicTrend.country == country)
            
            if start_datetime:
                query = query.filter(TopicTrend.date >= start_datetime)
            
            if end_datetime:
                query = query.filter(TopicTrend.date <= end_datetime)
            
            # Get trends ordered by date
            trends = query.order_by(desc(TopicTrend.date)).limit(limit).all()
            
            return [TopicTrendResponse.from_orm(trend) for trend in trends]
            
        except Exception as db_error:
            logger.warning(f"Database query failed: {db_error}")
            # Return empty data if database is not available
            return []
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting topic trends: {e}")
        # Return empty data instead of 500 error for now
        return []

@router.get("/countries/{country}/topics", response_model=CountryTopicsResponse)
async def get_country_topics(
    country: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get topics by country"""
    try:
        # Convert date strings to datetime objects
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                if 'T' in start_date:
                    start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    start_datetime = datetime.fromisoformat(f"{start_date}T00:00:00")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}")
        
        if end_date:
            try:
                if 'T' in end_date:
                    end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    end_datetime = datetime.fromisoformat(f"{end_date}T23:59:59")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}")
        
        # Set default date range if not provided
        if not end_datetime:
            end_datetime = datetime.now()
        if not start_datetime:
            start_datetime = end_datetime - timedelta(days=30)
        
        # Get topic trends for the country
        trends = (db.query(TopicTrend)
                 .filter(
                     and_(
                         TopicTrend.country == country,
                         TopicTrend.date >= start_datetime,
                         TopicTrend.date <= end_datetime
                     )
                 )
                 .order_by(desc(TopicTrend.trend_score))
                 .all())
        
        if not trends:
            raise HTTPException(status_code=404, detail="No data found for this country")
        
        return CountryTopicsResponse(
            country=country,
            topics=[TopicTrendResponse.from_orm(trend) for trend in trends],
            date_range={
                "start_date": start_datetime,
                "end_date": end_datetime
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting country topics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trends/{topic}/analysis")
async def get_topic_analysis(
    topic: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get comprehensive analysis for a specific topic"""
    try:
        # Validate topic
        matched_topic = None
        for available_topic in settings.NEWS_TOPICS:
            if topic.lower() in available_topic.lower() or available_topic.lower() in topic.lower():
                matched_topic = available_topic
                break
        
        if not matched_topic:
            raise HTTPException(status_code=404, detail=f"Topic not found. Available topics: {settings.NEWS_TOPICS}")
        
        # Convert date strings to datetime objects
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                if 'T' in start_date:
                    start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    start_datetime = datetime.fromisoformat(f"{start_date}T00:00:00")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}")
        
        if end_date:
            try:
                if 'T' in end_date:
                    end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    end_datetime = datetime.fromisoformat(f"{end_date}T23:59:59")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}")
        
        # Set default date range if not provided (last 30 days)
        if not end_datetime:
            end_datetime = datetime.now()
        if not start_datetime:
            start_datetime = end_datetime - timedelta(days=30)
        
        # Get trend data for the topic
        trends = (db.query(TopicTrend)
                 .filter(
                     and_(
                         TopicTrend.theme == matched_topic,
                         TopicTrend.date >= start_datetime,
                         TopicTrend.date <= end_datetime
                     )
                 )
                 .order_by(TopicTrend.date)
                 .all())
        
        # Get articles for the topic (for top stories and additional analysis)
        articles = (db.query(Article)
                   .filter(
                       and_(
                           Article.primary_theme == matched_topic,
                           Article.published_date >= start_datetime,
                           Article.published_date <= end_datetime
                       )
                   )
                   .order_by(desc(Article.published_date))
                   .all())
        
        # Calculate analysis metrics
        analysis = calculate_topic_analysis(trends, articles, matched_topic, start_datetime, end_datetime)
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting topic analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/countries/trends")
async def get_countries_trends(
    topic: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get aggregated trend data for all countries for a specific topic (for map visualization)"""
    try:
        logger.info(f"Countries trends request - topic: {topic}, start_date: {start_date}, end_date: {end_date}")
        
        # Convert date strings to datetime objects
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                if 'T' in start_date:
                    start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    start_datetime = datetime.fromisoformat(f"{start_date}T00:00:00")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}")
        
        if end_date:
            try:
                if 'T' in end_date:
                    end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    end_datetime = datetime.fromisoformat(f"{end_date}T23:59:59")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}")
        
        # Set default date range if not provided (last 7 days)
        if not end_datetime:
            end_datetime = datetime.now()
        if not start_datetime:
            start_datetime = end_datetime - timedelta(days=7)
        
        # Build query
        query = db.query(TopicTrend).filter(
            and_(
                TopicTrend.date >= start_datetime,
                TopicTrend.date <= end_datetime
            )
        )
        
        # Filter by topic if provided
        if topic:
            # Validate topic - allow partial matches
            matched_topic = None
            for available_topic in settings.NEWS_TOPICS:
                if topic.lower() in available_topic.lower() or available_topic.lower() in topic.lower():
                    matched_topic = available_topic
                    break
            
            if matched_topic:
                query = query.filter(TopicTrend.theme == matched_topic)
            else:
                return []
        
        # Get all trends
        trends = query.all()
        
        if not trends:
            # Fallback: Generate trend data from articles if no trends exist
            logger.info("No trends found, generating from articles...")
            return generate_trends_from_articles_fallback(db, topic, start_datetime, end_datetime)
        
        # Aggregate by country
        country_data = {}
        for trend in trends:
            country = trend.country
            if country not in country_data:
                country_data[country] = {
                    'country': country,
                    'article_count': 0,
                    'trend_score': 0,
                    'sentiment_avg': 0,
                    'count': 0,
                    'latest_date': trend.date
                }
            
            data = country_data[country]
            data['article_count'] += trend.article_count or 0
            data['trend_score'] += trend.trend_score or 0
            data['sentiment_avg'] += trend.sentiment_avg or 0
            data['count'] += 1
            
            # Keep track of latest date
            if trend.date > data['latest_date']:
                data['latest_date'] = trend.date
        
        # Calculate averages and format response
        result = []
        for country, data in country_data.items():
            if data['count'] > 0:
                result.append({
                    'country': country,
                    'article_count': data['article_count'],
                    'trend_score': data['trend_score'] / data['count'],
                    'sentiment_avg': data['sentiment_avg'] / data['count'],
                    'latest_date': data['latest_date'].isoformat(),
                    'data_points': data['count']
                })
        
        # Sort by article count (most active countries first)
        result.sort(key=lambda x: x['article_count'], reverse=True)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting countries trends: {e}")
        return []

@router.get("/live", response_model=LiveTrendsResponse)
async def get_live_trends(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """Get real-time trending topics"""
    try:
        # Get recent trending topics (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        trending_topics = (db.query(TopicTrend)
                          .filter(TopicTrend.created_at >= cutoff_time)
                          .order_by(desc(TopicTrend.trend_score))
                          .all())
        
        # Aggregate by topic to avoid duplicates
        topic_aggregates = {}
        for trend in trending_topics:
            topic = trend.theme
            if topic not in topic_aggregates:
                topic_aggregates[topic] = {
                    "topic": topic,
                    "countries": [],
                    "total_article_count": 0,
                    "max_trend_score": 0,
                    "avg_sentiment": 0,
                    "sentiment_count": 0,
                    "top_country": trend.country,
                    "top_country_articles": trend.article_count
                }
            
            agg = topic_aggregates[topic]
            agg["countries"].append(trend.country)
            agg["total_article_count"] += trend.article_count or 0
            agg["max_trend_score"] = max(agg["max_trend_score"], trend.trend_score or 0)
            
            # Track sentiment
            if trend.sentiment_avg is not None:
                agg["avg_sentiment"] += trend.sentiment_avg
                agg["sentiment_count"] += 1
            
            # Track top country (most articles)
            if (trend.article_count or 0) > agg["top_country_articles"]:
                agg["top_country"] = trend.country
                agg["top_country_articles"] = trend.article_count or 0
        
        # Format trending topics data
        trending_data = []
        for topic, agg in topic_aggregates.items():
            # Calculate average sentiment
            avg_sentiment = None
            if agg["sentiment_count"] > 0:
                avg_sentiment = agg["avg_sentiment"] / agg["sentiment_count"]
            
            trending_data.append({
                "topic": topic,
                "country": agg["top_country"],  # Show country with most articles
                "trend_score": agg["max_trend_score"],
                "article_count": agg["total_article_count"],
                "change_24h": agg["max_trend_score"],  # Simplified for now
                "sentiment": avg_sentiment,
                "countries_count": len(set(agg["countries"]))  # Number of countries
            })
        
        # Sort by trend score and limit
        trending_data.sort(key=lambda x: x["trend_score"], reverse=True)
        trending_data = trending_data[:limit]
        
        return LiveTrendsResponse(
            trending_topics=trending_data,
            last_updated=datetime.now(),
            update_interval=settings.NEWS_FETCH_INTERVAL
        )
        
    except Exception as e:
        logger.error(f"Error getting live trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/predictions")
async def get_predictions(
    topic: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """Get ML trend predictions"""
    try:
        # Build query
        query = db.query(TopicPrediction)
        
        if topic:
            query = query.filter(TopicPrediction.theme == topic)
        
        if country:
            query = query.filter(TopicPrediction.country == country)
        
        # Get recent predictions
        predictions = (query.order_by(desc(TopicPrediction.created_at))
                      .limit(limit)
                      .all())
        
        # Format response
        prediction_data = []
        for pred in predictions:
            # Get current trend for comparison
            current_trend = (db.query(TopicTrend)
                           .filter(
                               and_(
                                   TopicTrend.theme == pred.theme,
                                   TopicTrend.country == pred.country
                               )
                           )
                           .order_by(desc(TopicTrend.date))
                           .first())
            
            current_trend_score = current_trend.trend_score if current_trend else 0.0
            
            prediction_data.append(PredictionResponse(
                theme=pred.theme,
                country=pred.country,
                current_trend=current_trend_score,
                predicted_trend=pred.predicted_trend_score,
                confidence=pred.confidence,
                prediction_date=pred.prediction_date
            ))
        
        return prediction_data
        
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/articles/search")
async def search_articles(
    query: NewsSearchQuery = Depends(),
    db: Session = Depends(get_db)
):
    """Search articles with filters"""
    try:
        # Build query
        article_query = db.query(Article)
        
        # Apply filters
        if query.query:
            search_term = f"%{query.query}%"
            article_query = article_query.filter(
                Article.title.ilike(search_term) | 
                Article.content.ilike(search_term)
            )
        
        if query.topics:
            article_query = article_query.filter(Article.primary_theme.in_(query.topics))
        
        if query.countries:
            article_query = article_query.filter(Article.country.in_(query.countries))
        
        if query.start_date:
            article_query = article_query.filter(Article.published_date >= query.start_date)
        
        if query.end_date:
            article_query = article_query.filter(Article.published_date <= query.end_date)
        
        # Get total count
        total_count = article_query.count()
        
        # Apply pagination and ordering
        articles = (article_query.order_by(desc(Article.published_date))
                   .offset(query.offset)
                   .limit(query.limit)
                   .all())
        
        # Convert to response format with source names
        article_responses = []
        for article in articles:
            article_dict = ArticleResponse.from_orm(article).dict()
            article_dict['source_name'] = article.source.name if article.source else 'Unknown Source'
            article_responses.append(article_dict)
        
        return {
            "articles": article_responses,
            "total_count": total_count,
            "limit": query.limit,
            "offset": query.offset
        }
        
    except Exception as e:
        logger.error(f"Error searching articles: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/articles/recent")
async def get_recent_articles(
    hours: int = Query(24, le=168),  # Max 1 week
    limit: int = Query(20, le=100),
    topic: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get recent articles"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        query = (db.query(Article)
                .filter(Article.published_date >= cutoff_time))
        
        if topic:
            query = query.filter(Article.primary_theme == topic)
        
        if country:
            query = query.filter(Article.country == country)
        
        articles = (query.order_by(desc(Article.published_date))
                   .limit(limit)
                   .all())
        
        # Convert to response format with source names
        article_responses = []
        for article in articles:
            article_dict = ArticleResponse.from_orm(article).dict()
            article_dict['source_name'] = article.source.name if article.source else 'Unknown Source'
            article_responses.append(article_dict)
        
        return article_responses
        
    except Exception as e:
        logger.error(f"Error getting recent articles: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get aggregation statistics"""
    try:
        stats = news_aggregator.get_statistics()
        
        # Add more detailed statistics
        # Top countries by article count
        top_countries = (db.query(Article.country, func.count(Article.id).label('count'))
                        .filter(Article.country.isnot(None))
                        .group_by(Article.country)
                        .order_by(desc('count'))
                        .limit(10)
                        .all())
        
        stats['top_countries'] = [
            {"country": country, "article_count": count} 
            for country, count in top_countries
        ]
        
        # Recent activity
        last_hour = datetime.now() - timedelta(hours=1)
        recent_activity = db.query(Article).filter(Article.scraped_date >= last_hour).count()
        stats['recent_activity_1h'] = recent_activity
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/refresh")
async def refresh_news():
    """Manually trigger news refresh"""
    try:
        count = news_aggregator.fetch_and_process_news()
        return {
            "message": "News refresh completed",
            "articles_processed": count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error refreshing news: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh news")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint that doesn't require database"""
    return {
        "status": "success",
        "message": "API is working",
        "timestamp": datetime.now().isoformat(),
        "cors_enabled": True
    }

def calculate_topic_analysis(trends: List[TopicTrend], articles: List[Article], topic: str, start_datetime: datetime, end_datetime: datetime) -> Dict[str, Any]:
    """Calculate comprehensive topic analysis"""
    from collections import defaultdict
    import statistics
    
    # Basic metrics
    total_articles = len(articles)
    active_countries = len(set(article.country for article in articles if article.country))
    
    # Time series data for charting
    daily_counts = defaultdict(int)
    daily_sentiment = defaultdict(list)
    
    # Process articles for time series
    for article in articles:
        date_str = article.published_date.strftime('%Y-%m-%d')
        daily_counts[date_str] += 1
        if article.sentiment_score is not None:
            daily_sentiment[date_str].append(article.sentiment_score)
    
    # Create time series data
    time_series = []
    all_dates = sorted(set(daily_counts.keys()))
    
    for date_str in all_dates:
        count = daily_counts[date_str]
        avg_sentiment = None
        if daily_sentiment[date_str]:
            avg_sentiment = statistics.mean(daily_sentiment[date_str])
        
        time_series.append({
            'date': date_str,
            'article_count': count,
            'sentiment_avg': avg_sentiment
        })
    
    # Calculate overall sentiment
    all_sentiments = [a.sentiment_score for a in articles if a.sentiment_score is not None]
    avg_sentiment = statistics.mean(all_sentiments) if all_sentiments else None
    
    # Find peak activity date
    peak_date = None
    max_count = 0
    for date_str, count in daily_counts.items():
        if count > max_count:
            max_count = count
            peak_date = date_str
    
    # Calculate trend direction
    trend_direction = "stable"
    if len(time_series) >= 7:
        # Compare recent week vs previous week
        recent_week = time_series[-7:]
        previous_week = time_series[-14:-7] if len(time_series) >= 14 else time_series[:-7]
        
        recent_avg = statistics.mean([d['article_count'] for d in recent_week])
        previous_avg = statistics.mean([d['article_count'] for d in previous_week])
        
        if recent_avg > previous_avg * 1.2:
            trend_direction = "rising"
        elif recent_avg < previous_avg * 0.8:
            trend_direction = "falling"
    
    # Get top stories (5 most recent)
    top_stories = []
    for article in articles[:5]:
        top_stories.append({
            'id': article.id,
            'title': article.title,
            'url': article.url,
            'source': article.source.name if article.source else 'Unknown Source',
            'country': article.country,
            'published_date': article.published_date.isoformat(),
            'sentiment_score': article.sentiment_score,
            'summary': article.content[:200] + "..." if article.content and len(article.content) > 200 else article.content
        })
    
    # Country breakdown
    country_counts = defaultdict(int)
    for article in articles:
        if article.country:
            country_counts[article.country] += 1
    
    top_countries = sorted(
        [{'country': country, 'article_count': count} for country, count in country_counts.items()],
        key=lambda x: x['article_count'],
        reverse=True
    )[:10]
    
    return {
        'topic': topic,
        'date_range': {
            'start_date': start_datetime.isoformat(),
            'end_date': end_datetime.isoformat()
        },
        'metrics': {
            'total_articles': total_articles,
            'active_countries': active_countries,
            'avg_sentiment': avg_sentiment,
            'peak_date': peak_date,
            'peak_count': max_count,
            'trend_direction': trend_direction
        },
        'time_series': time_series,
        'top_stories': top_stories,
        'top_countries': top_countries,
        'analysis_timestamp': datetime.now().isoformat()
    }

def generate_trends_from_articles_fallback(db: Session, topic: Optional[str], start_datetime: datetime, end_datetime: datetime):
    """Generate trend data from articles when no trends exist"""
    from collections import defaultdict
    
    try:
        # Build query for articles
        query = db.query(Article).filter(
            and_(
                Article.published_date >= start_datetime,
                Article.published_date <= end_datetime,
                Article.country.isnot(None),
                Article.primary_theme.isnot(None)
            )
        )
        
        # Filter by topic if provided
        if topic:
            matched_topic = None
            for available_topic in settings.NEWS_TOPICS:
                if topic.lower() in available_topic.lower() or available_topic.lower() in topic.lower():
                    matched_topic = available_topic
                    break
            
            if matched_topic:
                query = query.filter(Article.primary_theme == matched_topic)
            else:
                return []
        
        articles = query.all()
        
        if not articles:
            return []
        
        # Group articles by country
        country_data = defaultdict(lambda: {
            'articles': [],
            'article_count': 0,
            'sentiment_scores': []
        })
        
        for article in articles:
            country = article.country
            country_data[country]['articles'].append(article)
            country_data[country]['article_count'] += 1
            if article.sentiment_score is not None:
                country_data[country]['sentiment_scores'].append(article.sentiment_score)
        
        # Generate trend data
        result = []
        for country, data in country_data.items():
            # Calculate trend score based on article count (simple heuristic)
            article_count = data['article_count']
            trend_score = min(article_count / 10.0, 1.0)  # Normalize to 0-1, max at 10 articles
            
            # Calculate average sentiment
            sentiment_avg = 0
            if data['sentiment_scores']:
                sentiment_avg = sum(data['sentiment_scores']) / len(data['sentiment_scores'])
            
            result.append({
                'country': country,
                'article_count': article_count,
                'trend_score': trend_score,
                'sentiment_avg': sentiment_avg,
                'latest_date': max(a.published_date for a in data['articles']).isoformat(),
                'data_points': 1
            })
        
        # Sort by article count (most active countries first)
        result.sort(key=lambda x: x['article_count'], reverse=True)
        
        logger.info(f"Generated fallback trend data for {len(result)} countries")
        return result
        
    except Exception as e:
        logger.error(f"Error generating fallback trend data: {e}")
        return [] 