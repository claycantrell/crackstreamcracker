# Core web framework and utilities
from flask import Flask, render_template, request, jsonify  # Flask: lightweight web framework
from flask_limiter import Limiter  # Rate limiting to prevent abuse
from flask_limiter.util import get_remote_address  # Helper to get client IP for rate limiting
from bs4 import BeautifulSoup  # HTML/XML parser - easy to use for web scraping
import time  # For sleep/delays when waiting for JavaScript to execute
import os  # Operating system interface (file paths, environment variables)
import stat  # File status/permissions (used to make chromedriver executable)
import logging  # Professional logging (better than print statements)
from datetime import datetime  # Date/time handling for consent timestamp validation
from urllib.parse import urlparse  # URL parsing and validation

# Selenium: Browser automation framework (headless Chrome)
from selenium import webdriver  # Main webdriver interface
from selenium.webdriver.chrome.service import Service  # ChromeDriver service manager
from selenium.webdriver.chrome.options import Options  # Chrome configuration options
from selenium.webdriver.support.ui import WebDriverWait  # Explicit waits (better than time.sleep)
from selenium.webdriver.common.by import By  # Locator strategies (By.TAG_NAME, By.ID, etc.)
from webdriver_manager.chrome import ChromeDriverManager  # Auto-download correct ChromeDriver version

"""
APPLICATION ARCHITECTURE
========================================

┌─────────────┐         ┌──────────────┐         ┌────────────────┐
│   Browser   │  HTTP   │  Flask App   │ Selenium│ Headless Chrome│
│  (Frontend) │◄───────►│  (app.py)    │◄───────►│  (on server)   │
│             │         │              │         │                │
│  app.js     │         │  • Routes    │         │  • Loads target│
│  style.css  │         │  • Selenium  │         │  • Runs JS     │
│  index.html │         │  • BeautifulS│         │  • Extracts    │
└─────────────┘         └──────────────┘         └────────────────┘
                                │                         │
                                │                         ▼
                                │                  ┌─────────────┐
                                │                  │ Target Site │
                                │                  │ (crackstreams│
                                │                  │  .com, etc.) │
                                │                  └─────────────┘
                                │
                        ┌───────┴────────┐
                        │  JS CONSTANTS  │ ◄── These run in Headless Chrome!
                        │                │
                        │ JS_EXTRACT_*   │     NOT in user's browser
                        └────────────────┘

Key Insight: JavaScript in app.py runs on SERVER, not CLIENT!
- User never sees this JavaScript
- It runs in a Chrome instance on our server
- Used to scrape third-party sites that load content via JavaScript
"""

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

"""
Rate Limiting Setup (Important for Production!)
-------------------------------------------------
Why? Selenium is CPU/memory intensive. Without rate limits, one user could crash your server.

Learning Points:
- key_func=get_remote_address: Rate limit by client IP address
- default_limits: Global limits applied to ALL routes (unless overridden)
- storage_uri="memory://": Stores counters in RAM (fast but resets on restart)
  * In production, use Redis: storage_uri="redis://localhost:6379"
- Route-specific limits: Use @limiter.limit("5 per minute") decorator on functions
"""
limiter = Limiter(
    app=app,
    key_func=get_remote_address,  # Rate limit by IP address
    default_limits=["100 per day", "20 per hour"],  # Global limits (applies to all routes)
    storage_uri="memory://"  # In-memory storage (use Redis in production for persistence)
)

"""
JavaScript Code Injection for Selenium (SERVER-SIDE!)
------------------------------------------------------
⚠️  IMPORTANT: This JavaScript runs on the SERVER, NOT in the user's browser!

Why is JavaScript in a Python file?
====================================
1. Selenium's execute_script() injects this JS into the HEADLESS CHROME on our server
2. This code scrapes THIRD-PARTY websites (the streaming sites)
3. It executes in the context of the TARGET PAGE, not our frontend
4. Returns data back to Python, which then sends it to our frontend

Flow:
1. User requests analysis via frontend
2. Backend (this file) opens headless Chrome with Selenium
3. Selenium navigates to target URL (e.g., crackstreams.com)
4. **This JavaScript** is injected into that page's DOM
5. It extracts iframe URLs from that page's JavaScript variables
6. Data returns to Python → Python sends to frontend

Why not just use BeautifulSoup?
================================
Some sites load iframes dynamically with JavaScript AFTER initial page load.
BeautifulSoup only sees the initial HTML. Selenium + injected JS sees the live DOM.

This script finds stream links 3 ways:
1. Button onclick handlers (common pattern on streaming sites)
2. JavaScript variables (like "allStreams" array on CrackStreams)
3. Regex pattern matching in <script> tags
"""
JS_EXTRACT_STREAM_LINKS = """
var links = [];

// Method 1: Look for stream link buttons
var buttons = document.querySelectorAll('button, a, div[onclick], span[onclick], li[onclick], .link-button, .stream-link');
for(var i = 0; i < buttons.length; i++) {
    var elem = buttons[i];
    var text = elem.textContent.toLowerCase();
    // Check if it's a stream link button
    if (text.includes('link') || text.includes('hd') || text.includes('server') || text.match(/link[\\s-]*\\d/)) {
        // Try to extract the stream URL from onclick or data attributes
        var onclick = elem.getAttribute('onclick') || '';
        var dataUrl = elem.getAttribute('data-url') || elem.getAttribute('data-src') || elem.getAttribute('data-stream') || '';
        
        // Look for URLs in onclick handlers
        var urlMatch = onclick.match(/https?:\\/\\/[^\\s'"\\)]+/);
        if (urlMatch) {
            links.push({
                label: elem.textContent.trim(),
                url: urlMatch[0]
            });
        } else if (dataUrl) {
            links.push({
                label: elem.textContent.trim(),
                url: dataUrl
            });
        }
    }
}

// Method 2: Look for the allStreams JavaScript variable (CrackStreams specific)
var scripts = document.getElementsByTagName('script');
for (var i = 0; i < scripts.length; i++) {
    var scriptText = scripts[i].textContent;
    if (scriptText && scriptText.includes('allStreams')) {
        // Try to extract the allStreams array
        var allStreamsMatch = scriptText.match(/const\\s+allStreams\\s*=\\s*(\\[.*?\\]);/s);
        if (allStreamsMatch) {
            try {
                var allStreamsData = JSON.parse(allStreamsMatch[1]);
                allStreamsData.forEach(function(stream) {
                    if (stream.value && stream.label) {
                        links.push({
                            label: stream.label,
                            url: stream.value
                        });
                    }
                });
            } catch(e) {
                console.error('Failed to parse allStreams:', e);
            }
        }
    }
}

// Method 3: Look for other player URLs in JavaScript
for (var i = 0; i < scripts.length; i++) {
    var scriptText = scripts[i].textContent;
    if (scriptText) {
        // Look for player URLs in script
        var playerMatches = scriptText.match(/https?:\\/\\/[^\\s'"\\)]+player[^\\s'"\\)]*channel=[\\d]+/g);
        if (playerMatches) {
            playerMatches.forEach(function(url, idx) {
                // Check if not already in links
                if (!links.some(l => l.url === url)) {
                    links.push({
                        label: 'Server ' + (links.length + 1),
                        url: url
                    });
                }
            });
        }
    }
}

return links;
"""

"""
Simple iframe extractor (gets live src attributes from target page)
--------------------------------------------------------------------
⚠️  Executes on SERVER in headless Chrome, NOT in user's browser!

Why? Sometimes iframe src is set by JavaScript AFTER page load,
so we need to read the LIVE DOM (after JS executes), not the initial HTML.

Alternative approaches we're NOT using:
- BeautifulSoup alone: Only sees initial HTML (misses JS-loaded iframes)
- Frontend scraping: Can't access third-party pages due to CORS
- This approach: Server-side browser with JS execution ✅
"""
JS_EXTRACT_IFRAMES = """
var iframes = document.getElementsByTagName('iframe');
var results = [];
for(var i = 0; i < iframes.length; i++) {
    results.push({
        src: iframes[i].src,
        id: iframes[i].id,
        className: iframes[i].className
    });
}
return results;
"""

def get_selenium_driver():
    """Initialize a headless Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Performance optimizations
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-images')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    chrome_options.page_load_strategy = 'eager'  # Don't wait for all resources
    
    # Block popups and ads
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--block-new-web-contents')
    chrome_options.add_experimental_option('prefs', {
        'profile.default_content_setting_values.notifications': 2,
        'profile.default_content_setting_values.popups': 2,
        'profile.default_content_setting_values.automatic_downloads': 2
    })
    
    # Check if we're in production (Docker/Render) - use system Chrome
    if os.environ.get('CHROME_BIN') or os.path.exists('/usr/bin/chromium'):
        # Production: use system Chrome/ChromeDriver
        chrome_options.binary_location = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
        driver_path = os.environ.get('CHROMEDRIVER_BIN', '/usr/bin/chromedriver')
    else:
        # Local development: use webdriver-manager
        driver_path = ChromeDriverManager().install()
        # The path might point to wrong file, so fix it
        if driver_path and ('THIRD_PARTY_NOTICES' in driver_path or 'LICENSE' in driver_path):
            driver_dir = os.path.dirname(driver_path)
            driver_path = os.path.join(driver_dir, 'chromedriver')
        
        # Ensure chromedriver has execute permissions
        if driver_path and os.path.exists(driver_path):
            os.chmod(driver_path, os.stat(driver_path).st_mode | stat.S_IEXEC)
    
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204  # No Content - suppress the 404

@app.route('/extract', methods=['POST'])
@limiter.limit("5 per minute")  # Max 5 extractions per minute per IP
def extract_stream():
    """
    Extract iframe URLs from a given webpage using Selenium.
    
    Why we create a new driver per request:
    - Session isolation: Each user gets a fresh browser state (no cookies/cache from others)
    - Memory safety: Prevents memory leaks from long-running Selenium instances
    - Error recovery: If one request crashes the driver, others aren't affected
    - Simplicity: No need for connection pooling logic (good for teaching basics)
    
    Trade-off: Slower (1-2s driver startup overhead), but more reliable for beginners.
    In production, consider using a driver pool or service like Selenium Grid.
    """
    driver = None
    try:
        data = request.get_json()
        url = data.get('url', '')
        consent = data.get('consent', {})
        
        # Validate consent
        if not consent.get('given') or not consent.get('timestamp'):
            return jsonify({'error': 'You must agree to the terms before using this service'}), 403
        
        # Validate timestamp format (ISO 8601)
        try:
            timestamp = consent.get('timestamp')
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # Parse ISO format
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid consent timestamp format: {timestamp}")
            return jsonify({'error': 'Invalid consent timestamp format'}), 400
        
        # Log consent for audit trail (in production, store in database)
        # Note: IP is available from request.remote_addr but we're not logging it
        # For production: Add IP logging for complete audit trail
        # Example: logger.info(f"CONSENT: IP={request.remote_addr} timestamp={timestamp} url={url}")
        logger.info(f"CONSENT: User accepted terms at {timestamp} for URL: {url}")
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate URL security (only allow http/https)
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme not in ['http', 'https']:
                return jsonify({'error': f'Invalid URL scheme: {parsed_url.scheme}. Only http/https allowed.'}), 400
            if not parsed_url.netloc:
                return jsonify({'error': 'Invalid URL: missing hostname'}), 400
        except Exception as e:
            return jsonify({'error': f'Invalid URL format: {str(e)}'}), 400
        
        # Initialize Selenium driver
        driver = get_selenium_driver()
        driver.set_page_load_timeout(10)
        driver.get(url)
        
        # Smart wait: Wait for iframes to appear (usually 3-5 seconds for streaming sites)
        iframe_wait = 8
        try:
            # Wait for at least one iframe or specific elements to load
            WebDriverWait(driver, iframe_wait).until(
                lambda d: len(d.find_elements(By.TAG_NAME, 'iframe')) > 0 or
                         len(d.find_elements(By.TAG_NAME, 'script')) > 5
            )
            # Give JS a moment to populate iframe sources
            time.sleep(2)
        except Exception as e:
            # Fallback if no iframes detected quickly
            logger.info(f"No iframes found quickly, using fallback wait: {e}")
            time.sleep(5)
        
        # Ensure page scripts have executed
        try:
            WebDriverWait(driver, 3).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except Exception as e:
            pass
        
        # Get the fully rendered page source
        page_source = driver.page_source
        
        # Extract iframe src from JavaScript execution
        try:
            iframes_from_js = driver.execute_script(JS_EXTRACT_IFRAMES)
        except Exception as e:
            logger.warning(f"Failed to extract iframes via JavaScript: {e}")
            iframes_from_js = []
        
        # Look for stream link buttons (Link-1 HD, Link-2 HD, etc.) and extract ALL player iframes
        stream_links = []
        try:
            stream_links = driver.execute_script(JS_EXTRACT_STREAM_LINKS)
        except Exception as e:
            logger.warning(f"Failed to extract stream links: {e}")
            stream_links = []
        
        """
        Data Extraction Phase
        ---------------------
        Now we parse the HTML and extract iframes from multiple sources.
        """
        
        # Parse HTML with BeautifulSoup
        # html5lib parser: slower but handles malformed HTML gracefully (common on streaming sites)
        # Alternative parsers: 'lxml' (faster) or 'html.parser' (built-in)
        soup = BeautifulSoup(page_source, 'html5lib')
        
        # Extract all iframes from static HTML
        # This catches iframes that were in the original HTML
        iframes = []
        for iframe in soup.find_all('iframe'):
            # Extract attributes into a dictionary
            iframe_data = {
                'src': iframe.get('src', ''),  # iframe.get() returns None if attribute missing
                'width': iframe.get('width', '100%'),
                'height': iframe.get('height', '500'),
                'allowfullscreen': iframe.get('allowfullscreen') is not None  # Boolean check
            }
            # Only include iframes that have a source URL
            if iframe_data['src']:
                iframes.append(iframe_data)
        
        """
        Data Merging Phase (Complex but Important!)
        --------------------------------------------
        Problem: We have iframes from 3 sources:
        1. Static HTML (BeautifulSoup) - iframes in initial page load
        2. Live DOM (Selenium JS) - iframes added by JavaScript after page load
        3. Stream link buttons (Selenium JS) - URLs hidden in onclick handlers
        
        Goal: Combine all sources without duplicates, and add labels where available.
        
        Learning Points:
        - Dictionary comprehension: {key: value for item in list}
        - Set for deduplication: Fast O(1) lookup to check if URL already seen
        - .get() method: Safe dictionary access (returns None if key missing, no KeyError)
        """
        
        # Step 1: Create a URL → label mapping (dictionary comprehension)
        # Example: {'https://player.com/123': 'Link 1 HD', 'https://player.com/456': 'Link 2 HD'}
        url_to_label = {link['url']: link['label'] for link in stream_links if link.get('url') and link.get('label')}
        
        # Step 2: Apply labels to existing iframes (if they have matching URLs)
        for iframe in iframes:
            if iframe['src'] in url_to_label:
                iframe['label'] = url_to_label[iframe['src']]
        
        # Step 3: Merge JavaScript-extracted iframes (avoid duplicates using set)
        # Sets provide O(1) lookup time (fast!) vs lists which are O(n)
        all_iframe_srcs = set([i['src'] for i in iframes if i['src']])  # List → Set conversion
        
        for js_iframe in iframes_from_js:
            # Only add if not already in our list (no duplicates!)
            if js_iframe['src'] and js_iframe['src'] not in all_iframe_srcs:
                label = url_to_label.get(js_iframe['src'])  # Get label if it exists
                iframes.append({
                    'src': js_iframe['src'],
                    'width': '100%',
                    'height': '600',
                    'allowfullscreen': True,
                    'label': label  # May be None (that's OK)
                })
                all_iframe_srcs.add(js_iframe['src'])  # Add to set to track it
        
        # Step 4: Add stream link URLs as iframe options (if not already present)
        # These are URLs we found in button onclick handlers
        for link in stream_links:
            if link['url'] and link['url'] not in all_iframe_srcs:
                iframes.append({
                    'src': link['url'],
                    'width': '100%',
                    'height': '600',
                    'allowfullscreen': True,
                    'label': link['label']
                })
                all_iframe_srcs.add(link['url'])
        
        # Extract page title for display
        title = soup.find('title')  # Returns None if no <title> tag found
        page_title = title.text if title else 'Stream'  # Ternary operator: condition ? true : false
        
        # Check if we found any iframes (if not, offer linked pages)
        if not iframes or len(iframes) == 0:
            logger.warning(f"No iframes found on URL: {url}")
            
            # Extract links from the page for user to choose from
            # Only show links from the same domain (safety)
            domain = parsed_url.netloc
            links_found = []
            
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').strip()
                link_text = link.get_text().strip()
                
                # Skip empty, anchor, or javascript links
                if not href or href.startswith('#') or href.startswith('javascript:'):
                    continue
                
                # Make absolute URL
                if href.startswith('/'):
                    href = f"{parsed_url.scheme}://{domain}{href}"
                elif not href.startswith('http'):
                    continue
                
                # Only same domain (security - don't link to other sites)
                try:
                    link_domain = urlparse(href).netloc
                    if domain not in link_domain:
                        continue
                except:
                    continue
                
                # Skip if same as current URL
                if href == url:
                    continue
                
                # Add to list (with fallback title)
                links_found.append({
                    'url': href,
                    'title': link_text if link_text else href
                })
            
            # Remove duplicates (same URL)
            seen_urls = set()
            unique_links = []
            for link in links_found:
                if link['url'] not in seen_urls:
                    seen_urls.add(link['url'])
                    unique_links.append(link)
            
            return jsonify({
                'error': 'no_iframes',
                'message': 'No video players (iframes) detected on this page.',
                'help': 'This tool analyzes pages that contain embedded video players. Make sure the URL you entered has a visible video player embedded in it. If you see a player when you visit the page in your browser, but this tool says none found, the page may use JavaScript that blocks automated analysis.',
                'links': unique_links[:50]  # Limit to 50 links max
            }), 404
        
        # Build JSON response
        # jsonify() automatically converts Python dict → JSON and sets Content-Type header
        result = {
            'success': True,
            'title': page_title,
            'iframes': iframes  # List of iframe dictionaries
        }
        
        return jsonify(result)  # Returns HTTP 200 with JSON body
        
    except Exception as e:
        return jsonify({'error': f'Failed to extract stream: {str(e)}'}), 500
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    # Use environment variable for debug mode (never True in production!)
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=debug_mode, port=port, host='0.0.0.0')
