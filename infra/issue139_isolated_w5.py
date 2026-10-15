#!/usr/bin/env python3
"""Isolated #139 browser rehearsal. Never names or mutates a DEV Docker resource."""
from __future__ import annotations
import hashlib, json, os, pathlib, re, secrets, select, shutil, subprocess, sys, time

ROOT=pathlib.Path(__file__).resolve().parents[1]
STATE=pathlib.Path('/home/empv26/.local/state/centrochange-single')
BACKUP=STATE/'issue139-restore-rehearsal/cc139-restore-20261014180948'
IMAGE='centrochange-single:issue139-isolated-w5'
PROJECT='cc139-w5-isolated'
SERVICES=('db','redis-cache','redis-queue','backend','websocket','queue-short','queue-long','scheduler','frontend')
RUN=STATE/'issue139-isolated-w5-runs'/(time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+f'-{os.getpid()}')

def call(*cmd,check=True,input=None):
    p=subprocess.run(cmd,input=input,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if check and p.returncode:
        raise RuntimeError(f'{cmd[0]} {cmd[1] if len(cmd)>1 else ""} exit {p.returncode}: {p.stderr[-450:]}')
    return p

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert os.geteuid()==0 and os.uname().nodename=='srv2033673'
    assert shutil.disk_usage('/var/lib/docker').free>8*1024**3
    assert int(next(x.split()[1] for x in pathlib.Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))>3*1024**2
    assert not call('docker','ps','-a','--filter',f'label=com.docker.compose.project={PROJECT}','-q').stdout.strip()
    assert not call('docker','network','ls','--filter',f'name=^{PROJECT}_net$','-q').stdout.strip()
    assert not call('docker','volume','ls','--filter',f'name=^{PROJECT}-','-q').stdout.strip()
    assert call('docker','image','inspect','--format','{{.Id}}',IMAGE).stdout.strip().startswith('sha256:')
    source=ROOT/'infra/compose.yaml'
    content=source.read_text()
    assert content.count('centrochange-dev')>=10
    content=content.replace('centrochange-dev','cc139-w5-isolated')
    content=content.replace('127.0.0.1:${HTTP_PORT', '127.0.0.2:${HTTP_PORT')
    assert '127.0.0.2:${HTTP_PORT' in content and 'centrochange-dev' not in content
    overlay='services:\n'
    for name in (*SERVICES,'configurator'):
        if name in ('db','redis-cache','redis-queue'): continue
        overlay+=f'  {name}:\n    image: {IMAGE}\n    pull_policy: never\n'
        if name=='frontend':
            overlay+='    networks:\n      cc139-w5-isolated-net:\n        aliases: [centrochange.local]\n'
    RUN.mkdir(mode=0o700,parents=True,exist_ok=False)
    (RUN/'compose.yaml').write_text(content)
    (RUN/'overlay.yaml').write_text(overlay)
    password=secrets.token_urlsafe(30)
    source_env=dict(line.split('=',1) for line in (STATE/'runtime.env').read_text().splitlines()
                    if '=' in line and not line.startswith('#'))
    assert source_env['SITE_NAME']=='centrochange.local' and source_env['HTTP_PORT']=='8082'
    (RUN/'env').write_text(f'SITE_NAME=centrochange.local\nHTTP_PORT=8082\nDB_PASSWORD={password}\n'
                           f'ADMIN_PASSWORD={source_env["ADMIN_PASSWORD"]}\n')
    (RUN/'env').chmod(0o600)
    compose=['docker','compose','--env-file',str(RUN/'env'),'-p',PROJECT,'-f',str(RUN/'compose.yaml'),'-f',str(RUN/'overlay.yaml')]
    config=json.loads(call(*compose,'config','--format','json').stdout)
    assert config['name']==PROJECT
    assert config['services']['frontend']['ports'][0]['host_ip']=='127.0.0.2'
    assert config['services']['frontend']['networks']['cc139-w5-isolated-net']['aliases']==['centrochange.local']
    for name in SERVICES:
        assert config['services'][name]['image']==IMAGE if name not in ('db','redis-cache','redis-queue') else True
    before=call('docker','ps','--filter','label=com.docker.compose.project=centrochange-dev','--format','{{.Names}} {{.Image}}').stdout
    try:
        call(*compose,'up','-d','--no-deps','db','redis-cache','redis-queue')
        for _ in range(45):
            states=call(*compose,'ps','--format','json').stdout
            if states.count('healthy')>=3: break
            time.sleep(2)
        else: raise RuntimeError('clone technical services not healthy')
        volume=f'{PROJECT}-sites'
        # Populate immutable app assets, then restore synthetic Site from a previously verified native backup.
        call('docker','run','--rm','--network','none','-u','0','-v',f'{volume}:/target','--entrypoint','sh',IMAGE,'-c',
             'cp -a /home/frappe/frappe-bench/sites/. /target/ && mkdir -p /target/centrochange.local/private/backups && chown -R 1000:0 /target')
        manifest=json.loads((BACKUP/'report.json').read_text())['backup']
        for kind,filename in [('db','database.sql.gz'),('public','files.tgz'),('private','private-files.tgz'),('config','site_config.json')]:
            src=BACKUP/filename
            assert digest(src)==manifest[kind]['sha256']
        # One-shot helper writes only the clone Site volume; no DEV mount exists.
        call('docker','run','--rm','--network','none','-u','0','-v',f'{volume}:/target','-v',f'{BACKUP}:/source:ro',
             '--entrypoint','sh',IMAGE,'-c',
             'cp /source/site_config.json /target/centrochange.local/site_config.json && '
             'cp /source/database.sql.gz /source/files.tgz /source/private-files.tgz '
             '/target/centrochange.local/private/backups/ && '
             'cp /source/common_site_config.json /target/common_site_config.json && '
             'chown -R 1000:0 /target/centrochange.local /target/common_site_config.json')
        restore=['bench','--site','centrochange.local','restore',
                 '/home/frappe/frappe-bench/sites/centrochange.local/private/backups/database.sql.gz',
                 '--db-root-password',password,
                 '--with-public-files','/home/frappe/frappe-bench/sites/centrochange.local/private/backups/files.tgz',
                 '--with-private-files','/home/frappe/frappe-bench/sites/centrochange.local/private/backups/private-files.tgz','--force']
        call(*compose,'run','--rm','--no-deps','backend',*restore)
        # Native restore grants the transient one-shot container address. The
        # cloned persistent services use their own addresses on this network.
        site_config=json.loads((BACKUP/'site_config.json').read_text())
        db_name=site_config['db_name']; db_password=site_config['db_password']
        assert re.fullmatch(r'_[a-z0-9]+',db_name) and "'" not in db_password
        sql=(f"CREATE USER IF NOT EXISTS '{db_name}'@'%' IDENTIFIED BY '{db_password}'; "
             f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_name}'@'%'; FLUSH PRIVILEGES;")
        call('docker','exec','-i',f'{PROJECT}-db-1','sh','-c',
             'mariadb -uroot -p"$MYSQL_ROOT_PASSWORD"',input=sql)
        call(*compose,'run','--rm','--no-deps','backend','bench','--site','centrochange.local','migrate')
        call(*compose,'run','--rm','--no-deps','backend','bench','--site','centrochange.local',
             'set-config','--parse','cc_operational_activation_allowed','["CC-HTTP-UAT0000001 A"]')
        activation='''import frappe
from centrochange_core.security.center_state import set_operational
frappe.init(site="centrochange.local",sites_path="/home/frappe/frappe-bench/sites");frappe.connect()
frappe.set_user("Administrator")
assert frappe.db.get_value("Branch","CC-HTTP-UAT0000001 A","cc_operational")==0
assert frappe.db.get_value("Branch","CC-HTTP-UAT0000001 B","cc_operational")==0
result=set_operational("CC-HTTP-UAT0000001 A","1","#139 isolated W5 rehearsal")
assert result["active"]==1 and not result["replay"]
frappe.db.commit();frappe.destroy()
'''
        call(*compose,'run','--rm','--no-deps','-e','FRAPPE_STREAM_LOGGING=1',
             '-w','/home/frappe/frappe-bench/sites','backend',
             '/home/frappe/frappe-bench/env/bin/python','-c',activation)
        call(*compose,'run','--rm','--no-deps','backend','bench','--site','centrochange.local',
             'set-config','--parse','cc_operational_activation_allowed','[]')
        call(*compose,'up','-d','--no-deps','backend','websocket','queue-short','queue-long','scheduler','frontend')
        for _ in range(45):
            r=call('curl','--silent','--output','/dev/null','--write-out','%{http_code}','--resolve','centrochange.local:8082:127.0.0.2',
                   'http://centrochange.local:8082/login',check=False)
            if r.stdout=='200':break
            time.sleep(2)
        else: raise RuntimeError('clone HTTP unavailable')
        print(json.dumps({'clone':'READY','project':PROJECT,'image':IMAGE,'host':'127.0.0.2:8082'}),flush=True)
        # Keep clone available for isolated W5 invocation from this process.
        print('Press Enter after W5; clone expires automatically in 30 minutes.',flush=True)
        select.select([sys.stdin],[],[],1800)
    finally:
        call(*compose,'down','-v','--remove-orphans',check=False)
        after=call('docker','ps','--filter','label=com.docker.compose.project=centrochange-dev','--format','{{.Names}} {{.Image}}').stdout
        if after!=before: raise RuntimeError('DEV service inventory changed during isolated rehearsal')
        print(json.dumps({'clone':'REMOVED','dev_inventory_unchanged':True}),flush=True)

if __name__=='__main__': main()
