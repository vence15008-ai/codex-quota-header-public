import hashlib
import json
import re
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.build_release import SOURCES, collect_sources, findings, write_archive


class ReleaseTests(unittest.TestCase):
    def test_sources_are_safe_and_runtime_never_allowed(self):
        sources = collect_sources()
        self.assertEqual(set(sources), set(SOURCES))
        self.assertEqual(len(SOURCES), len(set(SOURCES)))
        for name in SOURCES:
            self.assertNotIn(name.split('/')[0], ('.git', 'runtime', 'dist', '.env'))
            self.assertNotIn(Path(name).suffix.lower(), ('.png', '.log', '.lnk', '.exe', '.zip'))

    def test_archive_reproducible_with_manifest(self):
        sources = collect_sources()
        with tempfile.TemporaryDirectory() as folder:
            first, second = Path(folder) / 'one.zip', Path(folder) / 'two.zip'
            write_archive(first, sources, '0.1.0')
            write_archive(second, sources, '0.1.0')
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                prefix = 'codex-quota-header-0.1.0/'
                self.assertEqual(len(archive.namelist()), len(SOURCES) + 1)
                manifest = json.loads(archive.read(prefix + 'SOURCE-MANIFEST.json'))
                for name, digest in manifest.items():
                    self.assertEqual(hashlib.sha256(archive.read(prefix + name)).hexdigest(), digest)

    def test_finite_pattern_scan_and_no_secret_echo(self):
        example = ('ghp_' + 'A' * 36).encode()
        self.assertEqual(findings(example), ['GitHub token'])
        self.assertEqual(findings(b'ordinary documentation'), [])

    def test_unknown_archive_input_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                write_archive(Path(folder) / 'bad.zip', {'runtime/secret.json': b'{}'}, '0.1.0')

    def test_documentation_relative_links_are_packaged(self):
        sources = collect_sources()
        for name, data in sources.items():
            if not name.endswith('.md'):
                continue
            for link in re.findall(r'\]\(([^)]+)\)', data.decode('utf-8')):
                if '://' in link or link.startswith('#'):
                    continue
                target = (Path(name).parent / link.split('#')[0]).as_posix()
                self.assertIn(target, sources, f'{name}: broken or unpackaged link')

    def test_custom_license_metadata_and_notification_channel(self):
        sources = collect_sources()
        package = json.loads(sources['package.json'])
        tracker = 'https://github.com/vence15008-ai/codex-quota-header-public/issues'
        self.assertEqual(package['license'], 'SEE LICENSE IN LICENSE')
        self.assertEqual(package['bugs']['url'], tracker)
        license_text = sources['LICENSE'].decode()
        self.assertTrue(license_text.startswith('Codex Quota Header Notification License 1.0'))
        self.assertIn(tracker, license_text)
        self.assertIn('No source-code disclosure', license_text)
        self.assertIn('You do not need approval', license_text)
        self.assertIn('does not withdraw', license_text)
        for name in ('README.md', 'README.en.md'):
            self.assertIn(tracker, sources[name].decode())
            self.assertIn('Notification License 1.0', sources[name].decode())
        template = sources['.github/ISSUE_TEMPLATE/usage_notice.md'].decode()
        self.assertIn('[Usage notice]', template)
        self.assertIn('No fee, approval', template)


if __name__ == '__main__':
    unittest.main()
