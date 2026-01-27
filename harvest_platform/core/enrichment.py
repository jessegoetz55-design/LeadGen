import requests
from typing import Dict, Optional, List
import re
import logging

logger = logging.getLogger(__name__)


class LeadEnricher:
    """Enrich leads with additional data"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.clearbit_key = self.config.get('clearbit_api_key')
        self.hunter_key = self.config.get('hunter_api_key')
    
    def enrich_lead(self, lead: Dict) -> Dict:
        """Enrich a single lead"""
        enriched = lead.copy()
        
        if lead.get('phone'):
            enriched['phone_formatted'] = self.format_phone(lead['phone'])
            enriched['phone_valid'] = self.validate_phone(lead['phone'])
        
        if lead.get('email'):
            enriched['email_valid'] = self.validate_email(lead['email'])
        
        if lead.get('website'):
            enriched['domain'] = self.extract_domain(lead['website'])
            
            if self.clearbit_key:
                company_data = self.get_clearbit_data(enriched['domain'])
                if company_data:
                    if 'metadata' not in enriched:
                        enriched['metadata'] = {}
                    enriched['metadata']['enrichment'] = company_data
        
        if not lead.get('email') and self.hunter_key and enriched.get('domain'):
            found_emails = self.find_emails(enriched['domain'])
            if found_emails:
                enriched['email'] = found_emails[0]
                if 'metadata' not in enriched:
                    enriched['metadata'] = {}
                enriched['metadata']['email_source'] = 'hunter.io'
        
        return enriched
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """Format phone number to E.164"""
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+{digits}"
        
        return phone
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Basic phone validation"""
        digits = re.sub(r'\D', '', phone)
        return len(digits) >= 10
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain from URL"""
        domain = re.sub(r'https?://', '', url)
        domain = re.sub(r'^www\.', '', domain)
        domain = domain.split('/')[0]
        return domain
    
    def get_clearbit_data(self, domain: str) -> Optional[Dict]:
        """Get company data from Clearbit API"""
        if not self.clearbit_key:
            return None
        
        try:
            response = requests.get(
                f"https://company.clearbit.com/v2/companies/find",
                params={'domain': domain},
                headers={'Authorization': f'Bearer {self.clearbit_key}'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'name': data.get('name'),
                    'description': data.get('description'),
                    'employees': data.get('metrics', {}).get('employees'),
                    'industry': data.get('category', {}).get('industry'),
                    'linkedin': data.get('linkedin', {}).get('handle'),
                    'twitter': data.get('twitter', {}).get('handle')
                }
        except Exception as e:
            logger.warning(f"Clearbit enrichment failed for {domain}: {e}")
        
        return None
    
    def find_emails(self, domain: str) -> List[str]:
        """Find email addresses using Hunter.io"""
        if not self.hunter_key:
            return []
        
        try:
            response = requests.get(
                "https://api.hunter.io/v2/domain-search",
                params={'domain': domain, 'api_key': self.hunter_key},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                emails = [
                    email['value'] 
                    for email in data.get('data', {}).get('emails', [])
                    if email.get('type') == 'generic'
                ]
                return emails[:3]
        except Exception as e:
            logger.warning(f"Hunter.io search failed for {domain}: {e}")
        
        return []
