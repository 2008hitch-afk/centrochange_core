#!/usr/bin/env python3
"""Native synthetic DEV backup, encrypted outside Git; never a production runbook."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tarfile
import tempfile
import uuid

CONTAINER='centrochange-dev-backend-1'
SITE='centrochange.local'


def run(args):
    result=subprocess.run(args,text=True,capture_output=True)
    if result.returncode:
        raise RuntimeError('Backup command failed: '+str(args[:3])+'; exit '+str(result.returncode))
    return result.stdout


def backup(destination):
    repository=Path(__file__).resolve().parent.parent
    destination=Path(destination).resolve()
    if destination==repository or repository in destination.parents:
        raise ValueError('Raw/encrypted backups and encryption keys must remain outside Git')
    if not shutil.which('gpg'):
        raise RuntimeError('GnuPG is required for authenticated encrypted DEV backup')
    check=run(['docker','exec',CONTAINER,'bench','--site',SITE,'execute','centrochange_core.dev_bootstrap.setup'])
    if not json.loads(check.strip()).get('synthetic_dev'):
        raise RuntimeError('Synthetic DEV guard did not pass')
    destination.mkdir(parents=True,exist_ok=True,mode=0o700)
    job=Path(tempfile.mkdtemp(prefix='cc-dev-backup-',dir=destination))
    os.chmod(job,0o700)
    remote='/tmp/cc-dev-backup-'+uuid.uuid4().hex
    raw=job/'raw'
    archive=job/'backup.tar'
    key=job/'dev-only.key'
    encrypted=job/'backup.tar.gpg'
    home=job/'gnupg'
    inventory=[]
    try:
        run(['docker','exec',CONTAINER,'bench','--site',SITE,'backup','--with-files','--compress','--backup-path',remote])
        run(['docker','cp',CONTAINER+':'+remote,str(raw)])
        os.chmod(raw,0o700)
        files=list(raw.iterdir())
        kinds={
            'database':lambda name:'database' in name,
            'public_files':lambda name:'files' in name and 'private' not in name,
            'private_files':lambda name:'private-files' in name,
            'configuration':lambda name:'site_config' in name,
        }
        for kind,predicate in kinds.items():
            matches=[path for path in files if predicate(path.name)]
            if len(matches)!=1 or not matches[0].is_file() or matches[0].stat().st_size==0:
                raise RuntimeError('Missing or ambiguous native backup component: '+kind)
            path=matches[0]
            inventory.append({'kind':kind,'size':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        with tarfile.open(archive,'w') as tar:
            for path in files:
                tar.add(path,arcname=path.name)
        os.chmod(archive,0o600)
        with os.fdopen(os.open(key,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),'w') as stream:
            stream.write(secrets.token_urlsafe(64))
        home.mkdir(mode=0o700)
        run(['gpg','--homedir',str(home),'--batch','--yes','--pinentry-mode','loopback','--passphrase-file',str(key),
             '--symmetric','--cipher-algo','AES256','--output',str(encrypted),str(archive)])
        os.chmod(encrypted,0o600)
        # Integrity verification decrypts through a pipe; no second raw archive remains.
        verified=subprocess.run(['gpg','--homedir',str(home),'--batch','--pinentry-mode','loopback',
            '--passphrase-file',str(key),'--decrypt',str(encrypted)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if verified.returncode or hashlib.sha256(verified.stdout).digest()!=hashlib.sha256(archive.read_bytes()).digest():
            raise RuntimeError('Encrypted archive integrity verification failed')
        report={'status':'PASS','site':SITE,'components':inventory,'encrypted_sha256':hashlib.sha256(encrypted.read_bytes()).hexdigest(),
            'encrypted_size':encrypted.stat().st_size,'raw_files_removed':True,'restore_tested':False,
            'backup_directory':str(job),'key_policy':'0600 local DEV-only key; production key custody and retention remain gated'}
        (job/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
        os.chmod(job/'inventory.json',0o600)
        return report
    finally:
        if raw.exists():
            shutil.rmtree(raw)
        archive.unlink(missing_ok=True)
        # This exact generated DEV-only directory contains only this invocation's native output.
        run(['docker','exec',CONTAINER,'rm','-rf','--',remote])


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--destination',default='/tmp/centrochange-dev-backups')
    args=parser.parse_args()
    os.umask(0o077)
    print(json.dumps(backup(args.destination)))
