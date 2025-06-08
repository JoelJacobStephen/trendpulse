import schedule
import time
import threading
import logging
from datetime import datetime
from typing import Callable
import signal
import sys

import sys
import os
# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.news_processor import NewsProcessor
from etl.trend_calculator import TrendCalculator
from config import settings

logger = logging.getLogger(__name__)

class BackgroundScheduler:
    """Simple background task scheduler using the schedule library"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.news_processor = NewsProcessor()
        self.trend_calculator = TrendCalculator()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down scheduler...")
        self.stop()
        sys.exit(0)
    
    def setup_jobs(self):
        """Setup all scheduled jobs"""
        logger.info("Setting up scheduled jobs...")
        
        # News fetching - every hour
        schedule.every().hour.do(self._safe_execute, self.fetch_news_job, "news_fetch")
        
        # Trend calculation - every 6 hours
        schedule.every(6).hours.do(self._safe_execute, self.calculate_trends_job, "trend_calculation")
        
        # Daily cleanup - every day at 2 AM
        schedule.every().day.at("02:00").do(self._safe_execute, self.cleanup_job, "daily_cleanup")
        
        # Health check - every 30 minutes
        schedule.every(30).minutes.do(self._safe_execute, self.health_check_job, "health_check")
        
        logger.info("Scheduled jobs configured successfully")
    
    def _safe_execute(self, job_func: Callable, job_name: str):
        """Safely execute a job with error handling"""
        try:
            logger.info(f"Starting job: {job_name}")
            start_time = datetime.now()
            
            result = job_func()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Job {job_name} completed successfully in {duration:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Job {job_name} failed: {e}", exc_info=True)
            return None
    
    def fetch_news_job(self):
        """Job to fetch and process news"""
        logger.info("Executing news fetch job...")
        
        try:
            # Fetch news from all sources
            article_count = self.news_processor.fetch_and_process_all()
            
            logger.info(f"News fetch job completed: {article_count} articles processed")
            return {"articles_processed": article_count, "status": "success"}
            
        except Exception as e:
            logger.error(f"News fetch job failed: {e}")
            raise
    
    def calculate_trends_job(self):
        """Job to calculate topic trends"""
        logger.info("Executing trend calculation job...")
        
        try:
            # Calculate trends for all topics and countries
            trend_count = self.trend_calculator.calculate_all_trends()
            
            logger.info(f"Trend calculation job completed: {trend_count} trends calculated")
            return {"trends_calculated": trend_count, "status": "success"}
            
        except Exception as e:
            logger.error(f"Trend calculation job failed: {e}")
            raise
    
    def cleanup_job(self):
        """Job to clean up old data"""
        logger.info("Executing cleanup job...")
        
        try:
            # Import here to avoid circular imports
            from config import settings
            
            # Clean up old articles (configurable retention period)
            cleaned_articles = self.news_processor.cleanup_old_articles(days=settings.ARTICLE_RETENTION_DAYS)
            
            # Clean up old trends (configurable retention period)
            cleaned_trends = self.trend_calculator.cleanup_old_trends(days=settings.TREND_RETENTION_DAYS)
            
            logger.info(f"Cleanup job completed: {cleaned_articles} articles, {cleaned_trends} trends removed")
            return {
                "articles_cleaned": cleaned_articles,
                "trends_cleaned": cleaned_trends,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Cleanup job failed: {e}")
            raise
    
    def health_check_job(self):
        """Job to perform health checks"""
        logger.debug("Executing health check job...")
        
        try:
            # Check database connectivity
            db_status = self.news_processor.check_database_health()
            
            # Check external API availability
            api_status = self.news_processor.check_api_health()
            
            # Log status
            if db_status and api_status:
                logger.debug("Health check passed")
            else:
                logger.warning(f"Health check issues: DB={db_status}, APIs={api_status}")
            
            return {
                "database": db_status,
                "apis": api_status,
                "status": "healthy" if db_status and api_status else "degraded"
            }
            
        except Exception as e:
            logger.error(f"Health check job failed: {e}")
            raise
    
    def run_scheduler(self):
        """Main scheduler loop"""
        logger.info("Starting background scheduler...")
        self.running = True
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def start(self):
        """Start the scheduler in a background thread"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        # Setup jobs
        self.setup_jobs()
        
        # Start in background thread
        self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("Background scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        logger.info("Stopping background scheduler...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
        
        logger.info("Background scheduler stopped")
    
    def run_job_now(self, job_name: str):
        """Run a specific job immediately"""
        job_map = {
            "fetch_news": self.fetch_news_job,
            "calculate_trends": self.calculate_trends_job,
            "cleanup": self.cleanup_job,
            "health_check": self.health_check_job
        }
        
        if job_name not in job_map:
            raise ValueError(f"Unknown job: {job_name}")
        
        logger.info(f"Running job {job_name} immediately...")
        return self._safe_execute(job_map[job_name], job_name)
    
    def get_job_status(self):
        """Get status of all scheduled jobs"""
        jobs = []
        for job in schedule.jobs:
            jobs.append({
                "job": str(job.job_func),
                "next_run": job.next_run.isoformat() if job.next_run else None,
                "interval": str(job.interval),
                "unit": job.unit
            })
        
        return {
            "scheduler_running": self.running,
            "scheduled_jobs": jobs,
            "total_jobs": len(jobs)
        }

# Global scheduler instance
scheduler = BackgroundScheduler()

def start_scheduler():
    """Start the global scheduler"""
    scheduler.start()

def stop_scheduler():
    """Stop the global scheduler"""
    scheduler.stop()

def run_job_immediately(job_name: str):
    """Run a job immediately"""
    return scheduler.run_job_now(job_name)

if __name__ == "__main__":
    # For testing - run scheduler directly
    logging.basicConfig(level=logging.INFO)
    
    try:
        scheduler.start()
        print("Scheduler started. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        scheduler.stop() 