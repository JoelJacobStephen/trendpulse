#!/usr/bin/env python3

import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Article, TopicTrend

def generate_trends_from_articles():
    """Generate trend data from existing articles"""
    db = SessionLocal()
    
    try:
        print("Generating trends from articles...")
        
        # Get all articles
        articles = db.query(Article).all()
        print(f"Found {len(articles)} articles")
        
        if not articles:
            print("No articles found!")
            return
        
        # Group articles by country and topic
        country_topic_counts = defaultdict(lambda: defaultdict(int))
        country_topic_articles = defaultdict(lambda: defaultdict(list))
        
        for article in articles:
            if article.country and article.primary_theme:
                country_topic_counts[article.country][article.primary_theme] += 1
                country_topic_articles[article.country][article.primary_theme].append(article)
        
        print(f"Found data for {len(country_topic_counts)} countries")
        
        # Create trend entries
        trends_created = 0
        today = datetime.now().date()
        
        for country, topics in country_topic_counts.items():
            for topic, count in topics.items():
                # Calculate a simple trend score based on article count
                # More articles = higher trend score
                trend_score = min(count / 10.0, 1.0)  # Normalize to 0-1
                
                # Check if trend already exists
                existing = db.query(TopicTrend).filter(
                    TopicTrend.theme == topic,
                    TopicTrend.country == country,
                    TopicTrend.date == today
                ).first()
                
                if not existing:
                    # Calculate average sentiment if available
                    articles_with_sentiment = [a for a in country_topic_articles[country][topic] if a.sentiment_score is not None]
                    avg_sentiment = None
                    if articles_with_sentiment:
                        avg_sentiment = sum(a.sentiment_score for a in articles_with_sentiment) / len(articles_with_sentiment)
                    
                    trend = TopicTrend(
                        theme=topic,
                        country=country,
                        date=today,
                        article_count=count,
                        trend_score=trend_score,
                        sentiment_avg=avg_sentiment,
                        engagement_score=trend_score * 0.8  # Simple engagement calculation
                    )
                    
                    db.add(trend)
                    trends_created += 1
                    print(f"Created trend: {topic} in {country} - {count} articles, score: {trend_score:.2f}")
        
        db.commit()
        print(f"Successfully created {trends_created} trend entries")
        
        # Verify the data
        total_trends = db.query(TopicTrend).count()
        print(f"Total trends in database: {total_trends}")
        
    except Exception as e:
        print(f"Error generating trends: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_trends_from_articles() 