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

def show_help():
    """Show help information"""
    help_text = """
TrendPulse Backend - Single Entry Point

Commands:
  python run.py                - Start the FastAPI development server (default)
  python run.py server         - Start the FastAPI development server
  python run.py prod           - Start the production server (gunicorn)
  python run.py scheduler      - Start only the background scheduler
  python run.py setup          - Set up and initialize the database
  python run.py fetch          - Run a one-time news fetch
  python run.py reset          - Clear all data and reset the database
  python run.py trend          - Run trend calculation for all topics and countries
  python run.py test           - Run a quick API test
  python run.py help           - Show this help message

Environment Setup:
  1. Install dependencies: pip install -r requirements.txt
  2. Set up PostgreSQL database
  3. Configure environment variables (see .env.example)
  4. Run: python run.py setup
  5. Run: python run.py server

For production deployment:
  - Use: python run.py prod
  - Or manually: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000

This is the ONLY script you need to run the backend. All other functionality is accessible through this script.
    """
    print(help_text)

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
    elif command == "help":
        show_help()
    else:
        logger.error(f"Unknown command: {command}")
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 