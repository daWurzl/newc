# -*- coding: utf-8 -*-
"""
Scrapy Item Pipelines für die Datenverarbeitung.

Pipelines werden verwendet um die von den Spiders zurückgegebenen Items
zu verarbeiten, zu validieren, zu transformieren und zu speichern.
"""

import csv
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from urllib.parse import urlparse

from itemadapter import ItemAdapter, is_item
from scrapy import Spider
from scrapy.exceptions import DropItem
from crawler.items import WebPageItem, NewsArticleItem, TenderItem


class CrawlerPipeline:
    """
    Basis-Pipeline für grundlegende Item-Verarbeitung.
    
    Diese Pipeline führt grundlegende Validierungen und Transformationen
    für alle Item-Typen durch.
    """
    
    def __init__(self):
        self.items_processed = 0
        self.items_dropped = 0
        self.logger = logging.getLogger(__name__)
    
    def process_item(self, item, spider: Spider):
        """
        Verarbeitet ein Item und führt grundlegende Validierungen durch.
        
        Args:
            item: Das zu verarbeitende Item
            spider: Der Spider der das Item erstellt hat
            
        Returns:
            Item: Das verarbeitete Item
            
        Raises:
            DropItem: Wenn das Item ungültig ist
        """
        adapter = ItemAdapter(item)
        
        # Grundlegende Validierung
        if not adapter.get('url'):
            self.logger.warning("Item ohne URL gefunden, wird verworfen")
            self.items_dropped += 1
            raise DropItem("Missing URL")
        
        if not adapter.get('title'):
            self.logger.warning(f"Item ohne Titel: {adapter.get('url')}")
            adapter['title'] = "Ohne Titel"
        
        # Zeitstempel hinzufügen falls nicht vorhanden
        if not adapter.get('timestamp'):
            adapter['timestamp'] = datetime.now().isoformat()
        
        # URL normalisieren
        url = adapter.get('url', '').strip()
        if url:
            adapter['url'] = url
            
            # Domain extrahieren falls nicht vorhanden
            if not adapter.get('domain'):
                try:
                    domain = urlparse(url).netloc
                    adapter['domain'] = domain
                except:
                    adapter['domain'] = 'unknown'
        
        # Titel bereinigen
        title = adapter.get('title', '').strip()
        if title:
            # Übermäßige Whitespaces entfernen
            title = ' '.join(title.split())
            # Maximale Länge begrenzen
            if len(title) > 200:
                title = title[:197] + "..."
            adapter['title'] = title
        
        # Beschreibung bereinigen
        description = adapter.get('description')
        if description:
            description = description.strip()
            if len(description) > 500:
                description = description[:497] + "..."
            adapter['description'] = description
        
        self.items_processed += 1
        self.logger.debug(f"Item verarbeitet: {adapter.get('title', 'Unknown')}")
        
        return item
    
    def close_spider(self, spider: Spider):
        """
        Wird aufgerufen wenn der Spider geschlossen wird.
        
        Args:
            spider: Der Spider der geschlossen wird
        """
        self.logger.info(f"Pipeline-Statistiken: {self.items_processed} verarbeitet, {self.items_dropped} verworfen")


class DuplicateFilterPipeline:
    """
    Pipeline zum Filtern von Duplikaten basierend auf der URL.
    """
    
    def __init__(self):
        self.seen_urls = set()
        self.duplicates_dropped = 0
        self.logger = logging.getLogger(__name__)
    
    def process_item(self, item, spider: Spider):
        """
        Prüft ob ein Item bereits basierend auf der URL gesehen wurde.
        
        Args:
            item: Das zu prüfende Item
            spider: Der Spider
            
        Returns:
            Item: Das Item wenn es neu ist
            
        Raises:
            DropItem: Wenn das Item ein Duplikat ist
        """
        adapter = ItemAdapter(item)
        url = adapter.get('url')
        
        if url in self.seen_urls:
            self.duplicates_dropped += 1
            self.logger.debug(f"Duplikat gefunden: {url}")
            raise DropItem(f"Duplicate item found: {url}")
        else:
            self.seen_urls.add(url)
            return item
    
    def close_spider(self, spider: Spider):
        """Logging der Pipeline-Statistiken."""
        self.logger.info(f"Duplikate-Pipeline: {self.duplicates_dropped} Duplikate entfernt")


class CSVExportPipeline:
    """
    Pipeline zum Exportieren von Items in eine CSV-Datei.
    
    Diese Pipeline erstellt eine CSV-Datei mit den extrahierten Daten
    und unterstützt verschiedene Item-Typen.
    """
    
    def __init__(self):
        self.files = {}
        self.writers = {}
        self.items_exported = 0
        self.logger = logging.getLogger(__name__)
    
    def open_spider(self, spider: Spider):
        """
        Initialisiert die CSV-Dateien für den Export.
        
        Args:
            spider: Der Spider der gestartet wird
        """
        # Basis-CSV für alle WebPageItems
        self._setup_csv_writer('webpages', [
            'title', 'url', 'domain', 'description', 'keywords', 
            'language', 'status_code', 'content_type', 'timestamp'
        ])
        
        # Spezielle CSV für NewsArticleItems
        self._setup_csv_writer('news', [
            'title', 'url', 'domain', 'author', 'publish_date', 
            'category', 'word_count', 'timestamp'
        ])
        
        # Spezielle CSV für TenderItems
        self._setup_csv_writer('tenders', [
            'tender_title', 'tender_id', 'organization', 'deadline', 
            'budget', 'category', 'location', 'url', 'timestamp'
        ])
        
        self.logger.info("CSV-Export-Pipeline initialisiert")
    
    def _setup_csv_writer(self, name: str, fieldnames: list):
        """
        Richtet einen CSV-Writer für einen bestimmten Item-Typ ein.
        
        Args:
            name: Name der CSV-Datei
            fieldnames: Liste der Spaltennamen
        """
        # Datenverzeichnis erstellen
        os.makedirs('data', exist_ok=True)
        
        filename = f'data/{name}.csv'
        file = open(filename, 'w', newline='', encoding='utf-8')
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        self.files[name] = file
        self.writers[name] = writer
        
        self.logger.info(f"CSV-Writer für {name} erstellt: {filename}")
    
    def process_item(self, item, spider: Spider):
        """
        Exportiert ein Item in die entsprechende CSV-Datei.
        
        Args:
            item: Das zu exportierende Item
            spider: Der Spider
            
        Returns:
            Item: Das unveränderte Item
        """
        adapter = ItemAdapter(item)
        
        # Item-Typ bestimmen und entsprechend exportieren
        if isinstance(item, NewsArticleItem):
            self._write_to_csv('news', adapter.asdict())
        elif isinstance(item, TenderItem):
            self._write_to_csv('tenders', adapter.asdict())
        elif isinstance(item, WebPageItem):
            self._write_to_csv('webpages', adapter.asdict())
        else:
            # Fallback für unbekannte Item-Typen
            self._write_to_csv('webpages', adapter.asdict())
        
        self.items_exported += 1
        return item
    
    def _write_to_csv(self, writer_name: str, item_dict: Dict[str, Any]):
        """
        Schreibt ein Item-Dictionary in die entsprechende CSV-Datei.
        
        Args:
            writer_name: Name des CSV-Writers
            item_dict: Dictionary mit Item-Daten
        """
        try:
            writer = self.writers.get(writer_name)
            if writer:
                # Listen und komplexe Objekte zu Strings konvertieren
                for key, value in item_dict.items():
                    if isinstance(value, (list, dict)):
                        item_dict[key] = json.dumps(value, ensure_ascii=False)
                    elif value is None:
                        item_dict[key] = ''
                
                writer.writerow(item_dict)
                self.files[writer_name].flush()  # Sofort schreiben
        except Exception as e:
            self.logger.error(f"Fehler beim CSV-Export: {e}")
    
    def close_spider(self, spider: Spider):
        """
        Schließt alle CSV-Dateien und gibt Statistiken aus.
        
        Args:
            spider: Der Spider der geschlossen wird
        """
        for file in self.files.values():
            file.close()
        
        self.logger.info(f"CSV-Export abgeschlossen: {self.items_exported} Items exportiert")


class JSONExportPipeline:
    """
    Pipeline zum Exportieren von Items in JSON-Format.
    """
    
    def __init__(self):
        self.file = None
        self.items_exported = 0
        self.logger = logging.getLogger(__name__)
    
    def open_spider(self, spider: Spider):
        """Öffnet die JSON-Datei für den Export."""
        os.makedirs('data', exist_ok=True)
        self.file = open('data/results.json', 'w', encoding='utf-8')
        self.file.write('[\n')
    
    def process_item(self, item, spider: Spider):
        """Exportiert ein Item als JSON."""
        adapter = ItemAdapter(item)
        
        if self.items_exported > 0:
            self.file.write(',\n')
        
        json.dump(adapter.asdict(), self.file, ensure_ascii=False, indent=2)
        self.items_exported += 1
        
        return item
    
    def close_spider(self, spider: Spider):
        """Schließt die JSON-Datei."""
        self.file.write('\n]')
        self.file.close()
        self.logger.info(f"JSON-Export abgeschlossen: {self.items_exported} Items")

