import threading
import schedule
import time
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class HarvestScheduler:
    """Advanced scheduler for automated scraping campaigns"""
    
    def __init__(self, engine):
        self.engine = engine
        self.scheduler = schedule.Scheduler()
        self.running = False
        self.thread = None
        self.jobs = {}
        
    def add_daily_job(self, source_id: int, time_str: str, 
                     max_leads: Optional[int] = None) -> str:
        """Schedule daily scraping at specific time"""
        job_id = f"daily_{source_id}_{time_str.replace(':', '')}"
        
        job = self.scheduler.every().day.at(time_str).do(
            self._run_with_error_handling,
            source_id=source_id,
            max_leads=max_leads,
            job_id=job_id
        )
        
        self.jobs[job_id] = {
            'job': job,
            'source_id': source_id,
            'schedule': f'Daily at {time_str}',
            'created_at': datetime.now()
        }
        
        logger.info(f"Scheduled daily job: {job_id}")
        return job_id
    
    def add_interval_job(self, source_id: int, hours: int, 
                        max_leads: Optional[int] = None) -> str:
        """Schedule scraping every N hours"""
        job_id = f"interval_{source_id}_{hours}h"
        
        job = self.scheduler.every(hours).hours.do(
            self._run_with_error_handling,
            source_id=source_id,
            max_leads=max_leads,
            job_id=job_id
        )
        
        self.jobs[job_id] = {
            'job': job,
            'source_id': source_id,
            'schedule': f'Every {hours} hours',
            'created_at': datetime.now()
        }
        
        logger.info(f"Scheduled interval job: {job_id}")
        return job_id
    
    def add_weekly_job(self, source_id: int, day: str, time_str: str,
                      max_leads: Optional[int] = None) -> str:
        """Schedule weekly scraping"""
        job_id = f"weekly_{source_id}_{day}_{time_str.replace(':', '')}"
        
        day_scheduler = getattr(self.scheduler.every(), day.lower())
        job = day_scheduler.at(time_str).do(
            self._run_with_error_handling,
            source_id=source_id,
            max_leads=max_leads,
            job_id=job_id
        )
        
        self.jobs[job_id] = {
            'job': job,
            'source_id': source_id,
            'schedule': f'{day.capitalize()} at {time_str}',
            'created_at': datetime.now()
        }
        
        return job_id
    
    def _run_with_error_handling(self, source_id: int, max_leads: Optional[int], job_id: str):
        """Wrapper with error handling"""
        try:
            logger.info(f"Starting scheduled job: {job_id}")
            result = self.engine.run_scraper(source_id, max_leads=max_leads)
            
            if result['success']:
                logger.info(f"Job {job_id} completed: {result['leads_saved']} leads saved")
            else:
                logger.error(f"Job {job_id} failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Job {job_id} crashed: {str(e)}")
    
    def remove_job(self, job_id: str):
        """Cancel a scheduled job"""
        if job_id in self.jobs:
            self.scheduler.cancel_job(self.jobs[job_id]['job'])
            del self.jobs[job_id]
            logger.info(f"Cancelled job: {job_id}")
    
    def start(self):
        """Start scheduler in background thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Scheduler started")
    
    def _run_loop(self):
        """Main scheduler loop"""
        while self.running:
            self.scheduler.run_pending()
            time.sleep(1)
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def get_jobs(self) -> Dict:
        """Get all scheduled jobs"""
        return {
            job_id: {
                **job_info,
                'next_run': job_info['job'].next_run.isoformat() if job_info['job'].next_run else None
            }
            for job_id, job_info in self.jobs.items()
        }
