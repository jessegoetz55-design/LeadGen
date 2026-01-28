import random
import time
import requests
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.failed_proxies = set()
    
    def fetch_free_proxies(self):
        sources = [
            'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all',
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        ]
        
        all_proxies = set()
        for source in sources:
            try:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    proxies = response.text.strip().split('\n')
                    for proxy in proxies:
                        proxy = proxy.strip()
                        if proxy and ':' in proxy:
                            all_proxies.add(proxy)
            except:
                pass
        
        self.proxies = list(all_proxies)
        logger.info(f"Loaded {len(self.proxies)} proxies")
        return len(self.proxies)
    
    def test_proxy(self, proxy: str) -> bool:
        try:
            proxy_dict = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
            response = requests.get('http://httpbin.org/ip', proxies=proxy_dict, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_working_proxy(self) -> Optional[Dict]:
        if self.working_proxies:
            proxy = random.choice(self.working_proxies)
            return {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        
        if not self.proxies:
            self.fetch_free_proxies()
        
        tested = 0
        while tested < 10 and self.proxies:
            proxy = self.proxies.pop(0)
            if proxy not in self.failed_proxies:
                if self.test_proxy(proxy):
                    self.working_proxies.append(proxy)
                    return {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
                self.failed_proxies.add(proxy)
            tested += 1
        return None
    
    def mark_proxy_failed(self, proxy_dict: Dict):
        if proxy_dict and 'http' in proxy_dict:
            proxy = proxy_dict['http'].replace('http://', '')
            if proxy in self.working_proxies:
                self.working_proxies.remove(proxy)
            self.failed_proxies.add(proxy)

class AdvancedAntiDetection:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    ]
    
    @staticmethod
    def get_random_user_agent():
        return random.choice(AdvancedAntiDetection.USER_AGENTS)
    
    @staticmethod
    def human_delay(min_sec=2.0, max_sec=8.0):
        time.sleep(random.uniform(min_sec, max_sec))
    
    @staticmethod
    def get_realistic_headers(referer=None):
        headers = {
            "User-Agent": AdvancedAntiDetection.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
        }
        if referer:
            headers["Referer"] = referer
        return headers