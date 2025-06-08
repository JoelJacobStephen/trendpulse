#!/usr/bin/env python3

import os
import sys
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def setup_environment():
    """Set up the environment for running the application"""
    # Load .env file first
    from dotenv import load_dotenv
    load_dotenv()
    
    # Set environment variables for development if not set
    env_vars = {
        'DATABASE_URL': 'postgresql://localhost:5432/trendpulse',
        'DEBUG': 'True',
        'SECRET_KEY': 'dev-secret-key-for-development-only',
        'CORS_ORIGINS': 'http://localhost:3000,http://localhost:8080',
        'NEWS_FETCH_INTERVAL': '3600',
        'TREND_CALCULATION_INTERVAL': '21600'
    }
    
    for key, default_value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = default_value
            logger.info(f"Set {key} to default value")
        else:
            logger.info(f"Using {key} from environment")

def check_dependencies():
    """Check if required dependencies are available"""
    # Map package names to their import names
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn', 
        'sqlalchemy': 'sqlalchemy',
        'psycopg2': 'psycopg2',
        'requests': 'requests',
        'beautifulsoup4': 'bs4',
        'feedparser': 'feedparser',
        'tensorflow': 'tensorflow',
        'transformers': 'transformers',
        'pandas': 'pandas',
        'numpy': 'numpy'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name.replace('-', '_'))
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.error("Please install them with: pip install -r requirements.txt")
        return False
    
    logger.info("All required dependencies are available")
    return True

def run_development_server():
    """Run the development server"""
    import uvicorn
    from main import app
    
    logger.info("Starting TrendPulse API in development mode...")
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

def run_background_scheduler():
    """Run only the background scheduler"""
    from etl.scheduler import start_scheduler
    import time
    
    logger.info("Starting background scheduler...")
    
    try:
        start_scheduler()
        logger.info("Background scheduler started. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        sys.exit(1)

def run_database_setup():
    """Set up and initialize the database"""
    from database import init_db
    from news_aggregator import news_aggregator
    
    logger.info("Setting up database...")
    
    try:
        # Initialize database tables
        init_db()
        logger.info("Database tables created successfully")
        
        # Initialize default news sources
        news_aggregator.initialize_sources()
        logger.info("Default news sources initialized")
        
        logger.info("Database setup completed successfully")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)

def run_news_fetch():
    """Run a one-time news fetch"""
    from news_aggregator import news_aggregator
    
    logger.info("Starting one-time news fetch...")
    
    try:
        count = news_aggregator.fetch_and_process_news()
        logger.info(f"News fetch completed: {count} articles processed")
        
    except Exception as e:
        logger.error(f"News fetch failed: {e}")
        sys.exit(1)

def run_database_reset():
    """Clear all data from the database and reinitialize"""
    from database import init_db, SessionLocal, engine
    from models import Base
    from news_aggregator import news_aggregator
    
    logger.info("Resetting database...")
    
    try:
        # Ask for confirmation
        response = input("This will delete ALL data in the database. Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Database reset cancelled")
            return
        
        logger.info("Dropping all tables...")
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully")
        
        logger.info("Recreating tables...")
        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables recreated successfully")
        
        # Initialize default news sources
        news_aggregator.initialize_sources()
        logger.info("Default news sources initialized")
        
        logger.info("Database reset completed successfully")
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        sys.exit(1)

def run_trend_calculation():
    """Run trend calculation for all topics and countries"""
    from etl.trend_calculator import TrendCalculator
    
    logger.info("Starting trend calculation...")
    
    try:
        calculator = TrendCalculator()
        count = calculator.calculate_all_trends()
        logger.info(f"Trend calculation completed: {count} trends calculated")
        
    except Exception as e:
        logger.error(f"Trend calculation failed: {e}")
        sys.exit(1)

def run_production_server():
    """Run the production server using gunicorn"""
    try:
        import subprocess
        
        logger.info("Starting TrendPulse API in production mode...")
        logger.info("Using Gunicorn with Uvicorn workers")
        
        # Production server configuration
        cmd = [
            "gunicorn",
            "-w", "4",  # 4 worker processes
            "-k", "uvicorn.workers.UvicornWorker",
            "--bind", "0.0.0.0:8000",
            "--access-logfile", "-",
            "--error-logfile", "-",
            "--log-level", "info",
            "main:app"
        ]
        
        subprocess.run(cmd, check=True)
        
    except ImportError:
        logger.error("Gunicorn is not installed. Install it with: pip install gunicorn")
        logger.info("Falling back to development server...")
        run_development_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Production server error: {e}")
        sys.exit(1)

def run_api_test():
    """Run a quick test of the API endpoints"""
    import requests
    import time
    
    logger.info("Running API test...")
    
    base_url = "http://localhost:8000"
    
    # Test endpoints
    test_endpoints = [
        "/",
        "/api",
        "/api/v1/health",
        "/docs"
    ]
    
    try:
        logger.info("Testing API endpoints...")
        
        for endpoint in test_endpoints:
            url = f"{base_url}{endpoint}"
            try:
                response = requests.get(url, timeout=5)
                status = "✓" if response.status_code == 200 else "✗"
                logger.info(f"{status} {endpoint} - Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"✗ {endpoint} - Error: {e}")
        
        logger.info("API test completed")
        
    except Exception as e:
        logger.error(f"API test failed: {e}")
        logger.error("Make sure the server is running with: python run.py server")
        sys.exit(1)

def run_historical_fetch():
    """Fetch historical news data for the past 30 days"""
    print("🔄 Starting historical news fetch...")
    
    try:
        from data_sources import NewsSourceManager
        from news_aggregator import news_aggregator
        from datetime import datetime, timedelta
        
        source_manager = NewsSourceManager()
        
        # Check if API keys are available
        has_newsapi = bool(source_manager.newsapi.client)
        has_guardian = bool(source_manager.guardian.api_key)
        
        if not has_newsapi and not has_guardian:
            print("❌ No API keys configured for historical fetching")
            print("   Add NEWS_API_KEY and/or GUARDIAN_API_KEY to your .env file")
            return
        
        print(f"📊 Available sources for historical data:")
        print(f"   NewsAPI: {'✅' if has_newsapi else '❌'}")
        print(f"   Guardian: {'✅' if has_guardian else '❌'}")
        
        # Fetch historical data for past 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Fetching articles from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        articles = source_manager.fetch_historical_news(
            from_date=start_date,
            to_date=end_date
        )
        
        if articles:
            print(f"📰 Fetched {len(articles)} historical articles")
            
            # Process and save articles using existing aggregator
            saved_count = news_aggregator._save_articles_to_db(articles)
            print(f"💾 Saved {saved_count} new articles to database")
            
            # Calculate trends after adding historical data
            print("📈 Calculating trends for historical data...")
            from etl.trend_calculator import TrendCalculator
            trend_calc = TrendCalculator()
            trend_count = trend_calc.calculate_all_trends()
            print(f"📊 Generated {trend_count} trend records")
            
        else:
            print("⚠️  No historical articles found")
            
        print("✅ Historical fetch completed successfully!")
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
    except Exception as e:
        print(f"❌ Error during historical fetch: {e}")
        import traceback
        traceback.print_exc()

def run_status():
    """Show database status and retention information"""
    print("📊 TrendPulse Database Status")
    
    try:
        from database import SessionLocal
        from models import Article, TopicTrend
        from datetime import datetime, timedelta
        from config import settings
        import collections
        
        db = SessionLocal()
        
        # Article statistics
        total_articles = db.query(Article).count()
        print(f"\n📰 Articles:")
        print(f"   Total articles: {total_articles}")
        
        if total_articles > 0:
            # Date range
            oldest_article = db.query(Article).order_by(Article.published_date).first()
            newest_article = db.query(Article).order_by(Article.published_date.desc()).first()
            
            print(f"   Date range: {oldest_article.published_date.strftime('%Y-%m-%d')} to {newest_article.published_date.strftime('%Y-%m-%d')}")
            
            # Retention analysis
            cutoff_date = datetime.now() - timedelta(days=settings.ARTICLE_RETENTION_DAYS)
            old_articles = db.query(Article).filter(Article.published_date < cutoff_date).count()
            recent_articles = total_articles - old_articles
            
            print(f"   Within retention period ({settings.ARTICLE_RETENTION_DAYS} days): {recent_articles}")
            print(f"   Will be deleted in next cleanup: {old_articles}")
            
            # Daily breakdown (last 7 days)
            print(f"\n📅 Recent activity (last 7 days):")
            for i in range(7):
                date = datetime.now().date() - timedelta(days=i)
                count = db.query(Article).filter(
                    Article.published_date >= datetime.combine(date, datetime.min.time()),
                    Article.published_date < datetime.combine(date + timedelta(days=1), datetime.min.time())
                ).count()
                print(f"   {date}: {count} articles")
        
        # Trend statistics
        total_trends = db.query(TopicTrend).count()
        print(f"\n📈 Trends:")
        print(f"   Total trends: {total_trends}")
        
        if total_trends > 0:
            trend_cutoff_date = datetime.now() - timedelta(days=settings.TREND_RETENTION_DAYS)
            old_trends = db.query(TopicTrend).filter(TopicTrend.date < trend_cutoff_date).count()
            recent_trends = total_trends - old_trends
            
            print(f"   Within retention period ({settings.TREND_RETENTION_DAYS} days): {recent_trends}")
            print(f"   Will be deleted in next cleanup: {old_trends}")
        
        # Cleanup schedule
        print(f"\n🧹 Automatic Cleanup:")
        print(f"   Runs daily at 2:00 AM")
        print(f"   Article retention: {settings.ARTICLE_RETENTION_DAYS} days")
        print(f"   Trend retention: {settings.TREND_RETENTION_DAYS} days")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error getting status: {e}")

def run_cleanup():
    """Run cleanup manually"""
    print("🧹 Running manual cleanup...")
    
    try:
        from etl.news_processor import NewsProcessor
        from etl.trend_calculator import TrendCalculator
        from config import settings
        
        processor = NewsProcessor()
        calculator = TrendCalculator()
        
        print(f"Cleaning up articles older than {settings.ARTICLE_RETENTION_DAYS} days...")
        deleted_articles = processor.cleanup_old_articles(days=settings.ARTICLE_RETENTION_DAYS)
        
        print(f"Cleaning up trends older than {settings.TREND_RETENTION_DAYS} days...")
        deleted_trends = calculator.cleanup_old_trends(days=settings.TREND_RETENTION_DAYS)
        
        print(f"✅ Cleanup completed:")
        print(f"   Deleted {deleted_articles} articles")
        print(f"   Deleted {deleted_trends} trends")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

def show_help():
    """Show available commands"""
    commands = {
        "server (default)": "Start the development server",
        "prod": "Start production server with gunicorn",
        "setup": "Initialize database and create tables",
        "fetch": "Fetch news from all sources once",
        "trend": "Calculate trends once",
        "scheduler": "Run background scheduler for automated tasks",
        "historical": "Fetch historical articles (last 30 days)",
        "status": "Show database status and retention info",
        "cleanup": "Run cleanup manually (delete old articles/trends)",
        "reset": "Reset database (delete all data)",
        "test": "Test API endpoints",
        "help": "Show this help message"
    }
    
    print("🚀 TrendPulse Backend - Available Commands")
    print("=" * 50)
    for cmd, desc in commands.items():
        print(f"  python run.py {cmd:<12} - {desc}")
    print()
    print("💡 Environment variables (create .env file):")
    print("  DATABASE_URL, NEWS_API_KEY, GUARDIAN_API_KEY")
    print("  ARTICLE_RETENTION_DAYS, TREND_RETENTION_DAYS")

def main():
    """Main entry point"""
    # Setup environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        command = "server"  # Default to server
    else:
        command = sys.argv[1].lower()
    
    # Route to appropriate function
    if command == "server":
        run_development_server()
    elif command == "scheduler":
        run_background_scheduler()
    elif command == "setup":
        run_database_setup()
    elif command == "fetch":
        run_news_fetch()
    elif command == "reset":
        run_database_reset()
    elif command == "trend":
        run_trend_calculation()
    elif command == "prod":
        run_production_server()
    elif command == "test":
        run_api_test()
    elif command == "historical":
        run_historical_fetch()
    elif command == "status":
        run_status()
    elif command == "cleanup":
        run_cleanup()
    elif command == "help":
        show_help()
    else:
        logger.error(f"Unknown command: {command}")
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 