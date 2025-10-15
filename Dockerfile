# ============================================================================
# DOCKERFILE (Educational Guide for Learners)
# ============================================================================
# What is Docker? Packages your app + dependencies into a container
# Benefits: Same environment everywhere (dev, staging, prod)
# Key Concepts: Layers, images, containers, caching
#
# Build: docker build -t stream-extractor .
# Run: docker run -p 8080:8080 stream-extractor
# ============================================================================

# Step 1: Base Image
# -------------------
# FROM: Inherit from another image (all Dockerfiles start with FROM)
# python:3.13-slim: Official Python image, "slim" = minimal (smaller size)
# Why slim? Fewer packages = smaller image, faster downloads, less attack surface
# Alternative: python:3.13-alpine (even smaller but can have compatibility issues)
FROM python:3.13-slim

# Step 2: Install System Dependencies
# ------------------------------------
# RUN: Execute command in the container (each RUN creates a new layer)
# Why combine with &&? Creates single layer (more efficient than separate RUNs)
#
# What we're installing:
# - chromium: Headless Chrome browser for Selenium
# - chromium-driver: ChromeDriver (Selenium's interface to Chrome)
# - fonts-liberation, lib*: Chrome dependencies (required for headless mode)
#
# apt-get tricks for production:
# - --no-install-recommends: Skip suggested packages (smaller image)
# - rm -rf /var/lib/apt/lists/*: Delete package lists (saves ~50MB)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    fonts-liberation \
    libasound2 \
    libnss3 \
    libx11-6 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Step 3: Environment Variables
# ------------------------------
# ENV: Set environment variables (persist in container)
# Why? Configure app without changing code
#
# CHROME_BIN: Tell Selenium where Chrome is installed
# CHROMEDRIVER_BIN: Tell Selenium where ChromeDriver is installed
# PYTHONUNBUFFERED=1: Show Python output immediately (critical for logs)
# PORT=8080: Default port (Render/Railway use this)
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Step 4: Working Directory
# --------------------------
# WORKDIR: Sets current directory (all subsequent commands run here)
# Creates /app if it doesn't exist
# Why /app? Convention for application code in containers
WORKDIR /app

# Step 5: Install Python Dependencies
# ------------------------------------
# COPY: Copy files from host → container
# Why copy requirements.txt first? Docker layer caching!
#   - If requirements.txt unchanged, reuses cached layer (fast rebuilds)
#   - If we copied all code first, would reinstall packages every time
#
# pip install flags:
# - --no-cache-dir: Don't store pip's download cache (saves space)
# - -r requirements.txt: Install from file
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Step 6: Copy Application Code
# ------------------------------
# COPY . .: Copy everything from current directory → /app in container
# Runs AFTER pip install (so code changes don't trigger reinstall)
COPY . .

# Step 7: Expose Port
# --------------------
# EXPOSE: Documents which port the container listens on
# Note: Doesn't actually publish the port (just documentation)
# Real publishing: docker run -p 8080:8080 (maps host:container)
EXPOSE 8080

# Step 8: Startup Command
# ------------------------
# CMD: Default command when container starts
# Format: ["executable", "param1", "param2"] (JSON array = exec form)
#
# Gunicorn configuration:
# - -b 0.0.0.0:8080: Bind to all interfaces on port 8080
# - -w 1: Use 1 worker (Selenium isn't thread-safe, would need process pool)
# - --timeout 120: Wait 120s before killing slow requests (Selenium is slow!)
# - app:app: Import "app" from "app.py"
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "1", "--timeout", "120", "app:app"]

