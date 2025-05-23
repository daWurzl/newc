# -*- coding: utf-8 -*-
"""
Scrapy Spider mit Playwright-Integration für Web-Crawling

Dieser Spider nutzt Scrapy-Playwright um JavaScript-lastige Webseiten zu crawlen
und unterstützt erweiterte Browser-Interaktionen wie Screenshots und Scrolling.
"""

import scrapy
import random
import os
from typing import Dict, Any, Generator
from urllib.parse import urlparse, urljoin
from scrapy.http import Request, Response
from scrapy_playwright.page import PageMethod
from crawler.items import WebPageItem


class WebSpider(scrapy.Spider):
    """
    Hauptspider für das Crawlen von Webseiten mit Playwright-Unterstützung.
    
    Features:
    - JavaScript-Rendering über Playwright
    - Anti-Bot-Maßnahmen durch User-Agent-Rotation
    - Screenshot-Funktionalität
    - Flexible URL-Konfiguration über Umgebungsvariablen
    - Ressourcen-Monitoring
    """
    
    name = 'webspider'
    
    # Erlaubte Domains für das Crawling
    allowed_domains = [
        'bund.de',
        'bundestag.de', 
        'euractiv.de',
        'dw.com',
        'zdf.de',
        'spiegel.de',
        'faz.net',
        'welt.de',
        'handelsblatt.com',
        'zeit.de'
    ]
    
    # Standard-URLs für das Crawling (erweiterbar über Umgebungsvariablen)
    start_urls = [
        "https://www.bund.de/",
        "https://www.bundestag.de/",
        "https://www.euractiv.de/",
        "https://www.dw.com/de/",
        "https://www.zdf.de/nachrichten/",
        "https://www.spiegel.de/",
        "https://www.faz.net/",
        "https://www.welt.de/",
        "https://www.handelsblatt.com/",
        "https://www.zeit.de/"
    ]
    
    # JavaScript-lastige Seiten, die spezielle Behandlung benötigen
    js_heavy_sites = [
        'zdf.de',
        'spiegel.de',
        'zeit.de'
    ]
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
    }

    def __init__(self, *args, **kwargs):
        """
        Spider-Initialisierung mit optionaler URL-Konfiguration.
        
        Args:
            *args: Variable Argumente
            **kwargs: Keyword-Argumente (url_list für custom URLs)
        """
        super(WebSpider, self).__init__(*args, **kwargs)
        
        # Custom URLs aus Argumenten laden (falls vorhanden)
        if 'url_list' in kwargs:
            custom_urls = kwargs['url_list'].split(',')
            self.start_urls = [url.strip() for url in custom_urls if url.strip()]
            self.logger.info(f"Using custom URLs: {len(self.start_urls)} URLs loaded")
        
        # Screenshot-Verzeichnis erstellen
        self.screenshot_dir = "screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        self.logger.info(f"WebSpider initialized with {len(self.start_urls)} start URLs")

    def start_requests(self) -> Generator[Request, None, None]:
        """
        Generiert die initialen Requests mit Playwright-Konfiguration.
        
        Yields:
            Request: Scrapy-Request mit Playwright-Meta-Daten
        """
        for url in self.start_urls:
            # Domain aus URL extrahieren für spezifische Behandlung
            domain = urlparse(url).netloc
            
            # Prüfen ob JavaScript-Rendering erforderlich ist
            needs_js = any(js_site in domain for js_site in self.js_heavy_sites)
            
            # Meta-Daten für Playwright konfigurieren
            meta = {
                'playwright': True,
                'playwright_include_page': True,
                'playwright_context': 'default',
                'domain': domain,
                'needs_js': needs_js
            }
            
            # Erweiterte Playwright-Methoden für JavaScript-lastige Seiten
            if needs_js:
                meta['playwright_page_methods'] = [
                    PageMethod('wait_for_load_state', 'networkidle'),
                    PageMethod('wait_for_timeout', 2000),  # 2 Sekunden warten
                ]
                self.logger.info(f"Using JavaScript rendering for {url}")
            else:
                meta['playwright_page_methods'] = [
                    PageMethod('wait_for_load_state', 'domcontentloaded'),
                ]
            
            yield Request(
                url=url,
                callback=self.parse,
                errback=self.handle_error,
                meta=meta,
                dont_filter=True
            )

    async def parse(self, response: Response) -> Generator[Dict[str, Any], None, None]:
        """
        Hauptparser für die extrahierten Webseiten-Daten.
        
        Args:
            response: Scrapy-Response-Objekt mit Playwright-Daten
            
        Yields:
            WebPageItem: Extrahierte Daten der Webseite
        """
        # Playwright-Page-Objekt aus Response-Meta extrahieren
        page = response.meta.get("playwright_page")
        domain = response.meta.get('domain', 'unknown')
        
        try:
            # Screenshot erstellen (optional, für Debugging)
            screenshot_path = f"{self.screenshot_dir}/{domain}_{random.randint(1000, 9999)}.png"
            if page:
                await page.screenshot(path=screenshot_path, full_page=True)
                self.logger.info(f"Screenshot saved: {screenshot_path}")
            
            # Seitentitel extrahieren
            title = response.css('title::text').get()
            if not title:
                title = response.css('h1::text').get()
            if not title:
                title = "Ohne Titel"
            
            # Titel bereinigen
            title = title.strip() if title else "Ohne Titel"
            
            # Meta-Beschreibung extrahieren
            description = response.css('meta[name="description"]::attr(content)').get()
            if not description:
                description = response.css('meta[property="og:description"]::attr(content)').get()
            
            # Keywords extrahieren
            keywords = response.css('meta[name="keywords"]::attr(content)').get()
            
            # Sprache der Seite ermitteln
            language = response.css('html::attr(lang)').get()
            if not language:
                language = response.css('meta[http-equiv="content-language"]::attr(content)').get()
            
            # Zusätzliche Links extrahieren (für weitere Crawling-Möglichkeiten)
            internal_links = []
            for link in response.css('a[href]::attr(href)').getall()[:10]:  # Begrenzt auf 10
                absolute_url = urljoin(response.url, link)
                if self._is_allowed_domain(absolute_url):
                    internal_links.append(absolute_url)
            
            # WebPageItem erstellen und befüllen
            item = WebPageItem()
            item['title'] = title
            item['url'] = response.url
            item['domain'] = domain
            item['description'] = description[:500] if description else None
            item['keywords'] = keywords
            item['language'] = language
            item['internal_links'] = internal_links
            item['screenshot_path'] = screenshot_path if os.path.exists(screenshot_path) else None
            item['status_code'] = response.status
            item['content_type'] = response.headers.get('content-type', b'').decode('utf-8')
            
            self.logger.info(f"Successfully parsed: {title[:50]}... ({response.url})")
            
            yield item
            
            # Optional: Weitere interne Links crawlen (begrenzt)
            # for link_url in internal_links[:2]:  # Nur 2 weitere Links pro Seite
            #     yield Request(
            #         url=link_url,
            #         callback=self.parse,
            #         meta={'playwright': True, 'playwright_include_page': True},
            #         dont_filter=False
            #     )
            
        except Exception as e:
            self.logger.error(f"Error parsing {response.url}: {str(e)}")
            
        finally:
            # Playwright-Page schließen um Memory-Leaks zu vermeiden
            if page:
                await page.close()

    async def handle_error(self, failure):
        """
        Error-Handler für fehlgeschlagene Requests.
        
        Args:
            failure: Twisted-Failure-Objekt mit Fehlerinformationen
        """
        request = failure.request
        
        self.logger.error(f"Request failed: {request.url}")
        self.logger.error(f"Error type: {failure.type}")
        self.logger.error(f"Error value: {failure.value}")
        
        # Playwright-Page schließen auch bei Fehlern
        page = request.meta.get("playwright_page")
        if page:
            try:
                await page.close()
            except:
                pass  # Page könnte bereits geschlossen sein

    def _is_allowed_domain(self, url: str) -> bool:
        """
        Prüft ob eine URL zu den erlaubten Domains gehört.
        
        Args:
            url: Zu prüfende URL
            
        Returns:
            bool: True wenn Domain erlaubt ist
        """
        try:
            domain = urlparse(url).netloc.lower()
            return any(allowed in domain for allowed in self.allowed_domains)
        except:
            return False

    def closed(self, reason):
        """
        Callback wenn Spider beendet wird.
        
        Args:
            reason: Grund für das Beenden des Spiders
        """
        self.logger.info(f"Spider closed: {reason}")
        
        # Aufräumen von temporären Dateien (optional)
        # for file in os.listdir(self.screenshot_dir):
        #     if file.endswith('.png'):
        #         os.remove(os.path.join(self.screenshot_dir, file))

