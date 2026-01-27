#!/usr/bin/env python3
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# Set page config first
st.set_page_config(
    page_title="🌾 Harvest - Lead Generation Platform",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

from core.engine import HarvestEngine
from core.db import DatabaseManager
from core.scheduler import HarvestScheduler
from core.scoring import LeadScorer
from utils.export import DataExporter

# Initialize session state
if 'engine' not in st.session_state:
    st.session_state.engine = HarvestEngine()
    st.session_state.db = DatabaseManager()

# Sidebar navigation
st.sidebar.title("🌾 Harvest Platform")
page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "🔄 Scraper", "📋 Leads", "⚙️ Settings", "📅 Scheduler", "📜 Logs"]
)

# ===== DASHBOARD PAGE =====
if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    
    stats = st.session_state.engine.get_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Sources", stats['total_sources'])
        st.metric("Enabled Sources", stats['enabled_sources'])
    
    with col2:
        st.metric("Total Leads", f"{stats['total_leads']:,}")
    
    with col3:
        total_runs = sum(s['scrape_stats'].get('total_runs', 0) for s in stats['sources'])
        st.metric("Total Scrape Runs", total_runs)
    
    st.divider()
    
    st.subheader("📈 Source Overview")
    
    if stats['sources']:
        df_sources = pd.DataFrame([
            {
                'ID': s['id'],
                'Name': s['name'],
                'Status': '✅ Enabled' if s['enabled'] else '❌ Disabled',
                'Leads': s['leads'],
                'Runs': s['scrape_stats'].get('total_runs', 0),
                'Success Rate': f"{(s['scrape_stats'].get('successful', 0) / max(s['scrape_stats'].get('total_runs', 1), 1) * 100):.1f}%"
            }
            for s in stats['sources']
        ])
        
        st.dataframe(df_sources, use_container_width=True, hide_index=True)
    else:
        st.info("No sources configured yet. Go to Settings to add sources.")

# ===== SCRAPER PAGE =====
elif page == "🔄 Scraper":
    st.title("🔄 Run Scraper")
    
    sources = st.session_state.db.load_sources(enabled_only=True)
    
    if not sources:
        st.warning("⚠️ No enabled sources. Enable sources in Settings first.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            source_options = {s['name']: s['id'] for s in sources}
            selected_source = st.selectbox("Select Source", list(source_options.keys()))
            
        with col2:
            max_leads = st.number_input("Max Leads (0 = unlimited)", min_value=0, value=100, step=10)
        
        if st.button("▶️ Start Scraping", type="primary"):
            source_id = source_options[selected_source]
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text(f"Starting scrape for {selected_source}...")
            progress_bar.progress(25)
            
            result = st.session_state.engine.run_scraper(
                source_id, 
                max_leads=max_leads if max_leads > 0 else None
            )
            
            progress_bar.progress(100)
            
            if result['success']:
                st.success(f"""
                ✅ Scraping completed!
                - **Scraped:** {result['leads_scraped']} leads
                - **Saved:** {result['leads_saved']} new leads
                - **Duplicates:** {result['duplicates']} leads
                """)
            else:
                st.error(f"❌ Scraping failed: {result.get('error', 'Unknown error')}")
            
            if result.get('errors'):
                with st.expander("⚠️ View Errors"):
                    for error in result['errors']:
                        st.text(error)

# ===== LEADS PAGE =====
elif page == "📋 Leads":
    st.title("📋 Leads Management")
    
    tab1, tab2 = st.tabs(["🔍 Browse", "📥 Export"])
    
    with tab1:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sources = st.session_state.db.load_sources(enabled_only=False)
            source_filter = st.selectbox(
                "Filter by Source",
                ["All Sources"] + [s['name'] for s in sources]
            )
        
        with col2:
            min_score = st.slider("Minimum Quality Score", 0, 100, 0)
        
        with col3:
            limit = st.number_input("Results per page", min_value=10, max_value=1000, value=100)
        
        source_id = None
        if source_filter != "All Sources":
            source_id = next(s['id'] for s in sources if s['name'] == source_filter)
        
        leads = st.session_state.db.get_leads(
            source_id=source_id,
            limit=limit,
            min_score=min_score if min_score > 0 else None
        )
        
        if leads:
            st.success(f"Found {len(leads)} leads")
            
            df_leads = pd.DataFrame([
                {
                    'Business': lead['business_name'],
                    'City': lead.get('city', 'N/A'),
                    'State': lead.get('state', 'N/A'),
                    'Phone': lead.get('phone', 'N/A'),
                    'Email': lead.get('email', 'N/A'),
                    'Website': lead.get('website', 'N/A'),
                    'Score': lead.get('score', 0),
                    'Quality': LeadScorer.classify_lead(lead.get('score', 0)),
                    'Scraped': str(lead.get('scraped_at', ''))[:10]
                }
                for lead in leads
            ])
            
            st.dataframe(df_leads, use_container_width=True, hide_index=True)
        else:
            st.info("No leads found with current filters.")
    
    with tab2:
        st.subheader("📥 Export Leads")
        
        export_format = st.radio("Format", ["CSV", "JSON", "Excel"])
        include_metadata = st.checkbox("Include metadata")
        
        if st.button("Generate Export"):
            leads = st.session_state.db.get_leads(limit=10000)
            
            if not leads:
                st.warning("No leads to export")
            else:
                if export_format == "CSV":
                    csv_data = DataExporter.to_csv(leads, include_metadata)
                    st.download_button(
                        "💾 Download CSV",
                        csv_data,
                        file_name=f"harvest_leads_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                
                elif export_format == "JSON":
                    json_data = DataExporter.to_json(leads)
                    st.download_button(
                        "💾 Download JSON",
                        json_data,
                        file_name=f"harvest_leads_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
                
                elif export_format == "Excel":
                    try:
                        excel_buffer = DataExporter.to_excel_buffer(leads)
                        st.download_button(
                            "💾 Download Excel",
                            excel_buffer,
                            file_name=f"harvest_leads_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except ImportError:
                        st.error("openpyxl not installed. Run: pip install openpyxl")

# ===== SETTINGS PAGE =====
elif page == "⚙️ Settings":
    st.title("⚙️ Source Management")
    
    tab1, tab2 = st.tabs(["📝 Sources", "➕ Add Source"])
    
    with tab1:
        sources = st.session_state.db.load_sources(enabled_only=False)
        
        for source in sources:
            with st.expander(f"{'✅' if source['enabled'] else '❌'} {source['name']}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input("Base URL", source['base_url'], disabled=True, key=f"url_{source['id']}")
                    st.text_input("Source Type", source['source_type'], disabled=True, key=f"type_{source['id']}")
                    st.number_input("Rate Limit (seconds)", value=source['rate_limit_delay'], 
                                  key=f"rate_{source['id']}", disabled=True)
                
                with col2:
                    enabled = st.checkbox("Enabled", value=source['enabled'], key=f"enabled_{source['id']}")
                    
                    if st.button("💾 Save Changes", key=f"save_{source['id']}"):
                        st.session_state.db.update_source(source['id'], {'enabled': enabled})
                        st.success("✅ Source updated!")
                        st.rerun()
                    
                    if st.button("🗑️ Delete Source", key=f"delete_{source['id']}"):
                        st.session_state.db.delete_source(source['id'])
                        st.success("✅ Source deleted!")
                        st.rerun()
                
                st.json(source['selectors'])
    
    with tab2:
        st.subheader("➕ Add New Source")
        
        with st.form("add_source_form"):
            name = st.text_input("Source Name *")
            source_type = st.text_input("Source Type *", value="example_direct")
            base_url = st.text_input("Base URL *")
            rate_limit = st.number_input("Rate Limit (seconds)", value=3.0, min_value=1.0, step=0.5)
            
            st.text("Selectors (JSON format):")
            selectors_json = st.text_area(
                "Selectors",
                value=json.dumps({
                    "listing_container": ".listing",
                    "business_name": ".name",
                    "phone": ".phone",
                    "email": ".email",
                    "website": "a.website",
                    "address": ".address",
                    "city": ".city",
                    "state": ".state"
                }, indent=2),
                height=200
            )
            
            submitted = st.form_submit_button("➕ Add Source")
            
            if submitted:
                if not all([name, source_type, base_url]):
                    st.error("Please fill in all required fields (*)")
                else:
                    try:
                        selectors = json.loads(selectors_json)
                        
                        new_source = {
                            'name': name,
                            'source_type': source_type,
                            'base_url': base_url,
                            'pagination_type': 'direct',
                            'selectors': selectors,
                            'rate_limit_delay': rate_limit,
                            'enabled': True
                        }
                        
                        st.session_state.db.add_source(new_source)
                        st.success(f"✅ Source '{name}' added successfully!")
                        st.rerun()
                    
                    except json.JSONDecodeError:
                        st.error("Invalid JSON in selectors field")
                    except Exception as e:
                        st.error(f"Error adding source: {e}")

# ===== SCHEDULER PAGE =====
elif page == "📅 Scheduler":
    st.title("📅 Scheduled Jobs")
    st.info("⚠️ Scheduler feature requires the app to run continuously. Jobs will be lost on restart.")
    
    if 'scheduler' not in st.session_state:
        st.session_state.scheduler = HarvestScheduler(st.session_state.engine)
        st.session_state.scheduler.start()
    
    tab1, tab2 = st.tabs(["📋 Active Jobs", "➕ Add Job"])
    
    with tab1:
        jobs = st.session_state.scheduler.get_jobs()
        
        if jobs:
            for job_id, job_info in jobs.items():
                with st.expander(f"🕐 {job_info['schedule']}", expanded=False):
                    st.write(f"**Job ID:** {job_id}")
                    st.write(f"**Source ID:** {job_info['source_id']}")
                    st.write(f"**Next Run:** {job_info.get('next_run', 'N/A')}")
                    
                    if st.button("🗑️ Remove Job", key=f"remove_{job_id}"):
                        st.session_state.scheduler.remove_job(job_id)
                        st.success("Job removed!")
                        st.rerun()
        else:
            st.info("No scheduled jobs. Add one in the 'Add Job' tab.")
    
    with tab2:
        sources = st.session_state.db.load_sources(enabled_only=True)
        
        if not sources:
            st.warning("No enabled sources available")
        else:
            source_options = {s['name']: s['id'] for s in sources}
            selected_source = st.selectbox("Source", list(source_options.keys()))
            
            schedule_type = st.radio("Schedule Type", ["Daily", "Interval (hours)", "Weekly"])
            
            if schedule_type == "Daily":
                time_str = st.time_input("Time").strftime("%H:%M")
                
                if st.button("Add Daily Job"):
                    source_id = source_options[selected_source]
                    job_id = st.session_state.scheduler.add_daily_job(source_id, time_str)
                    st.success(f"✅ Daily job created: {job_id}")
            
            elif schedule_type == "Interval (hours)":
                hours = st.number_input("Hours", min_value=1, max_value=24, value=6)
                
                if st.button("Add Interval Job"):
                    source_id = source_options[selected_source]
                    job_id = st.session_state.scheduler.add_interval_job(source_id, hours)
                    st.success(f"✅ Interval job created: {job_id}")
            
            else:  # Weekly
                day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
                time_str = st.time_input("Time", key="weekly_time").strftime("%H:%M")
                
                if st.button("Add Weekly Job"):
                    source_id = source_options[selected_source]
                    job_id = st.session_state.scheduler.add_weekly_job(source_id, day, time_str)
                    st.success(f"✅ Weekly job created: {job_id}")

# ===== LOGS PAGE =====
elif page == "📜 Logs":
    st.title("📜 Scraping Logs")
    
    logs = st.session_state.db.get_recent_logs(limit=100)
    
    if logs:
        df_logs = pd.DataFrame([
            {
                'Time': str(log['started_at'])[:19],
                'Source': log['source_name'],
                'Status': '✅ Success' if log['status'] == 'success' else '❌ Failed' if log['status'] == 'failed' else '🔄 Running',
                'Leads': log['leads_scraped'],
                'Duration': str(log.get('completed_at', ''))[:19] if log.get('completed_at') else 'Running...',
                'Error': log.get('error_message', '')[:50] if log.get('error_message') else ''
            }
            for log in logs
        ])
        
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("No scraping logs yet.")

# Footer
st.sidebar.divider()
st.sidebar.caption("🌾 Harvest Platform v1.0")
st.sidebar.caption("Made for growth hackers")
