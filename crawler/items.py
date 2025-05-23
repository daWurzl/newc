# -*- coding: utf-8 -*-
"""
Scrapy Items für die Definition der extrahierten Datenstrukturen.

Diese Datei definiert die Items (Datencontainer) die vom Spider
zurückgegeben werden. Items bieten eine strukturierte Art der
Datenvalidierung und -verarbeitung.
"""

import scrapy
from scrapy import Field
from itemadapter import ItemAdapter
from datetime import datetime


class WebPageItem(scrapy.Item):
    """
    Item-Container für extrahierte Webseiten-Daten.
    
    Dieses Item repräsentiert alle relevanten Informationen,
    die von einer gecrawlten Webseite extrahiert werden können.
    """
    
    # Grundlegende Seiteninformationen
    title = Field(
        serializer=str,
        description="Seitentitel aus <title> oder <h1> Tag"
    )
    
    url = Field(
        serializer=str,
        description="Vollständige URL der gecrawlten Seite"
    )
    
    domain = Field(
        serializer=str,
        description="Domain der URL (z.B. example.com)"
    )
    
    # Meta-Informationen
    description = Field(
        serializer=str,
        description="Meta-Description der Seite"
    )
    
    keywords = Field(
        serializer=str,
        description="Meta-Keywords der Seite"
    )
    
    language = Field(
        serializer=str,
        description="Sprache der Seite (aus lang-Attribut)"
    )
    
    # Technische Informationen
    status_code = Field(
        serializer=int,
        description="HTTP-Status-Code der Response"
    )
    
    content_type = Field(
        serializer=str,
        description="Content-Type der Response"
    )
    
    # Erweiterte Daten
    internal_links = Field(
        serializer=list,
        description="Liste interner Links auf der Seite"
    )
    
    screenshot_path = Field(
        serializer=str,
        description="Pfad zum Screenshot der Seite"
    )
    
    # Zeitstempel
    timestamp = Field(
        serializer=str,
        description="Zeitpunkt der Extraktion (ISO-Format)"
    )
    
    def __setitem__(self, key, value):
        """
        Überschreibt die Standard-Setter-Methode um automatisch
        einen Zeitstempel hinzuzufügen.
        """
        if key == 'timestamp' and not value:
            value = datetime.now().isoformat()
        super(WebPageItem, self).__setitem__(key, value)


class NewsArticleItem(scrapy.Item):
    """
    Spezielles Item für Nachrichtenartikel mit erweiterten Feldern.
    
    Dieses Item erweitert die Basis-Webseiten-Daten um spezifische
    Informationen für Nachrichtenartikel.
    """
    
    # Basis-Felder von WebPageItem
    title = Field()
    url = Field()
    domain = Field()
    description = Field()
    
    # Artikel-spezifische Felder
    author = Field(
        serializer=str,
        description="Autor des Artikels"
    )
    
    publish_date = Field(
        serializer=str,
        description="Veröffentlichungsdatum des Artikels"
    )
    
    category = Field(
        serializer=str,
        description="Kategorie/Rubrik des Artikels"
    )
    
    tags = Field(
        serializer=list,
        description="Tags/Schlagwörter des Artikels"
    )
    
    article_text = Field(
        serializer=str,
        description="Volltext des Artikels"
    )
    
    image_urls = Field(
        serializer=list,
        description="URLs der Bilder im Artikel"
    )
    
    word_count = Field(
        serializer=int,
        description="Wortanzahl des Artikels"
    )


class TenderItem(scrapy.Item):
    """
    Item für Ausschreibungen/Tender-Daten.
    
    Speziell für das Crawlen von Ausschreibungsportalen
    und Tender-Webseiten.
    """
    
    # Ausschreibungs-Informationen
    tender_title = Field(
        serializer=str,
        description="Titel der Ausschreibung"
    )
    
    tender_id = Field(
        serializer=str,
        description="Eindeutige ID der Ausschreibung"
    )
    
    organization = Field(
        serializer=str,
        description="Ausschreibende Organisation"
    )
    
    deadline = Field(
        serializer=str,
        description="Bewerbungsfrist"
    )
    
    budget = Field(
        serializer=str,
        description="Budget/Auftragswert"
    )
    
    category = Field(
        serializer=str,
        description="Kategorie der Ausschreibung"
    )
    
    location = Field(
        serializer=str,
        description="Ort der Ausführung"
    )
    
    contact_info = Field(
        serializer=dict,
        description="Kontaktinformationen"
    )
    
    requirements = Field(
        serializer=str,
        description="Anforderungen an Bewerber"
    )
    
    url = Field()
    timestamp = Field()
