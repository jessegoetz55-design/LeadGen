from typing import Generator, Dict, Optional
from core.base_scraper import BaseScraper
from utils.advanced_anti_detection import AdvancedAntiDetection, ProxyManager
from bs4 import BeautifulSoup
import requests
import time
import random
import logging

logger = logging.getLogger(__name__)

class YellowPagesProScraper(BaseScraper):
    SOURCE_TYPE = "yellowpages_pro"
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.proxy_manager = ProxyManager()
        logger.info("Loading proxies...")
        self.proxy_manager.fetch_free_proxies()
        self.current_proxy = None
    
    def _make_request_with_rotation(self, url: str, attempt: int = 1):
        if attempt > 5:
            return None
        
        if not self.current_proxy or attempt > 1:
            self.current_proxy = self.proxy_manager.get_working_proxy()
            if not self.current_proxy:
                return None
        
        headers = AdvancedAntiDetection.get_realistic_headers()
        
        try:
            response = requests.get(url, headers=headers, proxies=self.current_proxy, timeout=30)
            
            if response.status_code == 403:
                self.proxy_manager.mark_proxy_failed(self.current_proxy)
                time.sleep(3)
                return self._make_request_with_rotation(url, attempt + 1)
            
            if response.status_code == 200:
                AdvancedAntiDetection.human_delay(3, 7)
                return response
            
            time.sleep(2)
            return self._make_request_with_rotation(url, attempt + 1)
            
        except:
            self.proxy_manager.mark_proxy_failed(self.current_proxy)
            time.sleep(2)
            return self._make_request_with_rotation(url, attempt + 1)
    
    def scrape(self) -> Generator[Dict, None, None]:
        for page in range(1, 6):
            url = self.base_url if page == 1 else f"{self.base_url}{'&' if '?' in self.base_url else '?'}page={page}"
            
            response = self._make_request_with_rotation(url)
            if not response:
                break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            listings = soup.select('.result, .search-results .result')
            
            if not listings:
                break
            
            for listing in listings:
                lead = self.parse_lead(listing)
                if lead:
                    yield lead
                time.sleep(random.uniform(0.3, 1.0))
            
            if page < 5:
                time.sleep(random.uniform(5, 10))
    
    def parse_lead(self, element) -> Optional[Dict]:
        try:
            name_elem = element.select_one('.business-name, h2.business-name, h2 a')
            if not name_elem:
                return None
            
            phone_elem = element.select_one('.phones, .phone')
            city_elem = element.select_one('.locality')
            state_elem = element.select_one('.region')
            
            return {
                'business_name': name_elem.get_text(strip=True),
                'phone': phone_elem.get_text(strip=True) if phone_elem else None,
                'city': city_elem.get_text(strip=True) if city_elem else None,
                'state': state_elem.get_text(strip=True) if state_elem else None,
                'category': 'Yellow Pages'
            }
        except:
            return None