#!/usr/bin/env python3
"""
Script to process existing articles with sentiment analysis
"""
import sys
import os
import logging
from datetime import datetime
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import Article
from sentiment_analyzer import sentiment_analyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_articles_sentiment(batch_size: int = 50, limit: int = None):
    """Process existing articles with sentiment analysis"""
    db = SessionLocal()
    
    try:
        logger.info("Starting sentiment analysis for existing articles...")
        
        # Get articles without sentiment scores
        query = db.query(Article).filter(Article.sentiment_score.is_(None))
        
        if limit:
            query = query.limit(limit)
        
        total_articles = query.count()
        logger.info(f"Found {total_articles} articles without sentiment scores")
        
        if total_articles == 0:
            logger.info("No articles need sentiment processing")
            return 0
        
        processed_count = 0
        failed_count = 0
        
        # Process articles in batches
        offset = 0
        while offset < total_articles:
            batch = query.offset(offset).limit(batch_size).all()
            
            if not batch:
                break
            
            logger.info(f"Processing batch {offset//batch_size + 1} ({len(batch)} articles)")
            
            for article in batch:
                try:
                    # Analyze sentiment
                    sentiment_result = sentiment_analyzer.analyze_article(
                        article.title or '', 
                        article.content or ''
                    )
                    
                    if sentiment_result:
                        article.sentiment_score = sentiment_result.get('sentiment_score', 0.0)
                        
                        # Update keywords with sentiment metadata
                        sentiment_meta = {
                            'sentiment_method': sentiment_result.get('method', 'unknown'),
                            'sentiment_confidence': sentiment_result.get('confidence', 0.0),
                            'sentiment_label': sentiment_result.get('sentiment_label', 'neutral')
                        }
                        
                        if article.keywords:
                            if isinstance(article.keywords, dict):
                                article.keywords.update(sentiment_meta)
                            else:
                                article.keywords = sentiment_meta
                        else:
                            article.keywords = sentiment_meta
                        
                        processed_count += 1
                        
                        if processed_count % 10 == 0:
                            logger.info(f"Processed {processed_count}/{total_articles} articles")
                    
                    else:
                        # Set neutral sentiment if analysis fails
                        article.sentiment_score = 0.0
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing article {article.id}: {e}")
                    article.sentiment_score = 0.0
                    failed_count += 1
            
            # Commit batch
            db.commit()
            offset += batch_size
        
        logger.info(f"Sentiment processing completed!")
        logger.info(f"Successfully processed: {processed_count}")
        logger.info(f"Failed/neutral: {failed_count}")
        logger.info(f"Total: {processed_count + failed_count}")
        
        return processed_count
        
    except Exception as e:
        logger.error(f"Error in sentiment processing: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

def analyze_sentiment_distribution():
    """Analyze sentiment distribution of processed articles"""
    db = SessionLocal()
    
    try:
        logger.info("Analyzing sentiment distribution...")
        
        # Get all articles with sentiment scores
        articles = db.query(Article).filter(Article.sentiment_score.is_not(None)).all()
        
        if not articles:
            logger.warning("No articles with sentiment scores found")
            return
        
        # Calculate distribution
        positive_count = sum(1 for a in articles if a.sentiment_score > 0.1)
        negative_count = sum(1 for a in articles if a.sentiment_score < -0.1)
        neutral_count = sum(1 for a in articles if -0.1 <= a.sentiment_score <= 0.1)
        
        total = len(articles)
        
        logger.info(f"Sentiment Distribution ({total} articles):")
        logger.info(f"  Positive: {positive_count} ({positive_count/total*100:.1f}%)")
        logger.info(f"  Negative: {negative_count} ({negative_count/total*100:.1f}%)")
        logger.info(f"  Neutral:  {neutral_count} ({neutral_count/total*100:.1f}%)")
        
        # Average sentiment by topic
        from collections import defaultdict
        import statistics
        
        topic_sentiments = defaultdict(list)
        for article in articles:
            if article.primary_theme:
                topic_sentiments[article.primary_theme].append(article.sentiment_score)
        
        logger.info("\nAverage sentiment by topic:")
        for topic, scores in topic_sentiments.items():
            if scores:
                avg_sentiment = statistics.mean(scores)
                logger.info(f"  {topic}: {avg_sentiment:.3f} ({len(scores)} articles)")
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment distribution: {e}")
    finally:
        db.close()

def update_existing_articles_sentiment():
    """Update sentiment scores for articles that might have outdated scores"""
    db = SessionLocal()
    
    try:
        logger.info("Updating sentiment scores for existing articles...")
        
        # Get articles with very low confidence or no sentiment metadata
        articles = db.query(Article).filter(
            Article.sentiment_score.is_not(None)
        ).limit(100).all()  # Limit for testing
        
        updated_count = 0
        
        for article in articles:
            try:
                # Re-analyze sentiment
                sentiment_result = sentiment_analyzer.analyze_article(
                    article.title or '', 
                    article.content or ''
                )
                
                if sentiment_result and sentiment_result.get('confidence', 0) > 0.5:
                    old_score = article.sentiment_score
                    new_score = sentiment_result.get('sentiment_score', 0.0)
                    
                    # Only update if there's a significant difference
                    if abs(old_score - new_score) > 0.2:
                        article.sentiment_score = new_score
                        updated_count += 1
                        
                        logger.debug(f"Updated article {article.id}: {old_score:.3f} -> {new_score:.3f}")
                
            except Exception as e:
                logger.error(f"Error updating article {article.id}: {e}")
        
        db.commit()
        logger.info(f"Updated sentiment scores for {updated_count} articles")
        
    except Exception as e:
        logger.error(f"Error updating sentiment scores: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process articles with sentiment analysis")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    parser.add_argument("--limit", type=int, help="Limit number of articles to process")
    parser.add_argument("--analyze", action="store_true", help="Analyze sentiment distribution")
    parser.add_argument("--update", action="store_true", help="Update existing sentiment scores")
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_sentiment_distribution()
    elif args.update:
        update_existing_articles_sentiment()
    else:
        process_articles_sentiment(batch_size=args.batch_size, limit=args.limit) 