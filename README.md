# Stream Iframe Extractor

**Educational Tool for Learning Web Scraping & Iframe Analysis**

A local web application that demonstrates how to analyze and extract embedded iframe players from web pages using Python, Selenium, and BeautifulSoup.

See it in action here: https://stream-iframe-extractor.onrender.com/

## ⚖️ Legal Disclaimer

**FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY**

This tool is designed to teach web scraping techniques, iframe extraction, and client-side security concepts. Users must:
- Only analyze content they own or have permission to access
- Comply with all applicable copyright laws and website terms of service
- Not use this tool to circumvent DRM or access control measures
- Understand they are responsible for their own usage

This tool does **not** host, store, or distribute any content—it only analyzes webpage structure.

## Features

- 🔍 Analyze webpage structure to find embedded iframes
- 🎬 Extract multiple stream player options from a page
- 🛡️ Built-in popup blocker and security features
- 🎨 Clean, modern UI with gradient design
- 📊 Display iframe metadata and technical information
- 🔧 JavaScript-rendered content support via Selenium

## Installation

### Prerequisites
- Python 3.8+
- Chrome browser (for Selenium)

### Steps

1. **Clone the repository:**
```bash
git clone <repo-url>
cd crackstreamcracker
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate  # On Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Usage

1. **Start the Flask server:**
```bash
python app.py
```

2. **Open your browser:**
Navigate to: `http://localhost:5001`

3. **Analyze a webpage:**
   - Enter any webpage URL containing embedded iframe players
   - Click "Analyze Page" to extract technical details
   - Review iframe sources, dimensions, and metadata

4. **View results:**
   - See all detected iframes with labels (player, chat, ads)
   - Technical info: dimensions, sandbox attributes, sources
   - Option to open iframes in new tabs for testing

## How It Works (Educational Overview)

This tool demonstrates several web scraping concepts:

1. **HTTP Requests**: Fetches webpage HTML using Python's `requests` library
2. **JavaScript Rendering**: Uses Selenium WebDriver to render JavaScript-heavy pages
3. **DOM Parsing**: BeautifulSoup parses HTML to find iframe elements
4. **Pattern Recognition**: Identifies different types of iframes (players vs ads vs chat)
5. **Metadata Extraction**: Extracts iframe attributes (src, dimensions, sandbox rules)
6. **Client-Side Security**: Implements popup blocking and security best practices

### Technical Flow

```
User Input (URL) → Selenium (headless Chrome) → Page Render (12s wait)
    ↓
BeautifulSoup HTML Parsing → Iframe Detection → JavaScript Analysis
    ↓
Pattern Matching (player/chat/ads) → Metadata Extraction
    ↓
Flask API Response → Frontend Display
```

## Tech Stack

- **Backend**: Python 3.8+, Flask
- **Web Scraping**: Selenium WebDriver, BeautifulSoup4, html5lib
- **Browser Automation**: ChromeDriver (via webdriver-manager)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Security**: Sandboxed iframes, popup blocking, referrer policies

## Learning Objectives

This project teaches:
- ✅ Web scraping with Python
- ✅ Handling JavaScript-rendered content with Selenium
- ✅ HTML parsing with BeautifulSoup
- ✅ RESTful API design with Flask
- ✅ Client-side security best practices
- ✅ Cross-origin restrictions (CORS, Same-Origin Policy)
- ✅ Iframe sandboxing and permissions

## Limitations & Considerations

- **Same-Origin Policy**: Cannot modify cross-origin iframe content
- **Dynamic Content**: Some sites use WebSocket/WebRTC that can't be easily extracted
- **Anti-Scraping**: Many sites have protections against automated access
- **Rate Limiting**: Respect robots.txt and rate limits
- **Legal**: Only use on content you have permission to analyze

## Contributing

This is an educational project. Contributions that improve the learning experience are welcome:
- Better documentation of scraping techniques
- Additional security examples
- Performance optimizations
- Code comments explaining concepts

## License

MIT License - For educational use only

## Disclaimer

The developers are not responsible for misuse of this tool. Users must comply with all applicable laws, including copyright law and website terms of service. This tool is provided "as is" without warranties of any kind.
