"""Offline checks of public HTML, linked assets, facts and deployment boundaries."""
from html.parser import HTMLParser
import json
import posixpath
import re
import unittest
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from tools.build_release import ROOT, collect_sources

BASE = 'https://vence15008-ai.github.io/codex-quota-header-public/'


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.elements = []
        self.ids = []
        self.json_ld = []
        self.in_schema = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'script':
            self.in_schema = attrs.get('type') == 'application/ld+json'

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_schema = False

    def handle_data(self, data):
        if self.in_schema and data.strip():
            self.json_ld.append(json.loads(data))


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.sources = collect_sources()
        self.facts = json.loads(self.sources['docs/project-facts.json'])

    def test_metadata_language_and_facts(self):
        for name, lang, url in [('site/index.html', 'zh-CN', BASE),
                                ('site/en/index.html', 'en', BASE + 'en/')]:
            text = self.sources[name].decode()
            page = Page(text)
            self.assertIn(('html', {'lang': lang}), page.elements)
            self.assertEqual(sum(t == 'h1' for t, _ in page.elements), 1)
            self.assertIn(('link', {'rel': 'canonical', 'href': url}), page.elements)
            alternates = {a['hreflang']: a['href'] for t, a in page.elements
                          if t == 'link' and a.get('rel') == 'alternate'}
            self.assertEqual(alternates, {'zh-CN': BASE, 'en': BASE + 'en/', 'x-default': BASE})
            meta = {a['name']: a.get('content') for t, a in page.elements
                    if t == 'meta' and 'name' in a}
            self.assertGreater(len(meta['description']), 70)
            self.assertIn('index,follow', meta['robots'])
            self.assertEqual(len(page.json_ld), 1)
            schema = page.json_ld[0]
            self.assertEqual(schema['name'], self.facts['name'])
            self.assertEqual(schema['softwareVersion'], self.facts['softwareVersion'])
            self.assertEqual(schema['url'], url)
            self.assertEqual(schema['license'], self.facts['license']['url'])
            self.assertNotIn('aggregateRating', schema)
            self.assertNotIn('offers', schema)
            self.assertIn('CDP', text)
            self.assertIn('60', text)
            self.assertEqual(len(page.ids), len(set(page.ids)))
        home = Page(self.sources['site/index.html'].decode())
        self.assertEqual(sum(t == 'meta' and a.get('name') == 'google-site-verification'
                             for t, a in home.elements), 1)

    def test_internal_links_and_assets_exist(self):
        for name in ('site/index.html', 'site/en/index.html'):
            page = Page(self.sources[name].decode())
            for tag, attrs in page.elements:
                for field in ('href', 'src'):
                    link = attrs.get(field)
                    if not link:
                        continue
                    parts = urlsplit(link)
                    if parts.scheme or parts.netloc:
                        self.assertEqual(parts.scheme, 'https')
                        continue
                    target = posixpath.normpath(posixpath.join(posixpath.dirname(name), parts.path))
                    if not parts.path:
                        target = name
                    elif parts.path.endswith('/'):
                        target += '/index.html'
                    self.assertTrue(target.startswith('site/'), target)
                    self.assertIn(target, self.sources, link)
                    if parts.fragment:
                        self.assertIn(parts.fragment, Page(self.sources[target].decode()).ids)

    def test_no_runtime_javascript_tracking_or_external_assets(self):
        for name, data in self.sources.items():
            if name.startswith('site/') and name.endswith('.html'):
                for tag, attrs in Page(data.decode()).elements:
                    if tag == 'script':
                        self.assertEqual(attrs.get('type'), 'application/ld+json')
                        self.assertNotIn('src', attrs)
                    self.assertNotEqual(tag, 'iframe')
                    if tag == 'link' and attrs.get('rel') in ('stylesheet', 'icon'):
                        self.assertFalse(urlsplit(attrs['href']).scheme)
        css = self.sources['site/style.css'].decode()
        self.assertNotIn('@import', css)
        self.assertNotIn('url(', css)
        self.assertNotIn('site/robots.txt', self.sources)

    def test_sitemap_matches_canonical_pages(self):
        xml = ET.fromstring(self.sources['site/sitemap.xml'])
        urls = [node.text for node in xml.findall('{*}url/{*}loc')]
        self.assertEqual(urls, [BASE, BASE + 'en/'])
        self.assertEqual(self.facts['projectWebsite'], BASE)

    def test_pages_deployment_is_scoped_and_pinned(self):
        workflow = self.sources['.github/workflows/pages.yml'].decode()
        self.assertIn('branches: [main]', workflow)
        self.assertIn("if: github.ref == 'refs/heads/main'", workflow)
        self.assertIn('path: site', workflow)
        self.assertIn('needs: build', workflow)
        self.assertIn('python -m unittest discover -s tests -v', workflow)
        self.assertNotIn('pull_request', workflow)
        self.assertNotIn('secrets.', workflow)
        for ref in re.findall(r'uses: (\S+)', workflow):
            self.assertRegex(ref, r'^actions/[a-z-]+@[a-f0-9]{40}$')


if __name__ == '__main__':
    unittest.main()
