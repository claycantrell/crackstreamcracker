/*
 * ====================================================================================
 * CONSENT TRACKING SYSTEM
 * ====================================================================================
 * Why? Legal requirement for tools that access third-party content.
 * Tracks user consent before allowing any scraping operations.
 * 
 * Learning Points:
 * - Global variables: Accessible from any function in this file
 * - let vs const: 'let' allows reassignment, 'const' does not
 * - ISO 8601 timestamps: Standard format for dates (2024-01-15T10:30:00.000Z)
 */

// Global state variables (accessed by multiple functions)
let consentGiven = false;         // Boolean flag: has user agreed to terms?
let consentTimestamp = null;      // ISO timestamp: when did user consent?

/**
 * Handle checkbox state change
 * Called when user checks/unchecks the consent checkbox
 * 
 * Learning: DOM manipulation basics
 * - getElementById(): Get element by its id attribute
 * - .checked: Boolean property of checkbox elements
 * - .disabled: Boolean property to enable/disable buttons
 * - .style: Access CSS properties via JavaScript
 */
function handleConsentChange() {
    const checkbox = document.getElementById('consentCheckbox');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (checkbox.checked) {
        // User agreed to terms
        consentGiven = true;
        consentTimestamp = new Date().toISOString();  // Generate ISO 8601 timestamp
        
        // Enable the button (UI feedback)
        analyzeBtn.disabled = false;
        analyzeBtn.style.opacity = '1';
        analyzeBtn.style.cursor = 'pointer';
        
        // Log consent for debugging (in production, send to server database)
        console.log('User consent recorded:', {
            timestamp: consentTimestamp,
            userAgent: navigator.userAgent,  // Browser info for audit trail
        });
    } else {
        // User revoked consent
        consentGiven = false;
        consentTimestamp = null;
        
        // Disable the button
        analyzeBtn.disabled = true;
        analyzeBtn.style.opacity = '0.5';
        analyzeBtn.style.cursor = 'not-allowed';
    }
}

// Safe Block Monitor - Initialize FIRST before anything else
const BlockMonitor = {
    count: 0,
    maxEntries: 30,
    
    log: function(type, url) {
        try {
            // Safety checks - only proceed if elements exist
            const monitor = document.getElementById('blockMonitor');
            const list = document.getElementById('blockList');
            const counter = document.getElementById('blockCount');
            
            if (!monitor || !list || !counter) {
                console.warn('BlockMonitor: Elements not ready yet');
                return;
            }
            
            // Show monitor on first block
            if (monitor.style.display === 'none') {
                monitor.style.display = 'block';
            }
            
            // Increment count
            this.count++;
            counter.textContent = this.count;
            
            // Determine icon and color based on type
            let icon = '🚫';
            let color = '#e74c3c';
            let label = type || 'Blocked';
            
            if (url && typeof url === 'string') {
                if (url.includes('ad') || url.includes('banner')) {
                    icon = '🎯';
                    color = '#e67e22';
                    label = 'Ad';
                } else if (url.includes('track') || url.includes('analytic')) {
                    icon = '📊';
                    color = '#f1c40f';
                    label = 'Tracker';
                }
            }
            
            if (type === 'popup' || type === 'popunder') {
                icon = '🚫';
                color = '#e74c3c';
                label = 'Popup';
            }
            
            // Create entry
            const time = new Date().toLocaleTimeString();
            const shortUrl = url && typeof url === 'string' 
                ? (url.length > 60 ? url.substring(0, 60) + '...' : url) 
                : 'Unknown';
            
            const entry = document.createElement('div');
            entry.style.cssText = `
                margin-bottom: 6px; 
                padding: 10px 12px; 
                background: #ffffff; 
                border-radius: 8px; 
                border-left: 3px solid ${color};
                color: #1d1d1f;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
            `;
            entry.innerHTML = `
                <span style="color: ${color}; font-weight: 600; font-size: 14px;">${icon} ${label}</span> 
                <span style="color: #86868b; font-size: 12px; margin-left: 8px;">${time}</span>
                <div style="color: #86868b; font-size: 12px; margin-top: 4px; word-break: break-all; font-family: 'SF Mono', Monaco, monospace;">${shortUrl}</div>
            `;
            
            // Add to top of list
            list.insertBefore(entry, list.firstChild);
            
            // Limit entries
            while (list.children.length > this.maxEntries) {
                list.removeChild(list.lastChild);
            }
        } catch (e) {
            // Silently fail - don't break the app
            console.error('BlockMonitor error (non-fatal):', e);
        }
    }
};

// Safe clear function
function clearBlockMonitor() {
    try {
        const list = document.getElementById('blockList');
        const counter = document.getElementById('blockCount');
        
        if (list) list.innerHTML = '<div style="color: #86868b;">Monitoring for blocked requests...</div>';
        if (counter) counter.textContent = '0';
        
        BlockMonitor.count = 0;
    } catch (e) {
        console.error('Clear monitor error (non-fatal):', e);
    }
}

/*
 * ====================================================================================
 * GLOBAL POPUP & AD BLOCKER
 * ====================================================================================
 * Advanced Pattern: IIFE (Immediately Invoked Function Expression)
 * 
 * What's an IIFE? (function() { ... })();
 * - Function that runs immediately when defined
 * - Creates private scope (variables inside don't pollute global namespace)
 * - Pattern: (function() { code here })();  ← notice the () at the end
 * 
 * Why use IIFE here?
 * - Run setup code immediately on page load
 * - Keep variables like 'originalOpen' and 'observer' private
 * - Prevent conflicts with other scripts
 * 
 * Learning: Advanced JavaScript patterns used in production code
 */
(function() {
    /* 
     * METHOD 1: Block window.open() popups
     * =====================================
     * Technique: Function hijacking (override native browser function)
     * - Save reference to original window.open
     * - Replace it with our own function that logs & blocks
     * - Return null instead of opening window
     */
    const originalOpen = window.open;  // Save original function
    window.open = function(url, name, specs) {
        console.log('Blocked popup attempt:', url);
        // Log to monitor (safe try-catch so blocking never breaks)
        try {
            BlockMonitor.log('popup', url);
        } catch (e) {
            console.error('Monitor log failed (non-fatal):', e);
        }
        return null;  // Block the popup by returning null
    };
    
    /*
     * METHOD 2: Block popunder windows
     * =====================================
     * Technique: Event listener on user clicks
     * - e.isTrusted: Only handle real user clicks (not simulated)
     * - setTimeout: Check after click completes
     * - window.opener: Property exists if this window was opened by another window
     */
    window.addEventListener('click', function(e) {
        if (e.isTrusted) {  // Real user click (not script-triggered)
            setTimeout(() => {
                // If this window has an opener, it might be a popunder
                if (window.opener) {
                    try {
                        BlockMonitor.log('popunder', 'Popunder window detected');
                    } catch (e) {}
                    window.close();  // Close popunder
                }
            }, 100);  // 100ms delay to let click event complete
        }
    }, true);  // true = capture phase (runs before target phase)
    
    /*
     * METHOD 3: Block overlay ads (MutationObserver)
     * ================================================
     * Advanced Pattern: Watch DOM for changes and react
     * 
     * MutationObserver: Browser API that watches for DOM modifications
     * - Triggers callback when elements are added/removed/changed
     * - More efficient than polling (setInterval)
     * 
     * Use case: Streaming sites inject overlay ads after page load
     * Solution: Watch for new elements with suspicious properties:
     * - position: fixed (overlay)
     * - High z-index (appears on top)
     * - Class names like 'ad-overlay', 'popup-ad'
     */
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                // nodeType === 1 means Element node (not text, comment, etc.)
                if (node.nodeType === 1) {
                    // Check if element looks like an overlay ad
                    if (node.style && (
                        (node.style.position === 'fixed' && node.style.zIndex > 1000) ||
                        node.classList.contains('ad-overlay') ||
                        node.classList.contains('popup-ad')
                    )) {
                        try {
                            const className = node.className || 'overlay';
                            BlockMonitor.log('ad', `Overlay ad removed: ${className}`);
                        } catch (e) {}
                        node.remove();  // Remove the ad element from DOM
                    }
                }
            });
        });
    });
    
    // Start observing document.body for changes
    // childList: watch for child nodes being added/removed
    // subtree: watch all descendants, not just direct children
    observer.observe(document.body, { childList: true, subtree: true });
})();  // ← Execute immediately!

// Global variable to store current stream data
let streamData = null;  // Will hold response from /extract endpoint

/**
 * ====================================================================================
 * MAIN EXTRACTION FUNCTION (async/await pattern)
 * ====================================================================================
 * 
 * Advanced Pattern: async/await
 * -----------------------------
 * Why use async/await?
 * - Makes asynchronous code look synchronous (easier to read)
 * - Better than callback hell or .then() chains
 * - Built on Promises, but cleaner syntax
 * 
 * Key Concepts:
 * - async: Marks function as asynchronous (always returns a Promise)
 * - await: Pauses execution until Promise resolves
 * - try-catch-finally: Error handling for async code
 * 
 * Learning: Modern JavaScript for API calls
 */
async function extractStream() {
    // Step 1: Validate consent before doing anything
    if (!consentGiven) {
        showError('You must agree to the terms by checking the consent box before using this tool.');
        return;  // Early return pattern (guard clause)
    }
    
    // Step 2: Get DOM elements (caching them for performance)
    const url = document.getElementById('urlInput').value;
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const playerSection = document.getElementById('playerSection');
    
    // Step 3: Validate input
    if (!url) {
        showError('Please enter a URL');
        return;
    }
    
    // Step 4: Show loading UI (user feedback is important!)
    loading.classList.add('active');  // classList: modern way to manipulate CSS classes
    loading.querySelector('p').textContent = 'Analyzing page structure...';
    error.classList.remove('active');
    playerSection.classList.remove('active');
    
    /* 
     * Step 5: Make HTTP request to backend
     * ====================================
     * Fetch API: Modern way to make HTTP requests (replaces XMLHttpRequest)
     * 
     * await fetch():
     * - Sends HTTP request
     * - Returns Response object
     * - Doesn't throw on HTTP errors (404, 500, etc.) - only network errors
     * 
     * await response.json():
     * - Parses JSON response body
     * - Returns JavaScript object
     * 
     * JSON.stringify():
     * - Converts JavaScript object → JSON string for transmission
     * 
     * Learning: RESTful API communication pattern
     */
    try {
        const response = await fetch('/extract', {  // await = wait for Promise to resolve
            method: 'POST',  // HTTP method (POST sends data)
            headers: {
                'Content-Type': 'application/json'  // Tell server we're sending JSON
            },
            body: JSON.stringify({  // Convert JS object → JSON string
                url: url,
                consent: {
                    given: consentGiven,
                    timestamp: consentTimestamp
                }
            })
        });
        
        const data = await response.json();  // Parse JSON response
        
        // Check for application-level errors (not HTTP errors)
        if (data.error) {
            // Special handling for "no iframes" error with helpful guidance
            if (data.error === 'no_iframes' && data.help) {
                showDetailedError(data);
            } else {
                showError(data.error);
            }
            return;
        }
        
        // Success! Store and display the data
        streamData = data;  // Store globally for changeStream() function
        displayStream(data);
        
    } catch (err) {
        // Catch network errors or JSON parsing errors
        showError('Failed to extract stream: ' + err.message);
    } finally {
        // finally: Always runs (success or error)
        // Perfect for cleanup code (hiding loading spinner, etc.)
        loading.classList.remove('active');
    }
}

/**
 * ====================================================================================
 * DISPLAY STREAM DATA (DOM Manipulation)
 * ====================================================================================
 * 
 * Learning: Working with the DOM (Document Object Model)
 * 
 * DOM Concepts:
 * - getElementById(): Get single element by id (fastest selector)
 * - .innerHTML: Get/set HTML content (dangerous if not sanitized!)
 * - .textContent: Get/set text content (safe, no HTML parsing)
 * - createElement(): Create new HTML element
 * - appendChild(): Add child element to parent
 * 
 * Performance Tip: Cache DOM queries in variables (don't query repeatedly)
 */
function displayStream(data) {
    // Cache all DOM elements we'll need (query once, use many times)
    const playerSection = document.getElementById('playerSection');
    const playerContainer = document.getElementById('playerContainer');
    const streamTitle = document.getElementById('streamTitle');
    const streamSelector = document.getElementById('streamSelector');
    const streamSelect = document.getElementById('streamSelect');
    const infoList = document.getElementById('infoList');
    
    // Set page title (textContent is safe from XSS attacks)
    streamTitle.textContent = data.title || 'Stream Viewer';  // || = default value if null
    
    // Clear previous content (prepare for new data)
    // innerHTML = '': Fast way to clear all children
    playerContainer.innerHTML = '';
    streamSelect.innerHTML = '<option value="">Choose a stream...</option>';
    infoList.innerHTML = '';
    
    /*
     * Build dropdown selector with ALL iframes
     * ========================================
     * Learning: 
     * - forEach(): Loop through array
     * - String methods: includes(), toLowerCase(), substring()
     * - URL API: Parse and extract parts of URLs
     * - DOM creation: createElement(), appendChild()
     */
    if (data.iframes && data.iframes.length > 0) {
        let playerIframeIndex = 0;  // Track which iframe to load by default
        let playerCount = 0;  // Count actual video streams
        
        // Loop through each iframe and create an option element
        data.iframes.forEach((iframe, index) => {  // index: array position (0, 1, 2, ...)
            // Classify iframe by analyzing its URL (heuristic approach)
            const src = iframe.src.toLowerCase();  // Lowercase for case-insensitive matching
            const isChat = src.includes('chatango') || src.includes('chat');
            const isAd = src.includes('dtscout') || src.includes('analytics') || src.includes('ads');
            const isPlayer = src.includes('player') || src.includes('stream') || src.includes('embed') || src.includes('video');
            
            let label = '';
            let prefix = '';
            
            // Determine label based on iframe type (priority order matters!)
            if (iframe.label) {
                // Backend provided custom label (e.g., "Link 1 HD")
                playerCount++;
                label = iframe.label;
                prefix = '[STREAM] ';
                if (playerCount === 1) playerIframeIndex = index;  // Remember first stream
            } else if (isPlayer && !isChat && !isAd) {
                // Looks like video player (based on URL keywords)
                playerCount++;
                label = `VIDEO STREAM ${playerCount}`;
                prefix = '[STREAM] ';
                if (playerCount === 1) playerIframeIndex = index;
            } else if (isChat) {
                label = 'CHAT';
                prefix = '[CHAT] ';
            } else if (isAd) {
                label = 'TRACKING/ADS';
                prefix = '[BLOCKED] ';
            } else {
                label = `UNKNOWN ${index + 1}`;
                prefix = '[?] ';
            }
            
            // Create <option> element for dropdown
            const option = document.createElement('option');
            option.value = index;  // Store array index as value
            
            /*
             * Extract domain name from URL (URL API)
             * ======================================
             * new URL(): Browser API to parse URLs
             * - .hostname: Domain name (e.g., "www.example.com")
             * - .protocol: "https:" or "http:"
             * - .pathname: "/path/to/page"
             * 
             * Why try-catch? new URL() throws error if URL is malformed
             */
            try {
                const urlObj = new URL(iframe.src);  // Parse URL
                const domain = urlObj.hostname.replace('www.', '');  // Remove www. prefix
                option.textContent = iframe.label ? `${prefix}${label} (${domain})` : `${prefix}${label} - ${domain}`;
            } catch(e) {
                // Fallback if URL parsing fails (shouldn't happen with valid iframes)
                option.textContent = `${prefix}${label} - ${iframe.src.substring(0, 40)}...`;
            }
            
            // Disable non-player options (visual feedback: can't select chat/ads)
            if ((!isPlayer && !iframe.label) || isChat || isAd) {
                option.disabled = true;  // Can't be selected
                option.style.color = '#999';  // Gray out text
            }
            
            streamSelect.appendChild(option);  // Add to dropdown
        });
        
        // Add message if only one stream found
        if (playerCount === 1) {
            const separator = document.createElement('option');
            separator.disabled = true;
            separator.textContent = `━━━━━━━━━━━━━━━━━━━━━`;
            streamSelect.appendChild(separator);
            
            const note = document.createElement('option');
            note.disabled = true;
            note.textContent = `[INFO] Only 1 stream available for this game`;
            streamSelect.appendChild(note);
        } else if (playerCount > 1) {
            const separator = document.createElement('option');
            separator.disabled = true;
            separator.textContent = `━━━━━━━━━━━━━━━━━━━━━`;
            streamSelect.appendChild(separator);
            
            const note = document.createElement('option');
            note.disabled = true;
            note.textContent = `[INFO] ${playerCount} streams found! Try both for best quality`;
            streamSelect.appendChild(note);
        }
        
        streamSelector.style.display = 'block';
        
        // Load the main player by default
        streamSelect.value = playerIframeIndex;
        loadIframe(data.iframes[playerIframeIndex]);
    } else {
        playerContainer.innerHTML = '<p style="padding: 32px; text-align: center; color: #86868b; font-size: 17px;">No video player found. The stream might be loading dynamically via JavaScript.</p>';
    }
    
    // Display info
    const info = [
        `Found ${data.iframes ? data.iframes.length : 0} iframe(s)`
    ];
    
    
    info.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        infoList.appendChild(li);
    });
    
    playerSection.classList.add('active');
}

function loadIframe(iframeData) {
    const playerContainer = document.getElementById('playerContainer');
    const streamUrlCard = document.getElementById('streamUrlCard');
    const adWarningCard = document.getElementById('adWarningCard');
    const blockedWarningCard = document.getElementById('blockedWarningCard');
    
    // Hide all warning cards by default
    adWarningCard.style.display = 'none';
    blockedWarningCard.style.display = 'none';
    
    // Check if this stream blocks localhost embedding (like ppvs.su)
    const url = new URL(iframeData.src);
    const blocksLocalhost = url.hostname.includes('ppvs.su') || 
                           url.hostname.includes('streambtw.com') ||
                           url.hostname.includes('v3.sportsonline.si');
    
    // Check if this is a known ad-heavy domain
    const isAdHeavy = url.hostname.includes('thedaddy.to') ||
                     url.hostname.includes('daddylivestream.com') ||
                     url.hostname.includes('embedsports.me');
    
    // Create iframe with MAXIMUM blocking (DECLARE EARLY!)
    const iframe = document.createElement('iframe');
    iframe.src = iframeData.src;
    iframe.width = '100%';
    iframe.height = '600';
    iframe.allowFullscreen = true;
    
    // Advanced blocking: disable features that ads use
    iframe.allow = 'autoplay; fullscreen; picture-in-picture; encrypted-media';
    iframe.setAttribute('referrerpolicy', 'no-referrer');
    iframe.setAttribute('sandbox', 'allow-same-origin allow-scripts allow-forms');
    iframe.style.border = 'none';
    // Note: CSP must be set as an HTTP header, not an iframe attribute
    iframe.setAttribute('loading', 'lazy');
    
    // Populate the stream URL card
    streamUrlCard.style.display = 'block';
    streamUrlCard.innerHTML = `
        <div style="margin-bottom: 10px; word-break: break-all;"><strong style="color: #1d1d1f; font-size: 14px;">Stream URL:</strong> <span style="color: #86868b; font-size: 12px; font-family: 'SF Mono', Monaco, monospace;">${iframeData.src}</span></div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <a href="${iframeData.src}" target="_blank" style="background: #007aff; color: white; padding: 10px 18px; border-radius: 10px; text-decoration: none; display: inline-block; font-size: 14px; font-weight: 500; transition: all 0.2s; -webkit-tap-highlight-color: transparent; flex: 1; min-width: 140px; text-align: center;">Open in New Tab</a>
            <button onclick="copyToClipboard('${iframeData.src.replace(/'/g, "\\'")}')" style="background: #5856d6; color: white; border: none; padding: 10px 18px; border-radius: 10px; cursor: pointer; font-size: 14px; font-weight: 500; transition: all 0.2s; -webkit-tap-highlight-color: transparent; flex: 1; min-width: 140px;">Copy URL</button>
        </div>
    `;
    
    // Add iframe load error detection
    iframe.addEventListener('error', () => {
        console.warn('Iframe failed to load:', iframeData.src);
    });
    
    // Monitor iframe for load issues
    let iframeLoadTimeout = setTimeout(() => {
        // After 30 seconds, check if iframe is still loading
        console.warn('Iframe taking longer than expected to load');
    }, 30000);
    
    iframe.addEventListener('load', () => {
        clearTimeout(iframeLoadTimeout);
        console.log('Iframe loaded successfully');
    });
    
    // Show appropriate warning cards
    if (isAdHeavy) {
        adWarningCard.style.display = 'block';
    }
    
    if (blocksLocalhost) {
        blockedWarningCard.style.display = 'block';
        blockedWarningCard.innerHTML = `
            <strong style="color: #ff3b30; font-size: 16px;">Embedding Blocked</strong><br>
            <p style="margin: 10px 0 0 0; line-height: 1.5; font-size: 14px;">This stream (${url.hostname}) blocks embedding from localhost.<br>
            <strong>Solution:</strong> Click "<strong style="color: #007aff;">Open in New Tab</strong>" above to watch this stream.<br>
            <span style="font-size: 12px; color: #86868b; margin-top: 8px; display: block;">Reason: The stream provider checks the referring domain and only allows embedding from crackstreams.ms</span></p>
        `;
    }
    
    // Prepare player container
    playerContainer.innerHTML = '';
    
    // Only embed iframe if it doesn't block localhost
    if (blocksLocalhost) {
        const warningPlaceholder = document.createElement('div');
        warningPlaceholder.style.cssText = 'background: #000; color: white; padding: 40px 20px; text-align: center; border-radius: 8px; font-size: 16px;';
        warningPlaceholder.innerHTML = `
            <div style="font-size: 36px; margin-bottom: 16px;">🚫</div>
            <strong>This stream cannot be embedded from localhost</strong><br><br>
            <a href="${iframeData.src}" target="_blank" style="background: #764ba2; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block; font-size: 16px; margin-top: 10px; -webkit-tap-highlight-color: transparent;">Click Here to Watch</a>
        `;
        playerContainer.appendChild(warningPlaceholder);
    } else {
        playerContainer.appendChild(iframe);
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Stream URL copied to clipboard!');
    }).catch(() => {
        alert('Failed to copy. URL: ' + text);
    });
}

function changeStream() {
    const select = document.getElementById('streamSelect');
    const index = parseInt(select.value);
    
    if (!isNaN(index) && streamData && streamData.iframes && streamData.iframes[index]) {
        loadIframe(streamData.iframes[index]);
    }
}

/**
 * Show simple error message
 */
function showError(message) {
    const error = document.getElementById('error');
    error.textContent = message;
    error.classList.add('active');
}

/**
 * Show detailed error with helpful guidance (for no iframes found)
 * If links are provided, show them as clickable options
 */
function showDetailedError(data) {
    const error = document.getElementById('error');
    
    // Override default error styling to be white/clean
    error.style.background = '#ffffff';
    error.style.color = '#1d1d1f';
    error.style.border = '1px solid #d2d2d7';
    
    // Start with the error message
    let html = `
        <div style="margin-bottom: 16px;">
            <strong style="display: block; margin-bottom: 8px; color: #1d1d1f;">${data.message}</strong>
            <p style="margin: 0; color: #86868b; line-height: 1.5;">${data.help}</p>
        </div>
    `;
    
    // If links were found, show them as options
    if (data.links && data.links.length > 0) {
        html += `
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #d2d2d7;">
                <strong style="display: block; margin-bottom: 12px; color: #1d1d1f;">
                    Links found on this page (${data.links.length}):
                </strong>
                <p style="font-size: 13px; color: #86868b; margin-bottom: 12px; line-height: 1.5;">
                    Click a link below to analyze that page instead:
                </p>
                <div style="max-height: 300px; overflow-y: auto; background: #f5f5f7; border-radius: 8px; padding: 8px;">
        `;
        
        // Add each link as a clickable item
        data.links.forEach((link, index) => {
            // Truncate long titles
            const displayTitle = link.title.length > 80 ? link.title.substring(0, 80) + '...' : link.title;
            
            html += `
                <div onclick="analyzeLink('${link.url.replace(/'/g, "\\'")}')" 
                     style="padding: 10px 12px; margin-bottom: 4px; background: white; border-radius: 6px; cursor: pointer; transition: all 0.2s; border: 1px solid #e5e5e5;"
                     onmouseover="this.style.background='#007aff'; this.style.color='white'; this.style.borderColor='#007aff';"
                     onmouseout="this.style.background='white'; this.style.color='#1d1d1f'; this.style.borderColor='#e5e5e5';">
                    <div style="font-size: 14px; font-weight: 500; margin-bottom: 2px; color: inherit;">
                        ${displayTitle}
                    </div>
                    <div style="font-size: 11px; opacity: 0.7; font-family: 'SF Mono', Monaco, monospace; word-break: break-all;">
                        ${link.url}
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    error.innerHTML = html;
    error.classList.add('active');
}

/**
 * Analyze a link that was clicked from the link list
 * Populates the URL input and triggers extraction
 */
function analyzeLink(url) {
    // Populate the URL input
    document.getElementById('urlInput').value = url;
    
    // Trigger extraction (requires consent to still be given)
    extractStream();
}

/*
 * ====================================================================================
 * EVENT LISTENERS (User Interaction)
 * ====================================================================================
 * Set up keyboard shortcuts for better UX
 */

// Allow Enter key to submit (common user expectation)
// addEventListener(): Attach event handler to element
// 'keypress': Fires when user presses a key
document.getElementById('urlInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {  // e.key: Which key was pressed
        extractStream();  // Trigger extraction (same as clicking button)
    }
});

