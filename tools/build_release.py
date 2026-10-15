"""Build an allowlisted, reproducible source archive; never package the worktree wholesale."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    '.gitattributes', '.gitignore', 'README.md', 'README.en.md', 'LICENSE',
    'SECURITY.md', 'CONTRIBUTING.md', 'CHANGELOG.md', 'package.json',
    'account_reader.py', 'cdp_bridge.cjs', 'codex_quota_widget.py', 'header.js',
    'make_launchers.ps1', 'manage.ps1', 'quota_feed.py', 'quota_model.py', 'win32_job.py',
    'tests/bridge.test.cjs', 'tests/launcher.test.cjs', 'tests/preview.html',
    'tests/test_account_reader.py', 'tests/test_quota_model.py', 'tests/test_release.py',
    'tools/apply_header.cjs', 'tools/check_layout.cjs', 'tools/inspect_header.cjs',
    'tools/test_refresh.cjs', 'tools/build_release.py', 'tools/audit_history.py',
    'docs/header-demo.svg', 'docs/RELEASING.md', '.github/workflows/test.yml',
    '.github/ISSUE_TEMPLATE/bug_report.md', '.github/ISSUE_TEMPLATE/feature_request.md',
    '.github/ISSUE_TEMPLATE/usage_notice.md',
    '.github/pull_request_template.md',
    'llms.txt', 'docs/PROJECT-FACTS.md', 'docs/project-facts.json',
    'docs/FAQ.md', 'docs/DISCOVERABILITY.md', 'tests/test_discoverability.py',
    'site/index.html', 'site/en/index.html', 'site/style.css', 'site/favicon.svg',
    'site/sitemap.xml', 'site/llms.txt', '.github/workflows/pages.yml', 'tests/test_site.py',
)
# Heuristics, not proof that arbitrary text is safe. Never print matched values.
PATTERNS = {
    'private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'GitHub token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    'API key': re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b'),
    'absolute user path': re.compile(r'[A-Za-z]:[\\/]Users[\\/][A-Za-z0-9_.-]+[\\/]', re.I),
}


def findings(data: bytes) -> list[str]:
    text = data.decode('utf-8')
    return [name for name, pattern in PATTERNS.items() if pattern.search(text)]


def collect_sources(root: Path = ROOT) -> dict[str, bytes]:
    result = {}
    for name in sorted(SOURCES):
        source = root / name
        source.resolve().relative_to(root.resolve())
        if any(p.is_symlink() for p in (source, *source.parents) if p != root.parent):
            raise ValueError(f'Symlink in release input: {name}')
        data = source.read_bytes().replace(b'\r\n', b'\n')
        issues = findings(data)
        if issues:
            raise ValueError(f'Release audit: {name}: {", ".join(issues)}')
        result[name] = data
    return result


def write_archive(output: Path, sources: dict[str, bytes], version: str) -> None:
    prefix = f'codex-quota-header-{version}'
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sources.items()}
    entries = dict(sources)
    entries['SOURCE-MANIFEST.json'] = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            relative = PurePosixPath(name)
            if relative.is_absolute() or '..' in relative.parts or name not in (*SOURCES, 'SOURCE-MANIFEST.json'):
                raise ValueError('Non-allowlisted archive entry')
            info = zipfile.ZipInfo(f'{prefix}/{name}', date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update-manifest', action='store_true', help='Refresh the tracked source manifest explicitly.')
    args = parser.parse_args()
    sources = collect_sources()
    version = json.loads(sources['package.json'])['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?', version):
        raise ValueError('Invalid release version')
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    output = destination / f'codex-quota-header-{version}-source.zip'
    if output.is_symlink() or destination.is_symlink():
        raise ValueError('Release output must not be a symlink')
    write_archive(output, sources, version)
    if args.update_manifest:
        tracked_manifest = ROOT / 'SOURCE-MANIFEST.json'
        if tracked_manifest.is_symlink():
            raise ValueError('Source manifest must not be a symlink')
        manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sources.items()}
        tracked_manifest.write_bytes((json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode('utf-8'))
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum = output.with_suffix('.zip.sha256')
    if checksum.is_symlink():
        raise ValueError('Checksum must not be a symlink')
    checksum.write_text(f'{digest}  {output.name}\n', encoding='ascii')
    print(f'Audited {len(sources)} allowlisted source files (limited pattern scan, not a security guarantee).')
    print(f'Archive: dist/{output.name}')
    print(f'SHA256: {digest}')


if __name__ == '__main__':
    main()
