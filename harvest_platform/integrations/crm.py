"""CRM integration modules (HubSpot, Salesforce, etc.)"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
import requests
import logging

logger = logging.getLogger(__name__)


class BaseCRM(ABC):
    """Abstract base class for CRM integrations"""
    
    @abstractmethod
    def create_contact(self, lead: Dict) -> Optional[str]:
        """Create contact in CRM, return CRM ID"""
        pass
    
    @abstractmethod
    def update_contact(self, crm_id: str, lead: Dict) -> bool:
        """Update existing contact"""
        pass


class HubSpotCRM(BaseCRM):
    """HubSpot CRM integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.hubapi.com"
    
    def create_contact(self, lead: Dict) -> Optional[str]:
        """Create contact in HubSpot"""
        url = f"{self.base_url}/crm/v3/objects/contacts"
        
        properties = {
            "email": lead.get('email'),
            "phone": lead.get('phone'),
            "website": lead.get('website'),
            "address": lead.get('address'),
            "city": lead.get('city'),
            "state": lead.get('state'),
            "company": lead.get('business_name')
        }
        
        properties = {k: v for k, v in properties.items() if v}
        
        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={"properties": properties},
                timeout=15
            )
            
            if response.status_code == 201:
                return response.json().get('id')
            else:
                logger.error(f"HubSpot creation failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"HubSpot API error: {e}")
            return None
    
    def update_contact(self, crm_id: str, lead: Dict) -> bool:
        """Update contact in HubSpot"""
        # Implementation here
        pass
