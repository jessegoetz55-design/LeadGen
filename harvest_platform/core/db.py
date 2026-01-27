import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import threading

class DatabaseManager:
    """Thread-safe SQLite manager optimized for low-memory environments"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = "harvest.db"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = "harvest.db"):
        if not hasattr(self, 'initialized'):
            self.db_path = db_path
            self.initialized = True
            self._init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database schema"""
        schema = """
        -- Source configurations
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            source_type TEXT NOT NULL,
            base_url TEXT NOT NULL,
            pagination_type TEXT NOT NULL,
            selectors TEXT NOT NULL,
            rate_limit_delay REAL DEFAULT 3.0,
            proxy_config TEXT,
            enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Lead storage with composite unique constraint
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            business_name TEXT NOT NULL,
            city TEXT,
            state TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            address TEXT,
            category TEXT,
            metadata TEXT,
            score INTEGER DEFAULT 0,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES sources(id),
            UNIQUE(business_name, city, phone)
        );
        
        -- Scraping audit logs
        CREATE TABLE IF NOT EXISTS scraper_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            leads_scraped INTEGER DEFAULT 0,
            error_message TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES sources(id)
        );
        
        -- Scheduled jobs
        CREATE TABLE IF NOT EXISTS scheduled_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE NOT NULL,
            source_id INTEGER NOT NULL,
            schedule_type TEXT NOT NULL,
            schedule_config TEXT NOT NULL,
            max_leads INTEGER,
            enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES sources(id)
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source_id);
        CREATE INDEX IF NOT EXISTS idx_leads_scraped_at ON leads(scraped_at);
        CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score);
        CREATE INDEX IF NOT EXISTS idx_logs_source ON scraper_logs(source_id);
        CREATE INDEX IF NOT EXISTS idx_sources_enabled ON sources(enabled);
        """
        
        with self.get_connection() as conn:
            conn.executescript(schema)
    
    # ===== SOURCE MANAGEMENT =====
    
    def load_sources(self, enabled_only: bool = True) -> List[Dict]:
        """Load source configurations from database"""
        query = "SELECT * FROM sources"
        if enabled_only:
            query += " WHERE enabled = 1"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query)
            sources = []
            for row in cursor.fetchall():
                source = dict(row)
                source['selectors'] = json.loads(source['selectors'])
                if source['proxy_config']:
                    source['proxy_config'] = json.loads(source['proxy_config'])
                sources.append(source)
            return sources
    
    def add_source(self, config: Dict) -> int:
        """Add new source configuration"""
        query = """
        INSERT INTO sources (name, source_type, base_url, pagination_type, 
                           selectors, rate_limit_delay, proxy_config, enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, (
                config['name'],
                config['source_type'],
                config['base_url'],
                config['pagination_type'],
                json.dumps(config['selectors']),
                config.get('rate_limit_delay', 3.0),
                json.dumps(config.get('proxy_config')) if config.get('proxy_config') else None,
                config.get('enabled', True)
            ))
            return cursor.lastrowid
    
    def update_source(self, source_id: int, config: Dict):
        """Update existing source configuration"""
        fields = []
        values = []
        
        for key in ['name', 'source_type', 'base_url', 'pagination_type', 
                   'rate_limit_delay', 'enabled']:
            if key in config:
                fields.append(f"{key} = ?")
                values.append(config[key])
        
        if 'selectors' in config:
            fields.append("selectors = ?")
            values.append(json.dumps(config['selectors']))
        
        if 'proxy_config' in config:
            fields.append("proxy_config = ?")
            values.append(json.dumps(config['proxy_config']) if config['proxy_config'] else None)
        
        fields.append("updated_at = ?")
        values.append(datetime.now())
        values.append(source_id)
        
        query = f"UPDATE sources SET {', '.join(fields)} WHERE id = ?"
        
        with self.get_connection() as conn:
            conn.execute(query, values)
    
    def delete_source(self, source_id: int):
        """Delete a source and its associated data"""
        with self.get_connection() as conn:
            # Delete related leads
            conn.execute("DELETE FROM leads WHERE source_id = ?", (source_id,))
            # Delete logs
            conn.execute("DELETE FROM scraper_logs WHERE source_id = ?", (source_id,))
            # Delete jobs
            conn.execute("DELETE FROM scheduled_jobs WHERE source_id = ?", (source_id,))
            # Delete source
            conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
    
    # ===== LEAD MANAGEMENT =====
    
    def save_lead(self, source_id: int, lead_data: Dict) -> Optional[int]:
        """Save lead with duplicate detection. Returns lead_id if saved, None if duplicate."""
        query = """
        INSERT OR IGNORE INTO leads 
        (source_id, business_name, city, state, phone, email, website, 
         address, category, metadata, score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, (
                source_id,
                lead_data.get('business_name', ''),
                lead_data.get('city'),
                lead_data.get('state'),
                lead_data.get('phone'),
                lead_data.get('email'),
                lead_data.get('website'),
                lead_data.get('address'),
                lead_data.get('category'),
                json.dumps(lead_data.get('metadata', {})),
                lead_data.get('score', 0)
            ))
            
            if cursor.rowcount > 0:
                return cursor.lastrowid
            return None
    
    def bulk_save_leads(self, source_id: int, leads: List[Dict]) -> Dict[str, int]:
        """Bulk insert with duplicate tracking"""
        saved = 0
        duplicates = 0
        
        for lead in leads:
            result = self.save_lead(source_id, lead)
            if result:
                saved += 1
            else:
                duplicates += 1
        
        return {'saved': saved, 'duplicates': duplicates}
    
    def get_leads(self, source_id: Optional[int] = None, 
                  limit: int = 1000, offset: int = 0,
                  min_score: Optional[int] = None) -> List[Dict]:
        """Retrieve leads with optional filtering"""
        query = "SELECT * FROM leads WHERE 1=1"
        params = []
        
        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)
        
        if min_score is not None:
            query += " AND score >= ?"
            params.append(min_score)
        
        query += " ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            leads = []
            for row in cursor.fetchall():
                lead = dict(row)
                if lead['metadata']:
                    lead['metadata'] = json.loads(lead['metadata'])
                leads.append(lead)
            return leads
    
    def update_lead_score(self, lead_id: int, score: int):
        """Update lead quality score"""
        with self.get_connection() as conn:
            conn.execute("UPDATE leads SET score = ? WHERE id = ?", (score, lead_id))
    
    def count_leads(self, source_id: Optional[int] = None) -> int:
        """Count total leads"""
        query = "SELECT COUNT(*) as count FROM leads"
        params = []
        
        if source_id:
            query += " WHERE source_id = ?"
            params.append(source_id)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()['count']
    
    # ===== LOGGING =====
    
    def start_scrape_log(self, source_id: int) -> int:
        """Create initial log entry for scraping session"""
        query = """
        INSERT INTO scraper_logs (source_id, status, started_at)
        VALUES (?, 'started', ?)
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, (source_id, datetime.now()))
            return cursor.lastrowid
    
    def update_scrape_log(self, log_id: int, status: str, 
                         leads_scraped: int = 0, error: str = None):
        """Update scraping log with results"""
        query = """
        UPDATE scraper_logs 
        SET status = ?, leads_scraped = ?, error_message = ?, completed_at = ?
        WHERE id = ?
        """
        with self.get_connection() as conn:
            conn.execute(query, (status, leads_scraped, error, datetime.now(), log_id))
    
    def get_recent_logs(self, limit: int = 50, source_id: Optional[int] = None) -> List[Dict]:
        """Get recent scraping logs"""
        query = """
        SELECT l.*, s.name as source_name 
        FROM scraper_logs l
        JOIN sources s ON l.source_id = s.id
        """
        params = []
        
        if source_id:
            query += " WHERE l.source_id = ?"
            params.append(source_id)
        
        query += " ORDER BY l.started_at DESC LIMIT ?"
        params.append(limit)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_scrape_stats(self, source_id: Optional[int] = None) -> Dict:
        """Get scraping statistics"""
        query = """
        SELECT 
            COUNT(*) as total_runs,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
            SUM(leads_scraped) as total_leads
        FROM scraper_logs
        """
        params = []
        
        if source_id:
            query += " WHERE source_id = ?"
            params.append(source_id)
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else {}
