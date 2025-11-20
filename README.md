# YellowPages Scraper

A web scraping tool for collecting business URLs and detailed information from YellowPages.com.

## Features

- 🔍 **URL Collection**: Collect business URLs based on search term, state, and city
- 📋 **Data Scraping**: Scrape detailed business information from collected URLs
- 🎨 **Streamlit Interface**: User-friendly web interface for easy operation
- 🛡️ **Anti-Bot Protection**: Uses cloudscraper to bypass Cloudflare protection
- 📊 **CSV Export**: Results are saved in CSV format for easy analysis

## Installation

1. Clone the repository or navigate to the project directory
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Using Streamlit Interface (Recommended)

1. Start the Streamlit app:

```bash
streamlit run app.py
```

2. Open your browser and navigate to the URL shown (usually `http://localhost:8501`)

3. Use the interface to:
   - **URL Collection**: Enter search term, state, and city to collect business URLs
   - **Data Scraping**: Scrape detailed information from collected URLs
   - **View Results**: View and download collected data

### Using Command Line

#### Collect URLs

```python
from main import scrape_yellow_pages

scrape_yellow_pages("dental care", "WA", "Aberdeen")
```

#### Scrape Business Data

```python
from scrape_urls import scrape_url, read_urls_from_csv, get_session

urls = read_urls_from_csv("WA", "Aberdeen", "dental_care")
session = get_session(use_cloudscraper=True)
scrape_url(urls, session, "dental_care", "WA", "Aberdeen")
```

## Project Structure

```
.
├── app.py                 # Streamlit web interface
├── main.py                # URL collection script
├── scrape_urls.py         # Business data scraping script
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── [STATE]/              # Output folders (e.g., WA/, GA/)
    ├── *_urls.csv        # Collected URLs
    ├── *.csv             # Scraped business data
    └── *_failed.csv      # Failed URLs
```

## Configuration

### Cloudscraper

The tool uses `cloudscraper` by default to bypass Cloudflare protection. If you encounter 403 errors:

1. Make sure cloudscraper is installed: `pip install cloudscraper`
2. The tool will automatically use it if available

### Proxies

You can configure proxies in `scrape_urls.py` by adding them to the `PROXIES` list:

```python
PROXIES = [
    "http://user:pass@proxy1:port",
    "http://user:pass@proxy2:port",
]
```

## Output Format

### URL Collection Output
- File: `[STATE]/[state]_[city]_[search_term]_urls.csv`
- Columns: `Url`

### Data Scraping Output
- File: `[STATE]/[state]_[city]_[provider_type].csv`
- Columns: `Username`, `Email`, `Phone Number`, `Password`, `Address`, `Latitude`, `Longitude`, `Provider Type`, `Provider Name`, `State`, `City`

## Notes

- The scraper includes random delays to mimic human behavior
- Failed URLs are saved to separate CSV files for retry
- The tool handles Cloudflare challenges automatically when using cloudscraper
- Be respectful of the website's terms of service and rate limits

## Troubleshooting

### 403 Forbidden Errors
- Install cloudscraper: `pip install cloudscraper`
- Use a proxy/VPN
- Increase delays between requests

### No Results Found
- Verify the search term, state, and city are correct
- Check if the website structure has changed
- Review the debug HTML files generated

## License

This project is for educational purposes only. Please respect the website's terms of service and robots.txt file.

