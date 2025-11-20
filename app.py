import streamlit as st
import os
import pandas as pd
from main import scrape_yellow_pages
from scrape_urls import scrape_url, read_urls_from_csv, get_session
import time

# Page configuration
st.set_page_config(
    page_title="YellowPages Scraper",
    page_icon="📇",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B35;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF6B35;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #E55A2B;
    }
    .info-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f0f2f6;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">📇 YellowPages Scraper</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Choose an option:", ["URL Collection", "Data Scraping", "View Results"])

# State abbreviations for dropdown
US_STATES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
    "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

# Provider types mapping (key: filename format, value: search term)
PROVIDER_TYPES = {
    'diagnostic-center': 'medical diagnostic center',
    'imaging-labs': 'medical imaging labs',
    'primary-care': 'primary care',
    'dental-care': 'dental care',
    'urgent-care': 'urgent care',   
    'vision-care': 'medical vision care',
    'chiropractics': 'chiropractics',
    'physiotherapy': 'physiotherapy'
}

# URL Collection Page
if page == "URL Collection":
    st.header("🔍 Collect Business URLs")
    st.markdown("This tool collects business URLs from YellowPages.com based on your search criteria.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Provider type selection
        provider_type_key = st.selectbox(
            "Provider Type",
            options=list(PROVIDER_TYPES.keys()),
            index=list(PROVIDER_TYPES.keys()).index("dental-care") if "dental-care" in PROVIDER_TYPES else 0,
            format_func=lambda x: PROVIDER_TYPES[x].title(),
            help="Select the type of healthcare provider to search for"
        )
        search_term = PROVIDER_TYPES[provider_type_key]
        
        state_full = st.selectbox(
            "State",
            options=list(US_STATES.keys()),
            index=list(US_STATES.keys()).index("Washington") if "Washington" in US_STATES else 0,
            help="Select the state where you want to search"
        )
        state = US_STATES[state_full]
    
    with col2:
        city_name = st.text_input(
            "City Name",
            value="Aberdeen",
            help="Enter the city name (e.g., 'Aberdeen', 'Seattle', 'New York')"
        )
        
        use_cloudscraper = st.checkbox(
            "Use Cloudscraper (Recommended)",
            value=True,
            help="Use cloudscraper to bypass Cloudflare protection. Requires cloudscraper to be installed."
        )
    
    st.markdown("---")
    
    if st.button("🚀 Start URL Collection", type="primary"):
        if not search_term or not city_name:
            st.error("Please fill in all required fields!")
        else:
            with st.spinner(f"Collecting URLs for '{search_term}' in {city_name}, {state}..."):
                # Create a placeholder for output
                output_placeholder = st.empty()
                log_container = st.container()
                
                # Capture print statements
                import sys
                from io import StringIO
                
                old_stdout = sys.stdout
                sys.stdout = captured_output = StringIO()
                
                try:
                    # Run the scraping function
                    scrape_yellow_pages(search_term, state, city_name, use_cloudscraper=use_cloudscraper)
                    
                    # Get the output
                    output = captured_output.getvalue()
                    sys.stdout = old_stdout
                    
                    # Display output
                    with log_container:
                        st.text_area("Scraping Log", output, height=300)
                    
                    # Check if CSV was created (use provider_type_key for filename)
                    filename = f"{state.lower()}_{city_name}_{provider_type_key}_urls.csv"
                    filepath = os.path.join(state.upper(), filename)
                    
                    if os.path.exists(filepath):
                        st.success(f"✅ URL collection completed! Found URLs saved to: {filepath}")
                        
                        # Show preview of collected URLs
                        try:
                            df = pd.read_csv(filepath)
                            st.subheader("📊 Collected URLs Preview")
                            st.dataframe(df, use_container_width=True)
                            st.info(f"Total URLs collected: {len(df)}")
                        except Exception as e:
                            st.warning(f"Could not preview CSV: {e}")
                    else:
                        st.warning("⚠️ No URLs were collected. Check the log above for details.")
                        
                except Exception as e:
                    sys.stdout = old_stdout
                    st.error(f"❌ Error occurred: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

# Data Scraping Page
elif page == "Data Scraping":
    st.header("📋 Scrape Business Data")
    st.markdown("This tool scrapes detailed business information from collected URLs.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        state_full = st.selectbox(
            "State",
            options=list(US_STATES.keys()),
            index=list(US_STATES.keys()).index("Washington") if "Washington" in US_STATES else 0,
            help="Select the state"
        )
        state = US_STATES[state_full]
        
        # Provider type selection
        provider_type_key = st.selectbox(
            "Provider Type",
            options=list(PROVIDER_TYPES.keys()),
            index=list(PROVIDER_TYPES.keys()).index("dental-care") if "dental-care" in PROVIDER_TYPES else 0,
            format_func=lambda x: PROVIDER_TYPES[x].title(),
            help="Select the provider type (must match the one used for URL collection)"
        )
    
    with col2:
        city_name = st.text_input(
            "City Name",
            value="Aberdeen",
            help="Enter the city name"
        )
    
    use_cloudscraper = st.checkbox(
        "Use Cloudscraper (Recommended)",
        value=True,
        help="Use cloudscraper to bypass Cloudflare protection"
    )
    
    st.markdown("---")
    
    # Check if URL file exists (format: state_city_provider_type_urls.csv)
    filename = f"{state.lower()}_{city_name}_{provider_type_key}_urls.csv"
    filepath = os.path.join(state.upper(), filename)
    
    if os.path.exists(filepath):
        try:
            df_urls = pd.read_csv(filepath)
            st.success(f"✅ Found {len(df_urls)} URLs to scrape from: {filepath}")
            st.dataframe(df_urls.head(10), use_container_width=True)
            if len(df_urls) > 10:
                st.info(f"Showing first 10 URLs. Total: {len(df_urls)}")
        except Exception as e:
            st.error(f"Error reading URL file: {e}")
            filepath = None
    else:
        st.warning(f"⚠️ URL file not found: {filepath}")
        st.info("Please run URL Collection first to generate the URLs file.")
        filepath = None
    
    st.markdown("---")
    
    if st.button("🚀 Start Data Scraping", type="primary", disabled=filepath is None):
        if not city_name:
            st.error("Please fill in all required fields!")
        else:
            with st.spinner(f"Scraping business data from URLs..."):
                # Create a placeholder for output
                log_container = st.container()
                
                # Capture print statements
                import sys
                from io import StringIO
                
                old_stdout = sys.stdout
                sys.stdout = captured_output = StringIO()
                
                try:
                    # Read URLs (use provider_type_key for filename matching)
                    urls = read_urls_from_csv(state, city_name, provider_type_key)
                    
                    if urls:
                        # Initialize session
                        session = get_session(use_cloudscraper=use_cloudscraper)
                        
                        # Establish session
                        try:
                            timeout = 60 if use_cloudscraper else 30
                            response = session.get('https://www.yellowpages.com', timeout=timeout, allow_redirects=True)
                            if response.status_code == 200:
                                st.info("✓ Session established")
                        except Exception as e:
                            st.warning(f"Could not load homepage: {e}")
                        
                        # Run scraping (use provider_type_key for the key parameter)
                        scrape_url(urls, session, provider_type_key, state, city_name, use_cloudscraper=use_cloudscraper)
                        
                        # Get the output
                        output = captured_output.getvalue()
                        sys.stdout = old_stdout
                        
                        # Display output
                        with log_container:
                            st.text_area("Scraping Log", output, height=400)
                        
                        # Check if data CSV was created
                        data_filename = f"{state.lower()}_{city_name}_{provider_type_key}.csv"
                        data_filepath = os.path.join(state.upper(), data_filename)
                        
                        if os.path.exists(data_filepath):
                            st.success(f"✅ Data scraping completed! Results saved to: {data_filepath}")
                            
                            # Show preview
                            try:
                                df = pd.read_csv(data_filepath)
                                st.subheader("📊 Scraped Data Preview")
                                st.dataframe(df, use_container_width=True)
                                st.info(f"Total records scraped: {len(df)}")
                            except Exception as e:
                                st.warning(f"Could not preview CSV: {e}")
                        else:
                            st.warning("⚠️ No data was scraped. Check the log above for details.")
                    else:
                        sys.stdout = old_stdout
                        st.error("No URLs found to scrape!")
                        
                except Exception as e:
                    sys.stdout = old_stdout
                    st.error(f"❌ Error occurred: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

# View Results Page
elif page == "View Results":
    st.header("📊 View Results")
    st.markdown("View and download collected URLs and scraped data.")
    
    # Get all state folders
    state_folders = [f for f in os.listdir('.') if os.path.isdir(f) and len(f) == 2 and f.isupper()]
    
    if not state_folders:
        st.info("No results found. Please run URL Collection or Data Scraping first.")
    else:
        selected_state = st.selectbox("Select State", options=state_folders)
        
        if selected_state:
            folder_path = selected_state
            csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
            
            if not csv_files:
                st.info(f"No CSV files found in {selected_state} folder.")
            else:
                st.subheader(f"Files in {selected_state} folder")
                
                # Separate URL files and data files
                url_files = [f for f in csv_files if '_urls.csv' in f]
                data_files = [f for f in csv_files if '_urls.csv' not in f and '_failed.csv' not in f]
                failed_files = [f for f in csv_files if '_failed.csv' in f]
                
                # URL Files
                if url_files:
                    st.markdown("### 🔗 URL Collection Files")
                    for url_file in url_files:
                        filepath = os.path.join(folder_path, url_file)
                        try:
                            df = pd.read_csv(filepath)
                            with st.expander(f"📄 {url_file} ({len(df)} URLs)"):
                                st.dataframe(df, use_container_width=True)
                                
                                # Download button
                                csv_data = df.to_csv(index=False)
                                st.download_button(
                                    label=f"Download {url_file}",
                                    data=csv_data,
                                    file_name=url_file,
                                    mime="text/csv",
                                    key=f"download_url_{url_file}"
                                )
                        except Exception as e:
                            st.error(f"Error reading {url_file}: {e}")
                
                # Data Files
                if data_files:
                    st.markdown("### 📋 Scraped Data Files")
                    for data_file in data_files:
                        filepath = os.path.join(folder_path, data_file)
                        try:
                            df = pd.read_csv(filepath)
                            with st.expander(f"📄 {data_file} ({len(df)} records)"):
                                st.dataframe(df, use_container_width=True)
                                
                                # Download button
                                csv_data = df.to_csv(index=False)
                                st.download_button(
                                    label=f"Download {data_file}",
                                    data=csv_data,
                                    file_name=data_file,
                                    mime="text/csv",
                                    key=f"download_data_{data_file}"
                                )
                        except Exception as e:
                            st.error(f"Error reading {data_file}: {e}")
                
                # Failed Files
                if failed_files:
                    st.markdown("### ❌ Failed URLs Files")
                    for failed_file in failed_files:
                        filepath = os.path.join(folder_path, failed_file)
                        try:
                            df = pd.read_csv(filepath)
                            with st.expander(f"📄 {failed_file} ({len(df)} failed URLs)"):
                                st.dataframe(df, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error reading {failed_file}: {e}")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>YellowPages Scraper - Built with Streamlit</p>
    </div>
""", unsafe_allow_html=True)



