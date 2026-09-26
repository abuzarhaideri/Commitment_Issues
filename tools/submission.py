"""Build an allowlisted submission archive; never package local repair checkouts."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent.parent
DIRECTORIES = ('harness', 'tests', 'benchmarks', 'config', 'docs', 'tools', '.github')
ROOT_FILES = ('Makefile', 'README.md', '.gitignore', '.env.example', 'pyproject.toml', 'requirements.txt')
KEY_PATTERNS = (r'AIza[0-9A-Za-z_-]{30,}', r'\bsk-(?:proj-)?[0-9A-Za-z_-]{20,}', r'\bgh[pousr]_[0-9A-Za-z]{30,}')


def source_files():
    files = [ROOT / name for name in ROOT_FILES if (ROOT / name).is_file()]
    for name in DIRECTORIES:
        if (ROOT / name).exists():
            files.extend(p for p in (ROOT / name).rglob('*') if p.is_file()
                         and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.pyo'))
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError('Submission contains a symlink or external path')
        if any(re.search(pattern, path.read_text(errors='replace')) for pattern in KEY_PATTERNS):
            raise ValueError(f'Possible credential format in {path.relative_to(ROOT)}; inspect locally')
    return sorted(files)


def package(output):
    files = source_files()
    output.mkdir(parents=True, exist_ok=True)
    profile = json.loads((ROOT / 'config/evaluation.json').read_text())
    manifest = {'profile_status': profile.get('profile_status', 'configured'),
                'secret_scan': 'limited key-format scan, not a full security audit',
                'files': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    encoded = (json.dumps(manifest, indent=2) + '\n').encode()
    archive = output / 'commitment-issues-submission.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            info = zipfile.ZipInfo(str(path.relative_to(ROOT)), date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, path.read_bytes())
        bundle.writestr('submission-manifest.json', encoded)
    (output / 'submission-manifest.json').write_bytes(encoded)
    print(f'Packaged {len(files)} allowlisted files: {archive}')
    return archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/submission')
    args = parser.parse_args()
    package(args.output)
