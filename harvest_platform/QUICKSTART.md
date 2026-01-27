# 🚀 Quick Start Guide

## Installation (5 minutes)

### 1. Extract the ZIP file
```bash
unzip harvest_platform.zip
cd harvest_platform
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

For **Termux** (Android):
```bash
pip install -r requirements.txt --break-system-packages
```

### 3. Initialize Database
```bash
python init_db.py
```

### 4. Run the Platform
```bash
streamlit run app.py
```

The app will open at http://localhost:8501

## First Steps

1. **Dashboard** - View platform statistics
2. **Settings** - Enable sources you want to scrape
3. **Scraper** - Run your first scraping campaign
4. **Leads** - View and export collected leads

## Configuration (Optional)

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
nano .env  # or use any text editor
```

Add API keys for enrichment (optional):
- Clearbit API key (company data)
- Hunter.io API key (email finding)
- Webhook URLs (Slack, Discord)

## Troubleshooting

### Module not found
```bash
pip install -r requirements.txt --upgrade
```

### Permission errors (Termux)
```bash
chmod +x init_db.py app.py
```

### Database locked
Make sure only one instance is running

## Next Steps

- Check out README.md for detailed documentation
- Add custom sources in Settings
- Configure scheduled jobs in Scheduler tab
- Export leads in CSV/JSON/Excel formats

---

**Need Help?**
- Read the full README.md
- Check the examples in config/production_sources.py
- Review scraper templates in scrapers/registry.py
