#!/usr/bin/env python3
"""
Parsea feed.xml y genera archivos Markdown en _posts/ para Jekyll.
Uso: python3 scripts/parse_feed.py
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from html import unescape

FEED_PATH = os.path.join(os.path.dirname(__file__), '..', 'feed_original.xml')
POSTS_DIR = os.path.join(os.path.dirname(__file__), '..', '_posts')

NAMESPACES = {
    'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
    'atom': 'http://www.w3.org/2005/Atom',
}


def get_inner_xml(element):
    """Obtiene el contenido XML/HTML interior de un elemento."""
    text = element.text or ''
    for child in element:
        text += ET.tostring(child, encoding='unicode', method='html')
    return text


def clean_html(html_text):
    """Limpia el HTML del contenido del post."""
    if not html_text:
        return ''
    text = html_text.strip()
    # Eliminar los enlaces "Seguir leyendo" y "The post ... first appeared on"
    text = re.sub(r'<p>\s*The post\s*<a href=.*?</p>', '', text, flags=re.DOTALL)
    text = re.sub(r'<a href=[^>]*class="more-link"[^>]*>.*?</a>', '', text, flags=re.DOTALL)
    # Limpiar whitespace extra
    text = text.strip()
    return text


def slugify(title):
    """Genera un slug a partir del titulo del episodio."""
    slug = title.lower().strip()
    # Reemplazar caracteres especiales
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u', 'à': 'a', 'è': 'e', 'ì': 'i',
        'ò': 'o', 'ù': 'u',
    }
    for old, new in replacements.items():
        slug = slug.replace(old, new)
    # Solo alfanuméricos y guiones
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    # Limitar longitud
    if len(slug) > 60:
        slug = slug[:60].rstrip('-')
    return slug


def escape_yaml(text):
    """Escapa texto para valores YAML entre comillas dobles."""
    if not text:
        return ''
    text = text.strip()
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    # Reemplazar saltos de línea
    text = re.sub(r'\s*\n\s*', ' ', text)
    return text


def parse_date(date_str):
    """Parsea fecha RSS a datetime."""
    date_str = date_str.strip()
    # Formato: Fri, 18 Sep 2020 18:13:48 +0000
    try:
        return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
    except ValueError:
        return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S +0000')


def get_text(element, tag, ns=None):
    """Obtiene texto de un subelemento."""
    if ns:
        child = element.find(f'{{{NAMESPACES[ns]}}}{tag}')
    else:
        child = element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return ''


def main():
    os.makedirs(POSTS_DIR, exist_ok=True)

    tree = ET.parse(FEED_PATH)
    root = tree.getroot()
    channel = root.find('channel')
    items = channel.findall('item')

    print(f'Encontrados {len(items)} episodios')

    for item in items:
        title = get_text(item, 'title')
        link = get_text(item, 'link')
        pub_date_str = get_text(item, 'pubDate')
        guid = item.find('guid')
        guid_text = guid.text.strip() if guid is not None and guid.text else ''
        guid_permalink = guid.get('isPermaLink', 'true') if guid is not None else 'true'

        desc_el = item.find('description')
        description = get_inner_xml(desc_el) if desc_el is not None else ''

        # Enclosure
        enclosure = item.find('enclosure')
        audio_url = enclosure.get('url', '') if enclosure is not None else ''
        audio_length = enclosure.get('length', '') if enclosure is not None else ''
        audio_type = enclosure.get('type', '') if enclosure is not None else ''

        # iTunes metadata
        itunes_subtitle = get_text(item, 'subtitle', 'itunes')
        itunes_summary = get_text(item, 'summary', 'itunes')
        itunes_author = get_text(item, 'author', 'itunes')
        itunes_season = get_text(item, 'season', 'itunes')
        itunes_episode = get_text(item, 'episode', 'itunes')
        itunes_title = get_text(item, 'title', 'itunes')
        itunes_duration = get_text(item, 'duration', 'itunes')

        itunes_image_el = item.find(f'{{{NAMESPACES["itunes"]}}}image')
        itunes_image = itunes_image_el.get('href', '') if itunes_image_el is not None else ''

        # Parsear fecha
        pub_date = parse_date(pub_date_str)
        date_str = pub_date.strftime('%Y-%m-%d')
        date_full = pub_date.strftime('%Y-%m-%d %H:%M:%S %z')

        # Generar slug
        slug = slugify(title)
        filename = f'{date_str}-{slug}.md'
        filepath = os.path.join(POSTS_DIR, filename)

        # Limpiar descripcion para el contenido
        content = clean_html(description)

        # Front matter
        front_matter = f"""---
layout: post
title: "{escape_yaml(title)}"
date: {date_full}
guid: "{escape_yaml(guid_text)}"
permalink: /{slug}/
audio_url: "{audio_url}"
audio_length: "{audio_length}"
audio_type: "{audio_type}"
itunes_subtitle: "{escape_yaml(itunes_subtitle)}"
itunes_summary: "{escape_yaml(itunes_summary)}"
itunes_author: "{escape_yaml(itunes_author)}"
itunes_image: "{itunes_image}"
itunes_season: {itunes_season or '1'}
itunes_episode: {itunes_episode or '0'}
itunes_title: "{escape_yaml(itunes_title)}"
itunes_duration: "{itunes_duration}"
---
{content}
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(front_matter)

        print(f'  Generado: {filename}')

    print(f'\nTotal: {len(items)} posts generados en {POSTS_DIR}')


if __name__ == '__main__':
    main()
