# -*- coding: utf-8 -*-
"""
Scrapy Middlewares für erweiterte Request- und Response-Verarbeitung.

Middlewares ermöglichen es, den Request/Response-Zyklus von Scrapy
zu modifizieren und erweiterte Funktionalitäten hinzuzufügen.
"""

import random
import logging
from typing import Union, Optional
from urllib.parse import urlparse

from scrapy import signals, Request, Spider
from scrapy.http import HtmlResponse
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from scrapy.exceptions import NotConfigured


class CrawlerSpiderMiddleware:
    """
    Spider-Middleware für zusätzliche Spider-Funktionalitäten.
    """

    @classmethod
    def from_crawler(cls, crawler):
        """Factory-Methode zur Erstellung der Middleware."""
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        """Verarbeitet Spider-Input (Response)."""
        return None

    def process_spider_output(self, response, result, spider):
        """Verarbeitet Spider-Output (Items und Requests)."""
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        """Behandelt Spider-Exceptions."""
        spider.logger.error(f"Spider exception: {exception}")
        pass

    def process_start_requests(self, start_requests, spider):
        """Verarbeitet Start-Requests."""
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        """Wird aufgerufen wenn der Spider geöffnet wird."""
        spider.logger.info(f'Spider opened: {spider.name}')


class CrawlerDownloaderMiddleware:
    """
    Downloader-Middleware für Request/Response-Verarbeitung.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        """Factory-Methode zur Erstellung der Middleware."""
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request: Request, spider: Spider) -> Optional[Union[None, HtmlResponse, Request]]:
        """
        Verarbeitet ausgehende Requests.
        
        Args:
            request: Der zu verarbeitende Request
            spider: Der Spider der den Request erstellt hat
            
        Returns:
            None: Request wird normal verarbeitet
            HtmlResponse: Response wird direkt zurückgegeben
            Request: Neuer Request ersetzt den alten
        """
        # Zusätzliche Headers für bessere Tarnung
        request.headers.setdefault('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        request.headers.setdefault('Accept-Language', 'de-DE,de;q=0.9,en;q=0.8')
        
        # Referer-Header hinzufügen für bessere Tarnung
        if hasattr(spider, 'last_url') and spider.last_url:
            request.headers.setdefault('Referer', spider.last_url)
        
        spider.last_url = request.url
        
        self.logger.debug(f"Processing request: {request.url}")
        return None

    def process_response(self, request: Request, response: HtmlResponse, spider: Spider) -> Union[HtmlResponse, Request]:
        """
        Verarbeitet eingehende Responses.
        
        Args:
            request: Der ursprüngliche Request
            response: Die empfangene Response
            spider: Der Spider
            
        Returns:
            HtmlResponse: Die verarbeitete Response
            Request: Neuer Request für Retry
        """
        # Erfolgreiche Responses durchlassen
        if response.status == 200:
            return response
        
        # Umgang mit verschiedenen HTTP-Status-Codes
        if response.status == 403:
            self.logger.warning(f"Access forbidden (403): {request.url}")
        elif response.status == 404:
            self.logger.warning(f"Page not found (404): {request.url}")
        elif response.status >= 500:
            self.logger.error(f"Server error ({response.status}): {request.url}")
        
        return response

    def process_exception(self, request: Request, exception: Exception, spider: Spider):
        """
        Behandelt Exceptions während der Request-Verarbeitung.
        
        Args:
            request: Der fehlgeschlagene Request
            exception: Die aufgetretene Exception
            spider: Der Spider
        """
        self.logger.error(f"Request exception for {request.url}: {exception}")
        pass

    def spider_opened(self, spider):
        """Wird aufgerufen wenn der Spider geöffnet wird."""
        spider.logger.info(f'Downloader middleware opened for: {spider.name}')
        spider.last_url = None


class RotateUserAgentMiddleware(UserAgentMiddleware):
    """
    Middleware zur Rotation von User-Agent-Strings für bessere Tarnung.
    
    Diese Middleware rotiert zwischen verschiedenen User-Agent-Strings
    um zu verhindern, dass der Crawler als Bot erkannt wird.
    """
    
    def __init__(self, user_agent='Scrapy'):
        """
        Initialisiert die Middleware mit einer Liste von User-Agents.
        
        Args:
            user_agent: Standard User-Agent (wird überschrieben)
        """
        self.user_agent = user_agent
        
        # Liste realistischer User-Agent-Strings
        self.user_agent_list = [
            # Chrome Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            
            # Chrome macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            
            # Firefox Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
            
            # Firefox macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0',
            
            # Safari macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
            
            # Edge Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
            
            # Chrome Linux
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            
            # Mobile User-Agents
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 14; SM-S926B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36',
        ]
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"User-Agent-Rotation initialisiert mit {len(self.user_agent_list)} User-Agents")

    @classmethod
    def from_crawler(cls, crawler):
        """
        Factory-Methode zur Erstellung der Middleware aus Crawler-Settings.
        
        Args:
            crawler: Scrapy-Crawler-Objekt
            
        Returns:
            RotateUserAgentMiddleware: Initialisierte Middleware-Instanz
        """
        user_agent_list = crawler.settings.getlist("USER_AGENT_LIST")
        if not user_agent_list:
            raise NotConfigured("USER_AGENT_LIST not set or empty")
        
        middleware = cls(crawler.settings.get("USER_AGENT"))
        middleware.user_agent_list = user_agent_list
        return middleware

    def process_request(self, request: Request, spider: Spider):
        """
        Wählt zufällig einen User-Agent für den Request aus.
        
        Args:
            request: Der zu verarbeitende Request
            spider: Der Spider der den Request erstellt hat
        """
        # Zufälligen User-Agent auswählen
        ua = random.choice(self.user_agent_list)
        request.headers['User-Agent'] = ua
        
        self.logger.debug(f"Rotated User-Agent for {request.url}: {ua[:50]}...")
        
        return None


class ProxyMiddleware:
    """
    Middleware für Proxy-Rotation (optional, für erweiterte Anonymität).
    
    Diese Middleware kann verwendet werden um Requests über verschiedene
    Proxy-Server zu routen und so die IP-Adresse zu variieren.
    """
    
    def __init__(self):
        """Initialisiert die Proxy-Middleware."""
        self.proxies = []
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        """Factory-Methode zur Erstellung der Middleware."""
        middleware = cls()
        
        # Proxy-Liste aus Settings laden
        proxy_list = crawler.settings.getlist("PROXY_LIST", [])
        if proxy_list:
            middleware.proxies = proxy_list
            middleware.logger.info(f"Proxy-Middleware initialisiert mit {len(proxy_list)} Proxies")
        else:
            middleware.logger.warning("Keine Proxies konfiguriert")
        
        return middleware
    
    def process_request(self, request: Request, spider: Spider):
        """
        Weist einem Request zufällig einen Proxy zu.
        
        Args:
            request: Der zu verarbeitende Request
            spider: Der Spider
        """
        if self.proxies and not request.meta.get('proxy'):
            proxy = random.choice(self.proxies)
            request.meta['proxy'] = proxy
            self.logger.debug(f"Assigned proxy {proxy} to {request.url}")
        
        return None


class RetryMiddleware:
    """
    Erweiterte Retry-Middleware für fehlgeschlagene Requests.
    """
    
    def __init__(self, retry_times=3, retry_http_codes=None):
        """
        Initialisiert die Retry-Middleware.
        
        Args:
            retry_times: Anzahl der Retry-Versuche
            retry_http_codes: HTTP-Codes für die ein Retry versucht werden soll
        """
        self.retry_times = retry_times
        self.retry_http_codes = retry_http_codes or [500, 502, 503, 504, 408, 429]
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        """Factory-Methode zur Erstellung der Middleware."""
        retry_times = crawler.settings.getint("RETRY_TIMES", 3)
        retry_http_codes = crawler.settings.getlist("RETRY_HTTP_CODES", [500, 502, 503, 504, 408, 429])
        
        return cls(retry_times, retry_http_codes)
    
    def process_response(self, request: Request, response: HtmlResponse, spider: Spider):
        """
        Prüft ob ein Response einen Retry benötigt.
        
        Args:
            request: Der ursprüngliche Request
            response: Die empfangene Response
            spider: Der Spider
            
        Returns:
            HtmlResponse oder Request: Response oder neuer Retry-Request
        """
        if response.status in self.retry_http_codes:
            retry_times = request.meta.get('retry_times', 0) + 1
            
            if retry_times <= self.retry_times:
                self.logger.warning(f"Retrying {request.url} (attempt {retry_times}/{self.retry_times})")
                
                retry_req = request.copy()
                retry_req.meta['retry_times'] = retry_times
                retry_req.dont_filter = True
                
                return retry_req
            else:
                self.logger.error(f"Gave up retrying {request.url} after {self.retry_times} attempts")
        
        return response

