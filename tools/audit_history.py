"""Read-only limited-pattern audit of all reachable Git blobs; never print secrets."""
import subprocess

from build_release import ROOT, findings


def main() -> None:
    rows = subprocess.check_output(['git', 'rev-list', '--objects', '--all'], cwd=ROOT).splitlines()
    seen = set()
    issues = []
    for row in rows:
        object_id = row.split(b' ', 1)[0].decode('ascii')
        if object_id in seen:
            continue
        kind = subprocess.check_output(['git', 'cat-file', '-t', object_id], cwd=ROOT).strip()
        if kind != b'blob':
            continue
        seen.add(object_id)
        data = subprocess.check_output(['git', 'cat-file', 'blob', object_id], cwd=ROOT)
        try:
            detected = findings(data)
        except UnicodeDecodeError:
            detected = ['binary blob: manual review required']
        if detected:
            # Object id is sufficient to inspect privately; no matched content/path echoed.
            issues.append((object_id, detected))
    print(f'Scanned {len(seen)} reachable Git blobs; limited patterns only.')
    for object_id, detected in issues:
        print(object_id, ':', ', '.join(detected))
    if issues:
        raise SystemExit(1)
    print('No configured patterns detected. Review author metadata, filenames and all refs separately before publishing.')


if __name__ == '__main__':
    main()
