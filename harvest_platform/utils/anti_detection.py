import random
import time
from typing import Optional


class AntiDetection:
    """Anti-detection utilities for web scraping"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]
    
    @staticmethod
    def get_random_user_agent() -> str:
        """Get random user agent string"""
        return random.choice(AntiDetection.USER_AGENTS)
    
    @staticmethod
    def jitter_delay(base_delay: float = 3.0, min_delay: float = 2.0, 
                    max_delay: float = 7.0) -> float:
        """Add random jitter to delay"""
        jittered = base_delay + random.uniform(-1, 2)
        return max(min_delay, min(max_delay, jittered))
    
    @staticmethod
    def smart_sleep(base_delay: float = 3.0):
        """Sleep with jitter"""
        delay = AntiDetection.jitter_delay(base_delay)
        time.sleep(delay)
    
    @staticmethod
    def get_headers(referer: Optional[str] = None) -> dict:
        """Generate realistic request headers"""
        headers = {
            "User-Agent": AntiDetection.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }
        
        if referer:
            headers["Referer"] = referer
        
        return headers
