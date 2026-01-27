# 🌾 Harvest - Modular Lead Generation Platform

A production-ready, extensible lead generation and web scraping platform built with Python and Streamlit.

## 🚀 Features

- **Plugin System**: JSON-based source configuration - add new sources without code changes
- **15+ Pre-configured Sources**: Yellow Pages, Yelp, BBB, LinkedIn, Indeed, and more
- **Smart Deduplication**: Fuzzy matching to catch near-duplicates
- **Lead Scoring**: Automatic quality scoring (0-100) for each lead
- **Scheduled Scraping**: Cron-like scheduler for automated campaigns
- **Lead Enrichment**: Email validation, phone formatting, company data enrichment
- **CRM Integration**: HubSpot and Salesforce connectors
- **Multi-format Export**: CSV, JSON, Excel
- **Webhook Notifications**: Slack, Discord, custom webhooks
- **Anti-Detection**: Rotating user agents, request jitter, proxy support

## 📋 Requirements

- Python 3.8+
- 2GB RAM minimum (optimized for low-resource environments like Termux/Replit)
- SQLite (included with Python)

## 🔧 Installation

### Standard Installation

```bash
# Clone or download the project
cd harvest_platform

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Initialize database and load sources
python init_db.py
```

### Termux Installation (Android)

```bash
pkg update
pkg install python git
pip install --upgrade pip
cd harvest_platform
pip install -r requirements.txt --break-system-packages
python init_db.py
```

### Replit Installation

1. Upload the zip to Replit
2. Replit will auto-detect requirements.txt
3. Click "Run" - the app will auto-start

## 🎯 Quick Start

### Run the Web Interface

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

### Run from Command Line

```python
from core.engine import HarvestEngine

# Initialize engine
engine = HarvestEngine()

# Run a specific source
result = engine.run_scraper(source_id=1, max_leads=100)
print(f"Scraped {result['leads_saved']} leads")

# Run all enabled sources
results = engine.run_all_sources(max_leads_per_source=50)

# Get statistics
stats = engine.get_stats()
print(f"Total leads: {stats['total_leads']}")
```

## 📊 Usage Guide

### 1. Configure Sources

Go to **Settings** → **Source Management** in the web interface to:
- Enable/disable sources
- Adjust rate limiting
- Configure selectors
- Add custom sources

### 2. Run Scraping Campaign

**Option A: Manual (Web UI)**
- Go to **Scraper** tab
- Select source
- Set max leads
- Click "Start Scraping"

**Option B: Scheduled (Automated)**
- Go to **Scheduler** tab
- Create daily/weekly/interval jobs
- Monitor in dashboard

### 3. Review & Export Leads

- **Leads** tab: View, filter, score leads
- **Export**: Download as CSV, JSON, or Excel
- **CRM Sync**: Push to HubSpot/Salesforce

## 🔌 Adding Custom Sources

### Method 1: JSON Configuration (No Code)

```python
from core.db import DatabaseManager

db = DatabaseManager()

new_source = {
    "name": "My Custom Directory",
    "source_type": "example_direct",  # Use existing scraper type
    "base_url": "https://example.com/listings",
    "pagination_type": "direct",
    "selectors": {
        "listing_container": ".business-card",
        "business_name": "h2.name",
        "phone": ".phone",
        "email": ".email",
        "website": "a.website",
        "address": ".address",
        "city": ".city",
        "state": ".state"
    },
    "rate_limit_delay": 4.0,
    "enabled": True
}

db.add_source(new_source)
```

### Method 2: Custom Scraper Class

Create `scrapers/my_custom_scraper.py`:

```python
from core.base_scraper import BaseScraper
from bs4 import BeautifulSoup
from typing import Generator, Dict, Optional

class MyCustomScraper(BaseScraper):
    SOURCE_TYPE = "my_custom_type"
    
    def scrape(self) -> Generator[Dict, None, None]:
        response = self._make_request(self.base_url)
        if not response:
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        listings = soup.select(self.selectors.get('listing_container'))
        
        for listing in listings:
            lead = self.parse_lead(listing)
            if lead:
                yield lead
    
    def parse_lead(self, element) -> Optional[Dict]:
        return {
            'business_name': element.select_one('.name').get_text(strip=True),
            'phone': element.select_one('.phone').get_text(strip=True),
            # ... more fields
        }
```

## 🔔 Configuring Notifications

Edit `.env` file:

```bash
# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL

# Enable
ENABLE_NOTIFICATIONS=true
```

## 🔐 API Keys for Enrichment (Optional)

To enable lead enrichment features:

1. **Clearbit** (Company data): https://clearbit.com
2. **Hunter.io** (Email finding): https://hunter.io

Add to `.env`:
```bash
CLEARBIT_API_KEY=your_key_here
HUNTER_API_KEY=your_key_here
```

## 🏗️ Project Structure

```
harvest_platform/
├── core/                  # Core engine components
│   ├── db.py             # Database manager
│   ├── engine.py         # Main orchestration engine
│   ├── base_scraper.py   # Abstract scraper class
│   ├── scheduler.py      # Job scheduler
│   ├── notifications.py  # Notification manager
│   ├── enrichment.py     # Lead enrichment
│   ├── deduplication.py  # Fuzzy matching
│   └── scoring.py        # Lead scoring
├── scrapers/             # Scraper implementations
│   ├── registry.py       # Auto-discovery registry
│   └── ...               # Individual scrapers
├── utils/                # Utility modules
│   ├── anti_detection.py # User agents, delays
│   ├── export.py         # CSV/JSON/Excel export
│   ├── rate_limiter.py   # API rate limiting
│   └── proxy_manager.py  # Proxy rotation
├── integrations/         # CRM integrations
│   └── crm.py           # HubSpot, Salesforce
├── config/              # Configuration
│   ├── production_sources.py  # Pre-built sources
│   └── seed_data.py     # Database seeding
├── app.py               # Streamlit web interface
├── init_db.py           # Database initialization
└── requirements.txt     # Python dependencies
```

## 🛡️ Anti-Detection Features

- **Rotating User Agents**: 5+ realistic browser signatures
- **Request Jitter**: Random 2-7 second delays
- **Retry Logic**: 3 attempts with exponential backoff
- **Proxy Support**: Configure HTTP/HTTPS proxies
- **Rate Limiting**: Configurable per-source delays

## 📈 Performance Tips

### For Low-Resource Environments (Termux/Replit)

1. **Limit concurrent scraping**: Run one source at a time
2. **Use batch size**: Default 50 leads per bulk insert
3. **Enable only needed sources**: Disable unused sources
4. **Set max_leads**: Prevent memory overflow on large sites

### For Production

1. **Use proxies**: Rotate IPs for high-volume scraping
2. **Schedule off-peak**: Run jobs during low-traffic hours
3. **Enable notifications**: Monitor scraping health
4. **Regular exports**: Keep database size manageable

## 🐛 Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt --upgrade
```

### Database locked errors
```bash
# Single-threaded mode in Streamlit
streamlit run app.py --server.headless=true
```

### Scraping returns no results
1. Check if source is enabled
2. Verify selectors are still valid (sites change)
3. Check rate limits aren't too aggressive
4. View logs in **Logs** tab

### Memory issues on Termux
```bash
# Reduce batch size in core/engine.py
buffer_size = 25  # Instead of 50
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Add your scraper to `scrapers/`
4. Update `config/production_sources.py`
5. Submit a pull request

## 📝 License

MIT License - feel free to use for commercial projects.

## ⚠️ Legal Disclaimer

This tool is for educational purposes. Users are responsible for:
- Complying with websites' Terms of Service
- Respecting robots.txt
- Following data protection laws (GDPR, CCPA, etc.)
- Obtaining necessary permissions

**Always scrape responsibly and ethically.**

## 🔗 Resources

- [Streamlit Docs](https://docs.streamlit.io)
- [BeautifulSoup Guide](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests Documentation](https://requests.readthedocs.io)

## 💡 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing documentation
- Review logs in `harvest.db`

---

**Made with ❤️ for growth hackers and lead generation pros**
