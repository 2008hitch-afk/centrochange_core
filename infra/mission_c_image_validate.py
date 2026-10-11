"""Verify a Mission C OCI COPY delta against changed app files, without Docker."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def digest(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def validate(archive, source, base_revision):
    source = Path(source)
    head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    changed = subprocess.check_output([
        'git', '-C', str(source), 'diff', '--name-only', base_revision, head, '--',
        'app/centrochange_core/centrochange_core',
    ], text=True).splitlines()
    with tarfile.open(archive, 'r:') as outer:
        index = json.load(outer.extractfile('index.json'))
        descriptor = index['manifests'][0]
        def read(descriptor):
            content = outer.extractfile('blobs/sha256/' + descriptor['digest'].split(':')[1]).read()
            if digest(content) != descriptor['digest'] or len(content) != descriptor['size']:
                raise ValueError('OCI descriptor hash or length mismatch')
            return content
        manifest = json.loads(read(descriptor))
        config = json.loads(read(manifest['config']))
        if config['config']['Labels']['org.opencontainers.image.revision'] != head:
            raise ValueError('OCI revision differs from source HEAD')
        layer = manifest['layers'][-1]
        raw = gzip.decompress(read(layer))
        if digest(raw) != config['rootfs']['diff_ids'][-1]:
            raise ValueError('OCI uncompressed layer hash mismatch')
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as contents:
            copied = {item.name: contents.extractfile(item).read() for item in contents if item.isfile()}
    prefix = 'home/frappe/frappe-bench/apps/centrochange_core/'
    missing = []
    for name in changed:
        relative = name.removeprefix('app/centrochange_core/')
        path = prefix + relative
        if copied.get(path) != (source / name).read_bytes():
            missing.append(name)
    if missing:
        raise ValueError('Changed app files missing or different in OCI delta: ' + ', '.join(missing))
    return {'status': 'PASS', 'revision': head, 'changed_app_files': len(changed), 'copied_files': len(copied), 'image_manifest': descriptor['digest']}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--archive', required=True)
    p.add_argument('--source', required=True)
    p.add_argument('--base-revision', required=True)
    args = p.parse_args()
    print(json.dumps(validate(args.archive, args.source, args.base_revision)))
