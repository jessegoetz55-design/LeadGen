import logging
from typing import Dict, List, Optional, Type
from datetime import datetime
import importlib
import inspect

from core.db import DatabaseManager
from core.base_scraper import BaseScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HarvestEngine:
    """Core orchestration engine for lead generation"""
    
    def __init__(self, db_path: str = "harvest.db"):
        """Initialize the Harvest engine"""
        self.db = DatabaseManager(db_path)
        self.scraper_registry: Dict[str, Type[BaseScraper]] = {}
        self._discover_scrapers()
    
    def _discover_scrapers(self):
        """Dynamically discover and register all scraper classes"""
        try:
            scrapers_module = importlib.import_module('scrapers')
            
            if hasattr(scrapers_module, '__path__'):
                import pkgutil
                for importer, modname, ispkg in pkgutil.iter_modules(scrapers_module.__path__):
                    try:
                        module = importlib.import_module(f'scrapers.{modname}')
                        
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if (issubclass(obj, BaseScraper) and 
                                obj is not BaseScraper and
                                hasattr(obj, 'SOURCE_TYPE')):
                                
                                self.scraper_registry[obj.SOURCE_TYPE] = obj
                                logger.info(f"Registered scraper: {obj.SOURCE_TYPE} -> {name}")
                    
                    except Exception as e:
                        logger.warning(f"Failed to load scraper module {modname}: {e}")
        
        except ImportError:
            logger.warning("Scrapers module not found - no scrapers registered")
    
    def register_scraper(self, source_type: str, scraper_class: Type[BaseScraper]):
        """Manually register a scraper class"""
        if not issubclass(scraper_class, BaseScraper):
            raise ValueError(f"{scraper_class} must inherit from BaseScraper")
        
        self.scraper_registry[source_type] = scraper_class
        logger.info(f"Manually registered scraper: {source_type}")
    
    def get_scraper(self, config: Dict) -> Optional[BaseScraper]:
        """Instantiate scraper based on source configuration"""
        source_type = config.get('source_type')
        
        if source_type not in self.scraper_registry:
            logger.error(f"No scraper registered for type: {source_type}")
            return None
        
        try:
            scraper_class = self.scraper_registry[source_type]
            return scraper_class(config)
        except Exception as e:
            logger.error(f"Failed to instantiate scraper {source_type}: {e}")
            return None
    
    def run_scraper(self, source_id: int, max_leads: Optional[int] = None) -> Dict:
        """Execute scraping for a specific source"""
        sources = self.db.load_sources(enabled_only=False)
        source_config = next((s for s in sources if s['id'] == source_id), None)
        
        if not source_config:
            return {'success': False, 'error': 'Source not found'}
        
        if not source_config['enabled']:
            return {'success': False, 'error': 'Source is disabled'}
        
        log_id = self.db.start_scrape_log(source_id)
        
        scraper = self.get_scraper(source_config)
        if not scraper:
            self.db.update_scrape_log(log_id, 'failed', error='Scraper not available')
            return {'success': False, 'error': 'Scraper not available'}
        
        result = {
            'success': False,
            'leads_scraped': 0,
            'leads_saved': 0,
            'duplicates': 0,
            'errors': []
        }
        
        try:
            logger.info(f"Starting scrape for source: {source_config['name']}")
            
            leads_buffer = []
            buffer_size = 50
            
            for idx, lead_data in enumerate(scraper.scrape()):
                if max_leads and idx >= max_leads:
                    break
                
                if not scraper.validate_lead(lead_data):
                    result['errors'].append(f"Invalid lead skipped: {lead_data.get('business_name', 'Unknown')}")
                    continue
                
                leads_buffer.append(lead_data)
                result['leads_scraped'] += 1
                
                if len(leads_buffer) >= buffer_size:
                    save_result = self.db.bulk_save_leads(source_id, leads_buffer)
                    result['leads_saved'] += save_result['saved']
                    result['duplicates'] += save_result['duplicates']
                    leads_buffer = []
                    
                    logger.info(f"Progress: {result['leads_scraped']} scraped, "
                              f"{result['leads_saved']} saved, "
                              f"{result['duplicates']} duplicates")
            
            if leads_buffer:
                save_result = self.db.bulk_save_leads(source_id, leads_buffer)
                result['leads_saved'] += save_result['saved']
                result['duplicates'] += save_result['duplicates']
            
            result['success'] = True
            self.db.update_scrape_log(log_id, 'success', leads_scraped=result['leads_saved'])
            
            logger.info(f"Scraping completed: {result['leads_saved']} new leads saved")
        
        except Exception as e:
            error_msg = f"Scraping failed: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            self.db.update_scrape_log(log_id, 'failed', 
                                     leads_scraped=result['leads_saved'],
                                     error=error_msg)
        
        finally:
            scraper.cleanup()
        
        return result
    
    def run_all_sources(self, max_leads_per_source: Optional[int] = None) -> List[Dict]:
        """Run all enabled sources sequentially"""
        sources = self.db.load_sources(enabled_only=True)
        results = []
        
        for source in sources:
            logger.info(f"\n{'='*60}\nProcessing source: {source['name']}\n{'='*60}")
            result = self.run_scraper(source['id'], max_leads=max_leads_per_source)
            result['source_name'] = source['name']
            results.append(result)
        
        return results
    
    def get_stats(self) -> Dict:
        """Get overall platform statistics"""
        sources = self.db.load_sources(enabled_only=False)
        
        stats = {
            'total_sources': len(sources),
            'enabled_sources': sum(1 for s in sources if s['enabled']),
            'total_leads': 0,
            'sources': []
        }
        
        for source in sources:
            source_stats = self.db.get_scrape_stats(source['id'])
            lead_count = self.db.count_leads(source['id'])
            
            stats['total_leads'] += lead_count
            stats['sources'].append({
                'id': source['id'],
                'name': source['name'],
                'enabled': source['enabled'],
                'leads': lead_count,
                'scrape_stats': source_stats
            })
        
        return stats
