from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Generator
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.anti_detection import AntiDetection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all scrapers"""
    
    def __init__(self, config: Dict):
        """Initialize scraper with configuration"""
        self.config = config
        self.source_id = config['id']
        self.name = config['name']
        self.base_url = config['base_url']
        self.selectors = config['selectors']
        self.rate_limit_delay = config.get('rate_limit_delay', 3.0)
        self.proxy_config = config.get('proxy_config')
        self.session = self._create_session()
        self.logger = logger
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _make_request(self, url: str, method: str = "GET", 
                     **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with anti-detection measures"""
        try:
            headers = AntiDetection.get_headers(referer=kwargs.pop('referer', None))
            headers.update(kwargs.pop('headers', {}))
            
            proxies = None
            if self.proxy_config:
                proxies = {
                    'http': self.proxy_config.get('http'),
                    'https': self.proxy_config.get('https')
                }
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                proxies=proxies,
                timeout=30,
                **kwargs
            )
            response.raise_for_status()
            
            AntiDetection.smart_sleep(self.rate_limit_delay)
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return None
    
    @abstractmethod
    def scrape(self) -> Generator[Dict, None, None]:
        """Main scraping logic - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def parse_lead(self, element) -> Optional[Dict]:
        """Parse individual lead from HTML element"""
        pass
    
    def validate_lead(self, lead: Dict) -> bool:
        """Validate lead data"""
        if not lead.get('business_name'):
            return False
        
        if not any([lead.get('phone'), lead.get('email'), lead.get('website')]):
            return False
        
        return True
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close()
