import hashlib
import json
import re
import unittest

from tools.build_release import ROOT, collect_sources


class DiscoverabilityTests(unittest.TestCase):
    def test_tracked_source_manifest_is_current(self):
        sources = collect_sources()
        manifest = json.loads((ROOT / 'SOURCE-MANIFEST.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest, {name: hashlib.sha256(data).hexdigest() for name, data in sources.items()})

    def test_facts_match_package_and_implementation(self):
        sources = collect_sources()
        facts = json.loads(sources['docs/project-facts.json'])
        package = json.loads(sources['package.json'])
        self.assertEqual(facts['softwareVersion'], package['version'])
        self.assertEqual(facts['name'], 'Codex Quota Header')
        self.assertEqual(package['repository']['url'], facts['canonicalRepository'] + '.git')
        self.assertEqual(package['homepage'], facts['projectWebsite'])
        self.assertEqual(facts['quotaDataSource'], 'account/rateLimits/read')
        self.assertEqual(facts['refreshSeconds'], 60)
        self.assertEqual(facts['weeklyWindowMinutes'], 10080)
        self.assertEqual(facts['shortWindowMinutes'], 300)
        for field in ('officialOpenAIExtension', 'tracksTokens', 'tracksUsdCost',
                      'attributesPerDeviceUsage', 'bypassesAccountLimits', 'addsTelemetry'):
            self.assertIs(facts[field], False)
        self.assertTrue(facts['requiresPrivilegedLocalCdp'])
        self.assertEqual(package['license'], 'SEE LICENSE IN LICENSE')
        self.assertFalse(facts['license']['claimsOsiApproval'])
        self.assertIn('account/rateLimits/read', sources['account_reader.py'].decode())
        self.assertIn('commands.get(timeout=60)', sources['quota_feed.py'].decode())

    def test_keywords_are_relevant_and_not_misleading(self):
        package = json.loads(collect_sources()['package.json'])
        keywords = package['keywords']
        self.assertEqual(len(keywords), len(set(keywords)))
        self.assertLessEqual(len(keywords), 20)
        for keyword in keywords:
            self.assertRegex(keyword, r'^[a-z0-9][a-z0-9-]{0,49}$')
        for unsupported in ('mit', 'macos', 'linux', 'token-tracker', 'billing', 'quota-bypass'):
            self.assertNotIn(unsupported, keywords)

    def test_index_links_point_to_real_packaged_docs(self):
        sources = collect_sources()
        repo = json.loads(sources['docs/project-facts.json'])['canonicalRepository']
        links = re.findall(r'\]\(([^)]+)\)', sources['llms.txt'].decode())
        self.assertGreaterEqual(len(links), 7)
        for link in links:
            if link.startswith(repo + '/blob/main/'):
                self.assertIn(link.removeprefix(repo + '/blob/main/'), sources)
            else:
                self.assertEqual(link, repo + '/actions/workflows/test.yml')

    def test_documentation_keeps_identity_and_limits_visible(self):
        sources = collect_sources()
        for name in ('README.md', 'README.en.md', 'docs/FAQ.md', 'docs/PROJECT-FACTS.md'):
            text = sources[name].decode()
            self.assertIn('Codex Quota Header', text)
            self.assertIn('Windows', text)
            self.assertIn('CDP', text)
        faq = sources['docs/FAQ.md'].decode()
        self.assertEqual(len(re.findall(r'^## \d+\.', faq, re.M)), 12)
        self.assertIn('not a guaranteed crawler integration or ranking signal', sources['README.en.md'].decode())


if __name__ == '__main__':
    unittest.main()
