from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import numpy as np

from sentiment_analyzer import sentiment_analyzer
from trend_analyzer import trend_analyzer
from database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sentiment"])

# Request models
class TextAnalysisRequest(BaseModel):
    text: str
    method: Optional[str] = None

class ArticleAnalysisRequest(BaseModel):
    title: str
    content: str

class BatchAnalysisRequest(BaseModel):
    texts: List[str]

@router.post("/analyze")
async def analyze_text_sentiment(request: TextAnalysisRequest):
    """Analyze sentiment of provided text"""
    try:
        if not request.text or len(request.text.strip()) < 5:
            raise HTTPException(status_code=400, detail="Text too short for analysis")
        
        if request.method == 'neural':
            result = sentiment_analyzer.analyze_with_model(request.text)
            if not result:
                raise HTTPException(status_code=422, detail="Neural analysis failed, text may be unsuitable")
        elif request.method == 'rules':
            result = sentiment_analyzer.analyze_with_rules(request.text)
        else:
            # Auto method - tries neural first, falls back to rules
            result = sentiment_analyzer.analyze_text(request.text)
        
        return {
            "text_preview": request.text[:100] + "..." if len(request.text) > 100 else request.text,
            "text_length": len(request.text),
            "sentiment_result": result
        }
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(status_code=500, detail="Internal error during sentiment analysis")

@router.post("/analyze-article")
async def analyze_article_sentiment(request: ArticleAnalysisRequest):
    """Analyze sentiment of an article with title and content"""
    try:
        if not request.title and not request.content:
            raise HTTPException(status_code=400, detail="Either title or content must be provided")
        
        result = sentiment_analyzer.analyze_article(request.title, request.content)
        
        return {
            "title": request.title,
            "content_preview": request.content[:200] + "..." if len(request.content) > 200 else request.content,
            "sentiment_result": result
        }
        
    except Exception as e:
        logger.error(f"Error analyzing article sentiment: {e}")
        raise HTTPException(status_code=500, detail="Internal error during article sentiment analysis")

@router.get("/distribution")
async def get_sentiment_distribution(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get sentiment distribution across topics and time"""
    try:
        result = trend_analyzer.analyze_sentiment_distribution(days=days)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sentiment distribution: {e}")
        raise HTTPException(status_code=500, detail="Internal error during sentiment distribution analysis")

@router.get("/trends")
async def get_sentiment_trends(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze trends"),
    min_articles: int = Query(5, ge=1, description="Minimum articles per topic"),
    db: Session = Depends(get_db)
):
    """Get sentiment trends across topics"""
    try:
        result = trend_analyzer.analyze_topic_trends(days=days, min_articles=min_articles)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        # Filter to include sentiment-focused data
        sentiment_trends = {}
        for topic, data in result.get('topics', {}).items():
            sentiment_trends[topic] = {
                'topic': topic,
                'sentiment_trend': data.get('sentiment_trend', {}),
                'overall_sentiment': data.get('summary', {}).get('overall_sentiment', 0),
                'sentiment_volatility': data.get('summary', {}).get('sentiment_volatility', 0),
                'article_count': data.get('summary', {}).get('total_articles', 0)
            }
        
        return {
            'period_days': result.get('period_days'),
            'sentiment_trends': sentiment_trends,
            'overall_sentiment': result.get('overall', {}).get('average_sentiment', 0),
            'generated_at': result.get('generated_at')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sentiment trends: {e}")
        raise HTTPException(status_code=500, detail="Internal error during sentiment trend analysis")

@router.get("/topic/{topic_name}")
async def get_topic_sentiment(
    topic_name: str,
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get detailed sentiment analysis for a specific topic"""
    try:
        from models import Article
        from datetime import datetime, timedelta
        import numpy as np
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get articles for the specific topic
        articles = db.query(Article).filter(
            Article.published_date >= cutoff_date,
            Article.primary_theme == topic_name,
            Article.sentiment_score.is_not(None)
        ).all()
        
        if not articles:
            raise HTTPException(status_code=404, detail=f"No articles found for topic '{topic_name}' with sentiment data")
        
        # Calculate metrics
        sentiment_scores = [article.sentiment_score for article in articles]
        
        # Daily breakdown
        from collections import defaultdict
        daily_sentiments = defaultdict(list)
        for article in articles:
            date_key = article.published_date.date()
            daily_sentiments[date_key].append(article.sentiment_score)
        
        daily_analysis = {}
        for date, scores in daily_sentiments.items():
            daily_analysis[str(date)] = {
                'average_sentiment': np.mean(scores),
                'article_count': len(scores),
                'sentiment_range': [float(np.min(scores)), float(np.max(scores))]
            }
        
        # Recent articles with sentiment
        recent_articles = sorted(articles, key=lambda x: x.published_date, reverse=True)[:10]
        
        return {
            'topic': topic_name,
            'analysis_period': days,
            'total_articles': len(articles),
            'sentiment_summary': {
                'average_sentiment': np.mean(sentiment_scores),
                'sentiment_std': np.std(sentiment_scores),
                'min_sentiment': float(np.min(sentiment_scores)),
                'max_sentiment': float(np.max(sentiment_scores)),
                'positive_ratio': sum(1 for s in sentiment_scores if s > 0.1) / len(sentiment_scores),
                'negative_ratio': sum(1 for s in sentiment_scores if s < -0.1) / len(sentiment_scores),
                'neutral_ratio': sum(1 for s in sentiment_scores if -0.1 <= s <= 0.1) / len(sentiment_scores)
            },
            'daily_sentiment': daily_analysis,
            'recent_articles': [
                {
                    'title': article.title,
                    'sentiment_score': article.sentiment_score,
                    'published_date': article.published_date.isoformat(),
                    'url': article.url
                }
                for article in recent_articles
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting topic sentiment: {e}")
        raise HTTPException(status_code=500, detail="Internal error during topic sentiment analysis")

@router.get("/trending")
async def get_trending_topics(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back for trending topics"),
    min_articles: int = Query(3, ge=1, description="Minimum articles per topic"),
    db: Session = Depends(get_db)
):
    """Get trending topics based on volume and sentiment"""
    try:
        trending_topics = trend_analyzer.get_trending_topics(hours=hours, min_articles=min_articles)
        
        if not trending_topics:
            return {
                'message': 'No trending topics found',
                'trending_topics': [],
                'hours_analyzed': hours
            }
        
        return {
            'trending_topics': trending_topics,
            'hours_analyzed': hours,
            'total_trending': len(trending_topics)
        }
        
    except Exception as e:
        logger.error(f"Error getting trending topics: {e}")
        raise HTTPException(status_code=500, detail="Internal error during trending topics analysis")

@router.post("/batch-analyze")
async def batch_analyze_texts(request: BatchAnalysisRequest):
    """Analyze sentiment for multiple texts"""
    try:
        if not request.texts:
            raise HTTPException(status_code=400, detail="No texts provided")
        
        results = sentiment_analyzer.batch_analyze(request.texts)
        
        # Calculate summary statistics
        sentiment_scores = [r['sentiment_score'] for r in results]
        labels = [r['sentiment_label'] for r in results]
        
        summary = {
            'total_texts': len(request.texts),
            'average_sentiment': np.mean(sentiment_scores),
            'sentiment_distribution': {
                'positive': labels.count('positive'),
                'negative': labels.count('negative'),
                'neutral': labels.count('neutral')
            }
        }
        
        return {
            'summary': summary,
            'results': results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal error during batch sentiment analysis")

@router.get("/model-info")
async def get_model_info():
    """Get information about the sentiment analysis model"""
    try:
        model_info = {
            'neural_model_available': sentiment_analyzer.model is not None,
            'tokenizer_available': sentiment_analyzer.tokenizer is not None,
            'max_sequence_length': sentiment_analyzer.max_length,
            'confidence_threshold': sentiment_analyzer.confidence_threshold,
            'methods_available': ['neural', 'rule-based', 'blended'],
            'sentiment_keywords_count': {
                'positive': len(sentiment_analyzer.sentiment_keywords['positive']),
                'negative': len(sentiment_analyzer.sentiment_keywords['negative']),
                'neutral': len(sentiment_analyzer.sentiment_keywords['neutral'])
            }
        }
        
        if sentiment_analyzer.model:
            try:
                # Get model summary if available
                import io
                import contextlib
                
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    sentiment_analyzer.model.summary()
                model_summary = f.getvalue()
                model_info['model_summary'] = model_summary
            except Exception:
                model_info['model_summary'] = 'Model summary not available'
        
        return model_info
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail="Internal error getting model information") 