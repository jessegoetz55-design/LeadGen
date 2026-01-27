from typing import Dict
from datetime import datetime, timedelta


class LeadScorer:
    """Score leads based on quality indicators"""
    
    WEIGHTS = {
        'has_phone': 25,
        'has_email': 20,
        'has_website': 15,
        'has_address': 10,
        'email_valid': 10,
        'phone_valid': 10,
        'has_social': 5,
        'freshness': 5
    }
    
    @classmethod
    def score_lead(cls, lead: Dict) -> int:
        """Calculate quality score (0-100)"""
        score = 0
        
        if lead.get('phone'):
            score += cls.WEIGHTS['has_phone']
            if lead.get('phone_valid'):
                score += cls.WEIGHTS['phone_valid']
        
        if lead.get('email'):
            score += cls.WEIGHTS['has_email']
            if lead.get('email_valid'):
                score += cls.WEIGHTS['email_valid']
        
        if lead.get('website'):
            score += cls.WEIGHTS['has_website']
        
        if lead.get('address'):
            score += cls.WEIGHTS['has_address']
        
        metadata = lead.get('metadata', {})
        if any(k in metadata for k in ['linkedin', 'facebook', 'instagram']):
            score += cls.WEIGHTS['has_social']
        
        if lead.get('scraped_at'):
            try:
                scraped_date = lead['scraped_at']
                if isinstance(scraped_date, str):
                    scraped_date = datetime.fromisoformat(scraped_date.replace('Z', '+00:00'))
                
                if datetime.now() - scraped_date < timedelta(days=7):
                    score += cls.WEIGHTS['freshness']
            except:
                pass
        
        return min(score, 100)
    
    @classmethod
    def classify_lead(cls, score: int) -> str:
        """Classify lead quality based on score"""
        if score >= 80:
            return "Hot"
        elif score >= 60:
            return "Warm"
        elif score >= 40:
            return "Cold"
        else:
            return "Poor"
