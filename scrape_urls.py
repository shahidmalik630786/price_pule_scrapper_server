import csv
import os
import time
import json
import random
import requests
from bs4 import BeautifulSoup

# Try to import cloudscraper for better anti-bot protection handling
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False


# ---------------------- Configuration -----------------------
PROXIES = [
    # "http://user:pass@proxy1:port",
]


# ---------------------- Utilities -----------------------
def get_random_proxy():
    return random.choice(PROXIES) if PROXIES else None


def get_session(use_cloudscraper=True):
    """
    Create a requests session with proper headers
    If cloudscraper is available and use_cloudscraper is True, use it to bypass anti-bot protection
    """
    if CLOUDSCRAPER_AVAILABLE and use_cloudscraper:
        print("Using cloudscraper for better anti-bot protection...")
        # cloudscraper automatically handles Cloudflare and other protections
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
    
    # Add proxy if configured
    proxy = get_random_proxy()
    if proxy:
        session.proxies = {
            'http': proxy,
            'https': proxy
        }
    
    return session


def random_delay(min_sec=2, max_sec=5):
    """Add random delay to mimic human behavior"""
    time.sleep(random.uniform(min_sec, max_sec))


def to_csv(username, email, phonenumber, password1, address, latitude, longitude, provider_type, provider_name, state, city_name):
    """Save scraped data to CSV file"""
    filename = f"{state}_{city_name}_{provider_type}.csv".replace(" ", "_").lower()
    folder = state.upper()
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)

    file_exists = os.path.isfile(filepath)
    with open(filepath, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow([
                'Username', 'Email', 'Phone Number', 'Password',
                'Address', 'Latitude', 'Longitude',
                'Provider Type', 'Provider Name',
                'State', 'City'
            ])
        writer.writerow([
            username, email, phonenumber, password1,
            address, latitude, longitude,
            provider_type, provider_name,
            state, city_name
        ])


def read_urls_from_csv(state, city_name, provider_type):
    """Read URLs from CSV file"""
    filename = f"{state}_{city_name}_{provider_type}_urls.csv".replace(" ", "_").lower()
    folder = state.upper()
    filepath = os.path.join(folder, filename)
    urls = []
    
    if os.path.exists(filepath):
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                urls.append(row['Url'] if 'Url' in row else list(row.values())[0])
        print(f"✓ Loaded {len(urls)} URLs from {filepath}")
    else:
        print(f"✗ URL CSV file not found: {filepath}")
    return urls


def extract_business_data(soup, url):
    """
    Extract business data from the parsed HTML
    Returns a dictionary with all extracted data
    """
    data = {
        'username': None,
        'phonenumber': None,
        'address': None,
        'latitude': None,
        'longitude': None
    }
    
    try:
        # Extract username from sales-info class
        sales_info = soup.find('div', class_='sales-info')
        if sales_info:
            data['username'] = sales_info.get_text(strip=True)
        else:
            # Try alternative selectors
            sales_info = soup.find('h1', class_='business-name')
            if sales_info:
                data['username'] = sales_info.get_text(strip=True)
            else:
                # Try any h1 tag
                h1 = soup.find('h1')
                if h1:
                    data['username'] = h1.get_text(strip=True)
    except Exception as e:
        print(f"  ⚠ Error extracting username: {e}")
    
    try:
        # Extract phone and address from default-ctas
        default_ctas = soup.find('div', id='default-ctas')
        if default_ctas:
            # Find phone
            phone_elem = default_ctas.find('div', class_='phone')
            if phone_elem:
                data['phonenumber'] = phone_elem.get_text(strip=True)
            else:
                # Try alternative phone selectors
                phone_elem = default_ctas.find('a', class_='phone')
                if phone_elem:
                    data['phonenumber'] = phone_elem.get_text(strip=True)
            
            # Find address
            address_elem = default_ctas.find('div', class_='address')
            if address_elem:
                data['address'] = address_elem.get_text(strip=True)
            else:
                # Try alternative address selectors
                address_elem = default_ctas.find('span', class_='address')
                if address_elem:
                    data['address'] = address_elem.get_text(strip=True)
        else:
            # Try finding phone and address elsewhere
            phone_elem = soup.find('div', class_='phone') or soup.find('a', class_='phone')
            if phone_elem:
                data['phonenumber'] = phone_elem.get_text(strip=True)
            
            address_elem = soup.find('div', class_='address') or soup.find('span', class_='address')
            if address_elem:
                data['address'] = address_elem.get_text(strip=True)
    except Exception as e:
        print(f"  ⚠ Error extracting phone/address: {e}")
    
    try:
        # Extract geo coordinates from JSON-LD script tag
        script_tags = soup.find_all('script', type='application/ld+json')
        for script_tag in script_tags:
            try:
                json_content = script_tag.string
                if json_content:
                    json_data = json.loads(json_content)
                    
                    # Handle different JSON-LD structures
                    if isinstance(json_data, dict):
                        geo = json_data.get('geo', {})
                        if geo:
                            data['latitude'] = geo.get('latitude')
                            data['longitude'] = geo.get('longitude')
                        else:
                            # Try alternative structure
                            location = json_data.get('location', {})
                            if location:
                                geo = location.get('geo', {})
                                data['latitude'] = geo.get('latitude')
                                data['longitude'] = geo.get('longitude')
                    elif isinstance(json_data, list):
                        # Sometimes JSON-LD is an array
                        for item in json_data:
                            if isinstance(item, dict):
                                geo = item.get('geo', {})
                                if geo:
                                    data['latitude'] = geo.get('latitude')
                                    data['longitude'] = geo.get('longitude')
                                    break
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"  ⚠ Error parsing JSON-LD: {e}")
                continue
    except Exception as e:
        print(f"  ⚠ Error extracting geo coordinates: {e}")
    
    return data


def scrape_url(urls, session, key, state, city_name, use_cloudscraper=True):
    """Scrape business data from each URL"""
    url_count = 1
    failed_urls = []

    for url in urls:
        print(f"\n{'='*60}")
        print(f"URL {url_count}/{len(urls)} - Scraping: {url}")
        print(f"{'='*60}")

        max_retries = 3
        retry_count = 0
        success = False

        while retry_count < max_retries and not success:
            try:
                # Random delay between requests
                if url_count > 1:
                    delay = random.uniform(3, 8)
                    print(f"Waiting {delay:.2f} seconds before next request...")
                    time.sleep(delay)

                print(f"Attempt {retry_count + 1}/{max_retries}")
                
                # Use longer timeout if using cloudscraper
                timeout = 60 if (CLOUDSCRAPER_AVAILABLE and use_cloudscraper) else 30
                
                # Update referer
                if not (CLOUDSCRAPER_AVAILABLE and use_cloudscraper):
                    session.headers.update({
                        'Referer': 'https://www.yellowpages.com/'
                    })
                
                # Make request
                response = session.get(url, timeout=timeout, allow_redirects=True)
                
                # Check response status
                if response.status_code == 403:
                    print(f"  ⚠ Got 403 Forbidden")
                    if CLOUDSCRAPER_AVAILABLE and use_cloudscraper:
                        print("  Even with cloudscraper, getting 403. The site may have very strong protection.")
                    else:
                        print("  You may need to install cloudscraper: pip install cloudscraper")
                    
                    # Retry with delay
                    if retry_count < max_retries - 1:
                        wait_time = random.uniform(10, 20)
                        print(f"  Waiting {wait_time:.2f} seconds before retry...")
                        time.sleep(wait_time)
                        retry_count += 1
                        continue
                
                if response.status_code >= 400:
                    print(f"  ✗ Got error status code: {response.status_code}")
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = random.uniform(5, 10) * retry_count
                        print(f"  Waiting {wait_time:.2f} seconds before retry...")
                        time.sleep(wait_time)
                    continue
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for Cloudflare challenge
                page_content = response.text.lower()
                if 'challenge-platform' in page_content or 'just a moment' in page_content:
                    print("  ⚠ Cloudflare challenge detected, waiting...")
                    time.sleep(random.uniform(10, 15))
                    # Retry the request
                    response = session.get(url, timeout=timeout, allow_redirects=True)
                    soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract data
                business_data = extract_business_data(soup, url)
                
                # Validate required data
                if not business_data['username']:
                    raise ValueError("Could not extract username/business name")
                
                # Generate email and password from username
                username_parts = business_data['username'].split()
                email = "".join(username_parts) + "@gmail.com" if username_parts else "default@gmail.com"
                password1 = username_parts[0] + "@123" if username_parts else "default@123"
                provider_name = business_data['username']

                # Save to CSV
                to_csv(
                    business_data['username'],
                    email,
                    business_data['phonenumber'] or 'N/A',
                    password1,
                    business_data['address'] or 'N/A',
                    business_data['latitude'] or 'N/A',
                    business_data['longitude'] or 'N/A',
                    key,
                    provider_name,
                    state,
                    city_name
                )
                
                print(f"  ✓ Successfully scraped: {business_data['username']}")
                if business_data['phonenumber']:
                    print(f"    Phone: {business_data['phonenumber']}")
                if business_data['address']:
                    print(f"    Address: {business_data['address']}")
                success = True

            except requests.exceptions.Timeout as e:
                retry_count += 1
                print(f"  ✗ Timeout error (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    wait_time = random.uniform(5, 10) * retry_count
                    print(f"  Waiting {wait_time:.2f} seconds before retry...")
                    time.sleep(wait_time)
                    
            except requests.exceptions.RequestException as e:
                retry_count += 1
                print(f"  ✗ Request error (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    wait_time = random.uniform(5, 10) * retry_count
                    print(f"  Waiting {wait_time:.2f} seconds before retry...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                retry_count += 1
                print(f"  ✗ Error (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    time.sleep(random.uniform(3, 7))

        if not success:
            print(f"  ✗ Failed to scrape after {max_retries} attempts: {url}")
            failed_urls.append(url)

        url_count += 1

    # Save failed URLs for retry
    if failed_urls:
        failed_filename = f"{state}_{city_name}_{key}_failed.csv".replace(" ", "_").lower()
        folder = state.upper()
        failed_filepath = os.path.join(folder, failed_filename)
        with open(failed_filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Url'])
            for failed_url in failed_urls:
                writer.writerow([failed_url])
        print(f"\n{len(failed_urls)} failed URLs saved to: {failed_filepath}")


# ---------------------- Script Entry -----------------------
if __name__ == "__main__":
    state = "wa"
    city_name = "aberdeen"
    key = "dental care"

    urls = read_urls_from_csv(state, city_name, key)

    if urls:
        print(f"\nTotal URLs to scrape: {len(urls)}")
        print("Starting scraper with requests library...")
        
        try:
            session = get_session(use_cloudscraper=True)
            
            # First, establish session by visiting homepage
            print("Establishing session by visiting homepage...")
            try:
                timeout = 60 if CLOUDSCRAPER_AVAILABLE else 30
                response = session.get('https://www.yellowpages.com', timeout=timeout, allow_redirects=True)
                if response.status_code == 200:
                    print("✓ Homepage loaded successfully")
                    random_delay(2, 4)
                else:
                    print(f"⚠ Homepage returned status {response.status_code}")
            except Exception as e:
                print(f"⚠ Could not load homepage: {e}")
                print("Continuing anyway...")
            
            scrape_url(urls, session, key, state, city_name, use_cloudscraper=True)
            
        except KeyboardInterrupt:
            print("\nScraping interrupted by user")
        except Exception as e:
            print(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("\nScraping completed!")
    else:
        print("No URLs found to scrape.")
