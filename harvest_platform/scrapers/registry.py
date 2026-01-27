from typing import Generator, Dict, Optional
from core.base_scraper import BaseScraper
from bs4 import BeautifulSoup


class ExampleDirectScraper(BaseScraper):
    """Example scraper for 'direct' pagination type"""
    
    SOURCE_TYPE = "example_direct"
    
    def scrape(self) -> Generator[Dict, None, None]:
        """Scrape leads from a direct listing page"""
        response = self._make_request(self.base_url)
        
        if not response:
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        listings = soup.select(self.selectors.get('listing_container', '.listing'))
        
        for listing in listings:
            lead = self.parse_lead(listing)
            if lead:
                yield lead
    
    def parse_lead(self, element) -> Optional[Dict]:
        """Parse individual lead"""
        try:
            lead = {
                'business_name': self._extract_text(element, self.selectors.get('business_name')),
                'phone': self._extract_text(element, self.selectors.get('phone')),
                'email': self._extract_text(element, self.selectors.get('email')),
                'website': self._extract_attr(element, self.selectors.get('website'), 'href'),
                'address': self._extract_text(element, self.selectors.get('address')),
                'city': self._extract_text(element, self.selectors.get('city')),
                'state': self._extract_text(element, self.selectors.get('state')),
                'category': self._extract_text(element, self.selectors.get('category')),
            }
            
            return lead
        
        except Exception as e:
            self.logger.warning(f"Failed to parse lead: {e}")
            return None
    
    def _extract_text(self, element, selector: Optional[str]) -> Optional[str]:
        """Extract text from element"""
        if not selector:
            return None
        
        try:
            found = element.select_one(selector)
            return found.get_text(strip=True) if found else None
        except:
            return None
    
    def _extract_attr(self, element, selector: Optional[str], 
                     attr: str = 'href') -> Optional[str]:
        """Extract attribute from element"""
        if not selector:
            return None
        
        try:
            found = element.select_one(selector)
            return found.get(attr) if found else None
        except:
            return None
