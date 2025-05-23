# -*- coding: utf-8 -*-
"""
Scrapy Settings für Crawler-Projekt mit Playwright-Integration

Diese Konfigurationsdatei definiert alle wichtigen Einstellungen für den
Scrapy-Spider mit Playwright-Unterstützung für JavaScript-Rendering.
"""

import os
from pathlib import Path

# Scrapy settings für crawler Projekt
BOT_NAME = 'crawler'

# Spider-Module definieren
SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'

# ---------------------------------------------
# SCRAPY-PLAYWRIGHT KONFIGURATION
# ---------------------------------------------

# Download-Handler für HTTP/HTTPS-Requests auf Playwright umstellen
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Twisted-Reactor für asyncio-Kompatibilität konfigurieren
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# ---------------------------------------------
# PLAYWRIGHT-SPEZIFISCHE EINSTELLUNGEN
# ---------------------------------------------

# Browser-Typ festlegen (chromium, firefox, webkit)
PLAYWRIGHT_BROWSER_TYPE = "chromium"

# Standard-Navigation-Timeout (30 Sekunden)
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30 * 1000

# Maximale Anzahl gleichzeitiger Browser-Kontexte
PLAYWRIGHT_MAX_CONTEXTS = 3

# Playwright-Prozess-Optionen
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,  # Headless-Modus für bessere Performance
    "args": [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding"
    ]
}

# Playwright-Kontext-Optionen für Anti-Bot-Schutz
PLAYWRIGHT_CONTEXTS = {
    "default": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
        "java_script_enabled": True,
    }
}

# ---------------------------------------------
# GENERAL SCRAPY EINSTELLUNGEN
# ---------------------------------------------

# Robots.txt-Protokoll respektieren
ROBOTSTXT_OBEY = False

# Gleichzeitige Requests begrenzen (für GitHub Actions optimiert)
CONCURRENT_REQUESTS = int(os.getenv('CONCURRENT_REQUESTS', 2))
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Download-Verzögerung zwischen Requests (in Sekunden)
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = 0.5

# AutoThrottle aktivieren für automatische Anpassung der Request-Rate
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False  # Aktivieren für Debug-Ausgaben

# Request-Timeout konfigurieren
DOWNLOAD_TIMEOUT = 30

# ---------------------------------------------
# ANTI-BOT MASSNAHMEN
# ---------------------------------------------

# Default Request Headers (um wie ein echter Browser auszusehen)
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# User-Agent-Rotation aktivieren
USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
]

# ---------------------------------------------
# MIDDLEWARE KONFIGURATION
# ---------------------------------------------

# Spider-Middlewares aktivieren
SPIDER_MIDDLEWARES = {
    'crawler.middlewares.CrawlerSpiderMiddleware': 543,
}

# Downloader-Middlewares aktivieren
DOWNLOADER_MIDDLEWARES = {
    'crawler.middlewares.CrawlerDownloaderMiddleware': 543,
    'crawler.middlewares.RotateUserAgentMiddleware': 400,  # User-Agent-Rotation
}

# ---------------------------------------------
# ITEM PIPELINES
# ---------------------------------------------

# Item-Processing-Pipeline aktivieren
ITEM_PIPELINES = {
    'crawler.pipelines.CrawlerPipeline': 300,
    'crawler.pipelines.CSVExportPipeline': 400,
}

# ---------------------------------------------
# LOGGING KONFIGURATION
# ---------------------------------------------

# Log-Level definieren
LOG_LEVEL = 'INFO'

# Log-Format anpassen
LOG_FORMAT = '%(levelname)s: %(message)s'

# Log-Datei aktivieren (optional)
# LOG_FILE = 'scrapy.log'

# ---------------------------------------------
# FEEDS/EXPORT KONFIGURATION
# ---------------------------------------------

# Standard-Feed-Einstellungen
FEEDS = {
    'data/results.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': ['title', 'url', 'timestamp'],
    }
}

# Feed-Export-Einstellungen
FEED_EXPORT_ENCODING = 'utf-8'

# ---------------------------------------------
# PERFORMANCE OPTIMIERUNGEN
# ---------------------------------------------

# DNS-Caching aktivieren
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000

# HTTP-Caching deaktivieren (für Live-Daten)
HTTPCACHE_ENABLED = False

# Request-Fingerprinting optimieren
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'

# Memory-Optimierungen
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 512  # Für GitHub Actions begrenzt
MEMUSAGE_WARNING_MB = 400

# ---------------------------------------------
# EXTENSIONS
# ---------------------------------------------

# Erweiterte Extensions aktivieren
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,  # Deaktivieren für Sicherheit
    'scrapy.extensions.memusage.MemoryUsage': 500,
}

