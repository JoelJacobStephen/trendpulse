#!/usr/bin/env python3

import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Article, TopicTrend

def test_database():
    """Test what data we have in the database"""
    db = SessionLocal()
    
    try:
        # Check articles
        articles = db.query(Article).all()
        print(f"📰 Found {len(articles)} articles in database")
        
        if articles:
            # Show sample articles
            print("\n🔍 Sample articles:")
            for i, article in enumerate(articles[:3]):
                print(f"  {i+1}. {article.title[:60]}...")
                print(f"     Country: {article.country}, Topic: {article.primary_theme}")
            
            # Count by country
            country_counts = defaultdict(int)
            topic_counts = defaultdict(int)
            
            for article in articles:
                if article.country:
                    country_counts[article.country] += 1
                if article.primary_theme:
                    topic_counts[article.primary_theme] += 1
            
            print(f"\n🌍 Countries with articles:")
            for country, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {country}: {count} articles")
            
            print(f"\n📊 Topics with articles:")
            for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {topic}: {count} articles")
        
        # Check trends
        trends = db.query(TopicTrend).all()
        print(f"\n📈 Found {len(trends)} trends in database")
        
        if trends:
            print("\n🔍 Sample trends:")
            for i, trend in enumerate(trends[:3]):
                print(f"  {i+1}. {trend.theme} in {trend.country}")
                print(f"     Articles: {trend.article_count}, Score: {trend.trend_score:.2f}")
        
        return len(articles), len(trends)
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return 0, 0
    finally:
        db.close()

def generate_simple_trends():
    """Generate simple trend data from articles"""
    db = SessionLocal()
    
    try:
        print("\n🔄 Generating trends from articles...")
        
        # Get all articles
        articles = db.query(Article).all()
        
        if not articles:
            print("❌ No articles found!")
            return 0
        
        # Group by country and topic
        country_topic_data = defaultdict(lambda: defaultdict(list))
        
        for article in articles:
            if article.country and article.primary_theme:
                country_topic_data[article.country][article.primary_theme].append(article)
        
        trends_created = 0
        today = datetime.now().date()
        
        for country, topics in country_topic_data.items():
            for topic, topic_articles in topics.items():
                # Check if trend already exists
                existing = db.query(TopicTrend).filter(
                    TopicTrend.theme == topic,
                    TopicTrend.country == country,
                    TopicTrend.date == today
                ).first()
                
                if not existing:
                    article_count = len(topic_articles)
                    trend_score = min(article_count / 10.0, 1.0)  # Normalize to 0-1
                    
                    # Calculate average sentiment
                    sentiments = [a.sentiment_score for a in topic_articles if a.sentiment_score is not None]
                    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else None
                    
                    trend = TopicTrend(
                        theme=topic,
                        country=country,
                        date=today,
                        article_count=article_count,
                        trend_score=trend_score,
                        sentiment_avg=avg_sentiment,
                        engagement_score=trend_score * 0.8
                    )
                    
                    db.add(trend)
                    trends_created += 1
                    print(f"  ✅ Created: {topic} in {country} ({article_count} articles, score: {trend_score:.2f})")
        
        db.commit()
        print(f"\n🎉 Successfully created {trends_created} trends!")
        return trends_created
        
    except Exception as e:
        print(f"❌ Error generating trends: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 Testing TrendPulse Database\n")
    
    article_count, trend_count = test_database()
    
    if article_count > 0 and trend_count == 0:
        print("\n💡 No trends found but articles exist. Generating trends...")
        generated = generate_simple_trends()
        
        if generated > 0:
            print(f"\n✅ Generated {generated} trends. Testing again...")
            test_database()
    
    print("\n�� Test complete!") 