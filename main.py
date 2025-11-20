import requests
import random
import csv
import os
import time
from urllib.parse import urljoin, urlencode
from bs4 import BeautifulSoup

# Try to import cloudscraper for better anti-bot protection handling
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False


def urls_to_csv(urls, state, city_name, provider_type):
    """Save URLs to CSV file"""
    filename = f"{state}_{city_name}_{provider_type}_urls.csv".replace(" ", "_").lower()
    folder = state.upper()
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    file_exists = os.path.isfile(filepath)

    with open(filepath, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Url'])
        for url in urls:
            writer.writerow([url])


def random_delay(min_sec=2, max_sec=5):
    """Add random delay to mimic human behavior"""
    time.sleep(random.uniform(min_sec, max_sec))


def get_session(use_cloudscraper=True):
    """
    Create a requests session with proper headers
    If cloudscraper is available and use_cloudscraper is True, use it to bypass anti-bot protection
    """
    if CLOUDSCRAPER_AVAILABLE and use_cloudscraper:
        print("Using cloudscraper for better anti-bot protection...")
        # cloudscraper automatically handles Cloudflare and other protections
        # Use delay parameter to give it time to solve challenges
        session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            },
            delay=10  # Give cloudscraper time to solve challenges
        )
    else:
        if use_cloudscraper and not CLOUDSCRAPER_AVAILABLE:
            print("Note: cloudscraper not available. Install it with: pip install cloudscraper")
            print("It helps bypass Cloudflare and other anti-bot protections.")
            print("Continuing with standard requests library...")
        session = requests.Session()
        # Use a more recent and realistic User-Agent
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        
        session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        })
    return session


def scrape_yellow_pages(search_term, state, city_name, use_cloudscraper=True):
    """
    Scrape YellowPages.com for business URLs
    
    Args:
        search_term: The search term (e.g., "dental care")
        state: State abbreviation (e.g., "WA")
        city_name: City name (e.g., "Aberdeen")
        use_cloudscraper: Whether to use cloudscraper if available (default: True)
    """
    print("SCRAPING STARTED.....")
    print(f"Search Term: {search_term}")
    print(f"Location: {city_name}, {state}")
    
    session = get_session(use_cloudscraper=use_cloudscraper)
    
    # First, establish session by visiting homepage
    print("Establishing session by visiting homepage...")
    try:
        # Visit homepage first to get cookies and establish session
        # Use longer timeout if using cloudscraper as it may need to solve challenges
        timeout = 60 if (CLOUDSCRAPER_AVAILABLE and use_cloudscraper) else 30
        response = session.get('https://www.yellowpages.com', timeout=timeout, allow_redirects=True)
        print(f"Homepage response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Homepage loaded successfully")
            # Wait a bit to mimic human behavior
            random_delay(3, 5)
        elif response.status_code == 403:
            print("⚠ Got 403 on homepage")
            if CLOUDSCRAPER_AVAILABLE and use_cloudscraper:
                print("Even with cloudscraper, getting 403. The site may have very strong protection.")
                print("You might need to use a proxy or browser automation (Playwright/Selenium)")
            else:
                print("Trying with different approach...")
                # Try visiting a different page first
                session.get('https://www.yellowpages.com/about', timeout=timeout)
                random_delay(2, 4)
        else:
            print(f"Warning: Homepage returned status {response.status_code}")
    except Exception as e:
        print(f"Warning: Could not load homepage: {e}")
        print("Continuing anyway...")
    
    all_urls = []
    page_num = 1
    consecutive_failures = 0
    max_failures = 3
    
    try:
        while page_num < 100:
            print(f"Collecting URLs from Page: {page_num}")
            
            # Construct search URL
            base_url = "https://www.yellowpages.com/search"
            params = {
                'search_terms': search_term,
                'geo_location_terms': f"{city_name}, {state}"
            }
            
            # Add page parameter if not first page
            if page_num > 1:
                params['page'] = page_num
            
            search_url = f"{base_url}?{urlencode(params)}"
            
            try:
                print(f"Navigating to: {search_url}")
                
                # Update referer for subsequent requests (only if not using cloudscraper)
                if not (CLOUDSCRAPER_AVAILABLE and use_cloudscraper):
                    session.headers.update({
                        'Referer': 'https://www.yellowpages.com/' if page_num == 1 else search_url
                    })
                
                # Use longer timeout if using cloudscraper
                timeout = 60 if (CLOUDSCRAPER_AVAILABLE and use_cloudscraper) else 30
                response = session.get(search_url, timeout=timeout, allow_redirects=True)
                
                # Check response status
                if response.status_code == 403:
                    print(f"Got 403 Forbidden - site may be blocking requests")
                    print("Response headers:", dict(response.headers))
                    
                    # Save the response HTML to see what Cloudflare is showing
                    debug_html_path = f"debug_403_page_{page_num}.html"
                    with open(debug_html_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"Saved 403 response to {debug_html_path} for inspection")
                    
                    # Check if it's a Cloudflare challenge
                    if 'cloudflare' in response.text.lower() or 'challenge' in response.text.lower():
                        print("Cloudflare challenge detected in response")
                        print("You need to install cloudscraper: pip install cloudscraper")
                        print("Or the site requires manual browser interaction")
                    
                    print("Trying with additional delay...")
                    random_delay(10, 15)
                    # Retry once with appropriate timeout
                    timeout = 60 if (CLOUDSCRAPER_AVAILABLE and use_cloudscraper) else 30
                    response = session.get(search_url, timeout=timeout, allow_redirects=True)
                
                if response.status_code >= 400:
                    print(f"Got error status code: {response.status_code}")
                    if response.status_code == 403:
                        print("403 Forbidden - The website is blocking automated requests.")
                        print("You may need to:")
                        print("  1. Use a proxy/VPN")
                        print("  2. Add more delays between requests")
                        print("  3. Use a tool like cloudscraper or curl_cffi")
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print("Too many HTTP errors, stopping")
                        break
                    page_num += 1
                    random_delay(5, 8)
                    continue
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check if we got a Cloudflare challenge page
                page_content = response.text.lower()
                if 'challenge-platform' in page_content or 'just a moment' in page_content:
                    print("Cloudflare challenge detected, waiting...")
                    random_delay(10, 15)
                    # Retry the request
                    response = session.get(search_url, timeout=30)
                    soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try multiple selectors for results
                result_cards = []
                
                # Try different class selectors
                class_selectors = ['result', 'organic', 'srp-listing', 'business-card']
                for class_name in class_selectors:
                    result_cards = soup.find_all('div', class_=class_name)
                    if result_cards:
                        print(f"Found {len(result_cards)} results using class: {class_name}")
                        break
                
                # Try data-impression attribute
                if not result_cards:
                    result_cards = soup.find_all('div', attrs={'data-impression': True})
                    if result_cards:
                        print(f"Found {len(result_cards)} results using data-impression attribute")
                
                # Also try finding by business-name class
                if not result_cards:
                    business_names = soup.find_all('a', class_='business-name')
                    if business_names:
                        # Get parent divs
                        result_cards = [name.find_parent('div', class_=lambda x: x and 'result' in x.lower()) 
                                       for name in business_names if name.find_parent('div')]
                        result_cards = [card for card in result_cards if card]
                        if result_cards:
                            print(f"Found {len(result_cards)} results using business-name links")
                
                if not result_cards:
                    print("No result cards found with any selector")
                    
                    # Save HTML content for inspection
                    html_path = f"debug_page_{page_num}.html"
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"HTML saved to {html_path}")
                    print(f"Page title: {soup.title.string if soup.title else 'N/A'}")
                    print(f"Current URL: {search_url}")
                    
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print("No results for multiple pages, stopping")
                        break
                    page_num += 1
                    random_delay(3, 5)
                    continue
                
                page_urls_before = len(all_urls)
                
                # Extract URLs from each card
                for card in result_cards:
                    try:
                        # Try different selectors for business name link
                        business_link = None
                        
                        # Try finding business-name link
                        business_link = card.find('a', class_='business-name')
                        if not business_link:
                            business_link = card.find('a', href=lambda x: x and '/mip/' in x)
                        if not business_link:
                            business_link = card.find('h2', class_='business-name').find('a') if card.find('h2', class_='business-name') else None
                        if not business_link:
                            business_link = card.find('h3', class_='business-name').find('a') if card.find('h3', class_='business-name') else None
                        if not business_link:
                            # Try any link with business in class or href
                            business_link = card.find('a', class_=lambda x: x and 'business' in x.lower())
                        if not business_link:
                            # Try any link with data-business attribute
                            business_link = card.find('a', attrs={'data-business': True})
                        
                        if business_link:
                            url = business_link.get('href')
                            if url:
                                # Make sure URL is absolute
                                if not url.startswith('http'):
                                    url = urljoin('https://www.yellowpages.com', url)
                                if url and url not in all_urls:
                                    all_urls.append(url)
                                    print(f"  Found URL: {url}")
                    except Exception as e:
                        print(f"Error extracting URL from card: {str(e)}")
                
                page_urls_collected = len(all_urls) - page_urls_before
                print(f"Collected {page_urls_collected} URLs from page {page_num}. Total: {len(all_urls)}")
                
                if page_urls_collected == 0:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print("No new URLs found for multiple pages, stopping")
                        break
                else:
                    consecutive_failures = 0
                
                # Check for next page
                has_next = False
                next_selectors = [
                    ('a', {'aria-label': 'Next'}),
                    ('a', {'rel': 'next'}),
                    ('a', {'class': 'next'}),
                    ('a', {'class': 'next-page'}),
                ]
                
                for tag, attrs in next_selectors:
                    next_button = soup.find(tag, attrs)
                    if next_button:
                        # Check if button is disabled
                        disabled = next_button.get('disabled')
                        aria_disabled = next_button.get('aria-disabled')
                        classes = next_button.get('class', [])
                        
                        if not disabled and aria_disabled != 'true' and 'disabled' not in classes:
                            has_next = True
                            break
                
                # Also check pagination
                if not has_next:
                    pagination = soup.find('div', class_='pagination')
                    if pagination:
                        next_link = pagination.find('a', class_=lambda x: x and 'next' in x and 'disabled' not in x)
                        if next_link:
                            has_next = True
                
                if not has_next:
                    print("Reached last page - no next button available")
                    break
                
                page_num += 1
                random_delay(3, 6)
                
            except requests.exceptions.Timeout as e:
                print(f"Timeout error on page {page_num}: {str(e)}")
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    print("Too many timeouts, stopping")
                    break
                page_num += 1
                random_delay(5, 8)
                continue
            except Exception as e:
                print(f"Error loading search page {page_num}: {str(e)}")
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    print("Too many failures, stopping")
                    break
                page_num += 1
                random_delay(5, 8)
                continue
    
    except Exception as e:
        print(f"Error during URL collection: {str(e)}")
    
    print(f"Total URLs collected: {len(all_urls)}")
    all_urls = list(set(all_urls))
    print(f"Unique URLs after deduplication: {len(all_urls)}")
    
    if all_urls:
        # Create a safe provider type name from search term
        provider_type = search_term.replace(" ", "_").lower()
        urls_to_csv(all_urls, state, city_name, provider_type)
    
    print("SCRAPING COMPLETED!")


if __name__ == "__main__":
    # Example usage:
    # scrape_yellow_pages("dental care", "WA", "Aberdeen")
    
    # You can modify these parameters or pass them as command-line arguments
    scrape_yellow_pages("dental care", "WA", "Aberdeen")
