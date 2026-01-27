#!/usr/bin/env python3
"""Initialize database and load production sources"""

from core.db import DatabaseManager
from config.production_sources import PRODUCTION_SOURCES


def init_database():
    """Initialize database and load sources"""
    print("🌾 Harvest Platform - Database Initialization")
    print("=" * 60)
    
    db = DatabaseManager()
    print("✓ Database initialized")
    
    print("\n📦 Loading production sources...")
    loaded = 0
    skipped = 0
    
    for source_config in PRODUCTION_SOURCES:
        try:
            existing = db.load_sources(enabled_only=False)
            if any(s['name'] == source_config['name'] for s in existing):
                print(f"  ⊘ Skipped (exists): {source_config['name']}")
                skipped += 1
            else:
                db.add_source(source_config)
                print(f"  ✓ Loaded: {source_config['name']}")
                loaded += 1
        except Exception as e:
            print(f"  ✗ Failed: {source_config['name']} - {e}")
    
    print(f"\n📊 Summary: {loaded} loaded, {skipped} skipped")
    print("\n✅ Initialization complete!")
    print("\n🚀 Run the platform with: streamlit run app.py")


if __name__ == "__main__":
    init_database()
