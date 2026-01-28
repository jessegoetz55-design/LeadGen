from core.db import DatabaseManager

db = DatabaseManager()

# Delete old Yellow Pages
sources = db.load_sources(enabled_only=False)
for s in sources:
    if 'yellow' in s['name'].lower():
        db.delete_source(s['id'])

# Add Pro version
db.add_source({
    'name': 'Yellow Pages PRO',
    'source_type': 'yellowpages_pro',
    'base_url': 'https://www.yellowpages.com/new-york-ny/restaurants',
    'pagination_type': 'click_next',
    'selectors': {},
    'rate_limit_delay': 5.0,
    'enabled': True
})

print("✅ Yellow Pages PRO added!")