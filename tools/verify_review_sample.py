#!/usr/bin/env python3
"""Verify sample integrity and optionally exact provenance against the source ZIP."""
import argparse
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

# Keep verification read-only, including when run without Python's -B flag.
sys.dont_write_bytecode = True

try:
    from .build_review_sample import row_summary, render_html
except ImportError:
    from build_review_sample import row_summary, render_html

SOURCE_SHA = 'f73a7d457ef69be4848e0d169bafc157d0faa3b15b3b56eac43d6fdc17a38803'


def verify(root, source_zip=None):
    root = Path(root)
    manifest = json.loads((root / 'sample-manifest.json').read_text(encoding='utf-8'))
    assert manifest['source_zip_sha256'] == SOURCE_SHA
    expected = set(manifest['files']) | {'sample-manifest.json', 'SHA256SUMS'}
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    assert actual == expected, 'Unexpected or missing sample files'
    for name in expected:
        parts = PurePosixPath(name)
        assert not parts.is_absolute() and '..' not in parts.parts and '\\' not in name
        assert not any(p.is_symlink() for p in [root / name, *(root / name).parents]), 'Symlink not allowed'
    sums = {}
    for line in (root / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        sha, name = line.split('  ', 1)
        assert name not in sums, 'Duplicate checksum entry'
        sums[name] = sha
    assert set(sums) == expected - {'SHA256SUMS'}
    for name, sha in sums.items():
        data = (root / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == sha, 'Checksum mismatch: ' + name
        if name in manifest['files']:
            assert manifest['files'][name] == {'sha256': sha, 'bytes': len(data)}
    rows = json.loads((root / 'samples.json').read_text(encoding='utf-8'))
    assert len(rows) == manifest['row_count'] == 10
    assert len({r['instance_id'] for r in rows}) == manifest['distinct_instances'] == 10
    assert [r['row_id'] for r in rows] == [f'R{i:02}' for i in range(1, 11)]
    with (root / 'samples.csv').open(encoding='utf-8-sig', newline='') as f:
        csv_rows = list(csv.DictReader(f))
    assert len(csv_rows) == 10
    for original, csv_row in zip(rows, csv_rows):
        for key, value in original.items():
            value = str(value)
            if value.lstrip().startswith(('=', '+', '-', '@')):
                value = "'" + value
            assert csv_row[key] == value, 'CSV differs from JSON'
        assert original['specialist_validation'] == 'none'
        assert original['evidence_file'] in expected
        evidence = json.loads((root / original['evidence_file']).read_text(encoding='utf-8'))
        assert evidence['row_id'] == original['row_id']
        assert row_summary(int(original['row_id'][1:]), evidence['source_records']) == original
    assert sum(r['owner_review'].startswith('owner_accepted') for r in rows) == manifest['owner_accepted_exact_instances'] == 1
    assert (root / 'START_HERE.html').read_bytes() == render_html(rows), 'HTML differs from summary'
    assert (root / 'index.html').read_bytes() == render_html(rows), 'Site entry differs from summary'
    checked = 0
    if source_zip:
        source_zip = Path(source_zip)
        assert hashlib.sha256(source_zip.read_bytes()).hexdigest() == SOURCE_SHA, 'Source ZIP hash mismatch'
        with zipfile.ZipFile(source_zip) as source:
            cache = {}
            for row in rows:
                evidence = json.loads((root / row['evidence_file']).read_text(encoding='utf-8'))
                assert evidence['row_id'] == row['row_id']
                for item in evidence['source_records']:
                    name = 'candidate/' + item['source_artifact']
                    if name not in cache:
                        cache[name] = source.read(name).splitlines(keepends=True)
                    line = cache[name][item['source_line'] - 1]
                    assert hashlib.sha256(line).hexdigest() == item['source_line_sha256']
                    assert json.loads(line) == item['record'], 'Changed source record'
                    checked += 1
    return {'status': 'passed', 'rows': 10, 'files': len(expected),
            'source_records_compared': checked,
            'meaning': 'Integrity/provenance only, not scientific or legal validation'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root'); parser.add_argument('--source-zip')
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.source_zip), indent=2))
