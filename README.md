# Stream Iframe Extractor

**Educational Tool for Learning Web Scraping, Selenium & Flask Development**

A local web application demonstrating server-side rendering and iframe extraction from JavaScript-heavy webpages using Python, Selenium, and BeautifulSoup. This project teaches full-stack web development, browser automation, and responsible web scraping practices.

See it in action here: https://stream-iframe-extractor.onrender.com/

## ⚖️ Legal Disclaimer

**FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY**

This tool is designed to teach:
- Server-side web scraping with Selenium
- Handling dynamically-loaded content
- Flask API development
- Responsive web design (mobile-first)
- User consent management

**Users must:**
- Only analyze content they own or have legal permission to access
- Comply with all applicable copyright laws and website terms of service
- Not circumvent access controls, DRM, or technical protection measures
- Accept terms via click-through consent before using the tool

This tool uses **server-side rendering** to extract iframe URLs from publicly accessible pages. It does **not** host, cache, or redistribute third-party content or copyrighted material.

## Features

- 🎨 **Mobile-First Responsive Design** - Optimized for phones, tablets, and desktop
- ⚖️ **Legal Consent Workflow** - Required click-through agreement before use
- ⚡ **Smart Performance** - Intelligent iframe detection (2-8s vs old 12s fixed delay)
- 🔍 **Server-Side Rendering** - Selenium-powered JavaScript execution
- 🎬 **Multiple Stream Detection** - Finds all embedded players on a page
- 🛡️ **Client-Side Security** - Popup blocking and sandboxed iframes
- 📱 **Separated Concerns** - External CSS file for maintainability

## Quick Start (Local Development)

### Prerequisites
- **Python 3.8+** - [Download here](https://www.python.org/downloads/)
- **Google Chrome** - Required for Selenium WebDriver

### Installation Steps

1. **Clone the repository:**
```bash
git clone https://github.com/claycantrell/crackstreamcracker.git
cd crackstreamcracker
```

2. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the application:**
```bash
python app.py
```

5. **Access the app:**
Open your browser to: **http://localhost:5001**

### Using the App

1. **Accept Terms** - Check the consent box to agree to legal terms
2. **Enter URL** - Paste a webpage URL containing embedded players
3. **Analyze** - Click "I Agree—Analyze Page" (takes 2-8 seconds)
4. **View Results** - See extracted iframe URLs with options to:
   - Open in new tab
   - Copy URL to clipboard
   - Switch between multiple detected streams

## How It Works

### Architecture Overview

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Browser   │ ───> │ Flask Server │ ───> │   Selenium  │
│  (Client)   │ <─── │   (Backend)  │ <─── │  (Headless  │
└─────────────┘      └──────────────┘      │   Chrome)   │
                                            └─────────────┘
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │ Target Site │
                                            │ (Analyzed)  │
                                            └─────────────┘
```

### Request Flow

1. **User submits URL** → Frontend validates consent checkbox
2. **POST /extract** → Flask receives URL + consent timestamp
3. **Selenium launches** → Headless Chrome starts with performance optimizations
4. **Page loads** → Smart wait for iframes (2-8s) instead of fixed delay
5. **JavaScript executes** → Full page rendering including dynamic iframes
6. **DOM analysis** → BeautifulSoup + Selenium extract iframe elements
7. **Pattern matching** → Identifies player vs chat vs ad iframes
8. **JSON response** → Returns iframe URLs, labels, and metadata
9. **Frontend displays** → Renders results with action buttons

### Key Concepts Demonstrated

**1. Server-Side Web Scraping**
- Bypasses CORS and X-Frame-Options restrictions (controversial!)
- Executes JavaScript to find dynamically-loaded content
- Not blocked by client-side protections

**2. Smart Performance Optimization**
```python

WebDriverWait(driver, 8).until(
    lambda d: len(d.find_elements(By.TAG_NAME, 'iframe')) > 0
)
```

**3. Mobile-First CSS**
- Base styles for mobile (< 768px)
- Progressive enhancement for tablets/desktop
- External CSS file for better caching

**4. Consent Management**
- Client-side checkbox validation
- Server-side consent logging
- Timestamps recorded for audit trail

## Project Structure

```
crackstreamcracker/
├── app.py                 # Flask server & Selenium logic
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main UI (610 lines, no inline CSS)
├── static/
│   └── style.css         # Mobile-first responsive styles
├── Dockerfile            # Container deployment config
├── railway.toml          # Railway deployment settings
└── README.md             # This file
```

### File Breakdown

#### **`app.py`** - Backend Logic (289 lines)
The Flask server that handles all backend operations.

**Key Functions:**
- `get_selenium_driver()` - Configures headless Chrome with performance optimizations
  - Disables images/extensions for speed
  - Sets `page_load_strategy = 'eager'`
  - Returns configured WebDriver instance

- `@app.route('/extract', methods=['POST'])` - Main API endpoint
  1. Validates user consent (403 if missing)
  2. Launches Selenium to load target page
  3. Smart-waits for iframes (2-8s)
  4. Executes JavaScript to find all iframes + stream links
  5. Parses HTML with BeautifulSoup
  6. Returns JSON with iframe data

**Learning Points:**
- Flask routing and JSON APIs
- Selenium WebDriver configuration
- Smart waiting strategies (avoid fixed delays!)
- Error handling and cleanup (`finally: driver.quit()`)

#### **`templates/index.html`** - Frontend (610 lines)
The single-page application interface.

**Key Sections:**
- **Legal Terms** (lines 11-37) - Required consent agreement
- **Input Form** (lines 39-56) - URL input + consent checkbox
- **Results Display** (lines 65-85) - Dynamic iframe cards
- **JavaScript** (lines 530-610) - Client-side logic

**JavaScript Functions:**
- `handleConsentChange()` - Enables/disables analyze button
- `extractStream()` - Sends POST request to `/extract` API
- `displayStream()` - Renders iframe results
- `loadIframe()` - Handles specific stream player loading

**Learning Points:**
- Progressive enhancement (works without JS for basic HTML)
- Event-driven UI updates
- Fetch API for AJAX requests
- DOM manipulation

#### **`static/style.css`** - Styles (383 lines)
Mobile-first responsive CSS separated from HTML.

**Structure:**
- Lines 1-237: Base mobile styles (< 768px)
- Lines 239-304: Tablet styles (@media min-width: 768px)
- Lines 306-373: Desktop styles (@media min-width: 1024px)
- Lines 375-388: Additional mobile optimizations

**Learning Points:**
- Mobile-first methodology (start small, scale up)
- CSS custom properties for consistency
- Responsive breakpoints
- Performance (external CSS = browser caching)

#### **`requirements.txt`** - Dependencies
```
flask==3.0.0           # Web framework
selenium==4.15.2       # Browser automation
beautifulsoup4==4.12.2 # HTML parsing
html5lib==1.1          # HTML5 parser
requests==2.31.0       # HTTP library
webdriver-manager==4.0.1 # Auto-manage ChromeDriver
python-dotenv==1.1.1   # Environment variables
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Flask 3.0 | Web framework & routing |
| **Browser Automation** | Selenium 4.15 | Headless Chrome control |
| **HTML Parsing** | BeautifulSoup4 | DOM traversal & extraction |
| **Driver Management** | webdriver-manager | Auto-download ChromeDriver |
| **Frontend** | Vanilla JS | No frameworks (educational simplicity) |
| **Styling** | CSS3 | Mobile-first responsive design |
| **Deployment** | Docker + Railway/Render | Container orchestration |

## What You'll Learn

### Backend Development
✅ **Flask API Design** - RESTful endpoints, JSON responses, error handling  
✅ **Selenium WebDriver** - Headless browser automation, smart waiting strategies  
✅ **Web Scraping** - HTML parsing, iframe extraction, pattern matching  
✅ **Performance Optimization** - Conditional waits vs fixed delays (60% speed improvement)

### Frontend Development  
✅ **Mobile-First CSS** - Responsive breakpoints, media queries, progressive enhancement  
✅ **Vanilla JavaScript** - Fetch API, DOM manipulation, event handling (no frameworks!)  
✅ **User Consent Flow** - Click-through agreements, form validation, audit logging  
✅ **Separation of Concerns** - External CSS, semantic HTML, modular JS

### DevOps & Deployment
✅ **Containerization** - Dockerfile for consistent environments  
✅ **Environment Management** - Virtual environments, dependency management  
✅ **Version Control** - Git workflow, meaningful commits

### Security & Ethics
✅ **Legal Compliance** - Terms of service, user agreements, consent logging  
✅ **Rate Limiting** - Respecting server resources  
✅ **Responsible Scraping** - Understanding when NOT to scrape

## Important Limitations

### Technical Constraints
- ⚠️ **Server-Side Approach** - This tool bypasses client-side security (CORS, X-Frame-Options). This is powerful but legally risky.
- ⚠️ **No DRM Bypass** - Does not defeat encrypted streams, tokens, or authentication
- ⚠️ **Static Analysis Only** - Cannot handle WebSocket connections or WebRTC streams
- ⚠️ **Rate Limited** - Selenium is slow; don't use for bulk scraping

### Legal Considerations
- ⚠️ **High Legal Risk** - Server-side scraping can violate CFAA, DMCA, and ToS
- ⚠️ **Copyright** - Extracting copyrighted content may be illegal in your jurisdiction
- ⚠️ **No Warranty** - Provided "as is" for educational purposes only
- ⚠️ **Your Responsibility** - Users liable for their own actions

### Ethical Usage
- ✅ Only use on sites you own or have written permission to scrape
- ✅ Respect `robots.txt` and rate limits
- ✅ Don't circumvent paywalls, logins, or access controls
- ✅ Understand the difference between legal/illegal scraping

## Performance Metrics

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Page Analysis | 12s fixed | 2-8s smart wait | ~60% faster |
| Chrome Startup | Standard | Disabled images/extensions | ~30% faster |
| Iframe Detection | Blind wait | Conditional check | Exits early |
| Repeat Page Loads | No caching | External CSS cached | Faster UX |

## Common Issues & Solutions

### `ModuleNotFoundError: No module named 'flask'`
**Solution:** Activate virtual environment first
```bash
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### `selenium.common.exceptions.WebDriverException: chrome not reachable`
**Solution:** Install Google Chrome browser (not just ChromeDriver)

### Slow analysis (>10 seconds)
**Cause:** Site has slow-loading JavaScript  
**Solution:** Reduce `iframe_wait` in `app.py` line 87 from 8 to 5

### "You must agree to terms" error even when checked
**Cause:** JavaScript disabled or browser blocking cookies  
**Solution:** Enable JavaScript and check browser console for errors

## Further Reading

**Web Scraping Ethics:**
- [Robots.txt specification](https://www.robotstxt.org/)
- [Is Web Scraping Legal? (2024 Guide)](https://www.scrapehero.com/is-web-scraping-legal/)

**Technical Learning:**
- [Selenium Python Documentation](https://selenium-python.readthedocs.io/)
- [Flask Quickstart](https://flask.palletsprojects.com/en/3.0.x/quickstart/)
- [Mobile-First CSS](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Responsive/Mobile_first)

## License

MIT License - See LICENSE file for details.

**Educational Use Only** - This code demonstrates web scraping techniques. Commercial use or misuse for illegal activities is strictly prohibited.

## Final Disclaimer

⚠️ **This tool uses server-side rendering to bypass client-side security measures. This approach carries legal risks including potential violations of:**
- Computer Fraud and Abuse Act (CFAA)
- Digital Millennium Copyright Act (DMCA)
- Website Terms of Service
- Copyright law

**You are solely responsible for ensuring your usage complies with all applicable laws.** The developers provide this code for educational purposes and disclaim all liability for misuse.
