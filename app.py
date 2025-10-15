from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
import time
import os
import stat
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

def get_selenium_driver():
    """Initialize a headless Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
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
def extract_stream():
    driver = None
    try:
        data = request.get_json()
        url = data.get('url', '')
        consent = data.get('consent', {})
        
        # Validate consent
        if not consent.get('given') or not consent.get('timestamp'):
            return jsonify({'error': 'You must agree to the terms before using this service'}), 403
        
        # Log consent for audit trail (in production, store in database)
        print(f"[CONSENT] User accepted terms at {consent.get('timestamp')} for URL: {url}")
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Initialize Selenium driver
        driver = get_selenium_driver()
        driver.get(url)
        
        # Wait for JavaScript to load
        time.sleep(12)
        
        # Wait for page to be fully loaded
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except Exception as e:
            pass
        
        # Get the fully rendered page source
        page_source = driver.page_source
        
        # Extract iframe src from JavaScript execution
        try:
            iframes_from_js = driver.execute_script("""
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
            """)
        except:
            iframes_from_js = []
        
        # Look for stream link buttons (Link-1 HD, Link-2 HD, etc.) and extract ALL player iframes
        stream_links = []
        try:
            stream_links = driver.execute_script("""
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
            """)
        except Exception as e:
            stream_links = []
        
        # Parse HTML
        soup = BeautifulSoup(page_source, 'html5lib')
        
        # Extract all iframes
        iframes = []
        for iframe in soup.find_all('iframe'):
            iframe_data = {
                'src': iframe.get('src', ''),
                'width': iframe.get('width', '100%'),
                'height': iframe.get('height', '500'),
                'allowfullscreen': iframe.get('allowfullscreen') is not None
            }
            if iframe_data['src']:
                iframes.append(iframe_data)
        
        # Create a URL -> label mapping from stream_links
        url_to_label = {link['url']: link['label'] for link in stream_links if link.get('url') and link.get('label')}
        
        # Apply labels to existing iframes
        for iframe in iframes:
            if iframe['src'] in url_to_label:
                iframe['label'] = url_to_label[iframe['src']]
        
        # Merge iframes from both sources
        all_iframe_srcs = set([i['src'] for i in iframes if i['src']])
        for js_iframe in iframes_from_js:
            if js_iframe['src'] and js_iframe['src'] not in all_iframe_srcs:
                # Check if this iframe has a label
                label = url_to_label.get(js_iframe['src'])
                iframes.append({
                    'src': js_iframe['src'],
                    'width': '100%',
                    'height': '600',
                    'allowfullscreen': True,
                    'label': label  # May be None
                })
                all_iframe_srcs.add(js_iframe['src'])
        
        # Add stream links as additional iframe options (if not already present)
        for link in stream_links:
            if link['url'] and link['url'] not in all_iframe_srcs:
                iframes.append({
                    'src': link['url'],
                    'width': '100%',
                    'height': '600',
                    'allowfullscreen': True,
                    'label': link['label']  # Add label for display
                })
                all_iframe_srcs.add(link['url'])
        
        # Get page title
        title = soup.find('title')
        page_title = title.text if title else 'Stream'
        
        result = {
            'success': True,
            'title': page_title,
            'iframes': iframes
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Failed to extract stream: {str(e)}'}), 500
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port, host='0.0.0.0')
