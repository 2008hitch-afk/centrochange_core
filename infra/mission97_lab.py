#!/usr/bin/env python3
"""Owner-authorized #97 disposable synthetic lab, never targets shared UAT."""
import argparse, io, json, os, secrets, subprocess, tarfile
from pathlib import Path
import yaml

PROJECT='centrochange-m97-lab'
SITE='mission97.local'
PORT=8097
ROOT=Path(__file__).resolve().parent.parent
PRIVATE=Path('/tmp/centrochange-m97-lab')

def run(argv, **kwargs):
    return subprocess.run(argv, check=True, **kwargs)

def compose(image):
    config=yaml.safe_load((ROOT/'infra/compose.yaml').read_text())
    config['name']=PROJECT
    config.pop('x-app-image');config.pop('x-configured-app')
    config['volumes']={key:{'name':key.replace('centrochange-dev',PROJECT)} for key in config['volumes']}
    config['networks']['centrochange-dev-net']['name']=PROJECT+'-net'
    for service in config['services'].values():
        if 'build' in service:
            service.pop('build');service.pop('pull_policy',None);service['image']=image
    PRIVATE.mkdir(mode=0o700,exist_ok=True)
    env=PRIVATE/'runtime.env'
    if not env.exists():
        env.write_text(f'SITE_NAME={SITE}\nHTTP_PORT={PORT}\nDB_PASSWORD={secrets.token_hex(24)}\nADMIN_PASSWORD={secrets.token_hex(24)}\n');env.chmod(0o600)
    path=PRIVATE/'compose.yaml';path.write_text(yaml.safe_dump(config));path.chmod(0o600)
    return ['docker','compose','--project-name',PROJECT,'--env-file',str(env),'-f',str(path)]

def execute(code):
    prefix=f"import frappe,json\nfrappe.init(site={SITE!r},sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')\n"
    result=subprocess.run(['docker','exec','-i','-e','FRAPPE_STREAM_LOGGING=1','-w','/home/frappe/frappe-bench',PROJECT+'-backend-1','env/bin/python'],input=prefix+code,capture_output=True,text=True)
    if result.returncode:
        (PRIVATE/'execute-private.log').write_text(result.stdout+result.stderr)
        raise RuntimeError('Isolated execution failed; diagnostic in private lab directory')
    return result.stdout

def isolation():
    items=json.loads(subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project='+PROJECT],text=True).strip() and subprocess.check_output(['docker','inspect']+subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project='+PROJECT],text=True).split(),text=True) or '[]')
    assert items
    for item in items:
        assert item['Config']['Labels']['com.docker.compose.project']==PROJECT
        for mount in item['Mounts']:
            assert mount['Type']=='volume', 'Source or host bind forbidden'
            if not mount['Name'].startswith(PROJECT+'-'):
                assert mount['Destination']=='/home/frappe/frappe-bench/logs', 'Unexpected anonymous mount'
                users=subprocess.check_output(['docker','ps','-aq','--no-trunc','--filter','volume='+mount['Name']],text=True).split()
                assert users==[item['Id']], 'Anonymous logs volume must be exclusive to isolated container'
        assert all(key.startswith(PROJECT) for key in item['NetworkSettings']['Networks'])
        for ports in item['NetworkSettings']['Ports'].values():
            if ports:assert all(p['HostIp']=='127.0.0.1' and p['HostPort']==str(PORT) for p in ports)
    return {'project':PROJECT,'site':SITE,'port':PORT,'isolated_mounts_network_ports':True,'shared_uat_mutated':False}

def main():
    os.umask(0o077)
    p=argparse.ArgumentParser();p.add_argument('action',choices=['up','redeploy','build','isolation','read-hooks','seed']);p.add_argument('--image',default='centrochange-uat:goal02-20261008-rc22');p.add_argument('--source-ref');a=p.parse_args()
    if a.action=='build':
        sha=subprocess.check_output(['git','rev-parse',a.source_ref+'^{commit}'],cwd=ROOT,text=True).strip()
        assert a.image.startswith('centrochange-m97:')
        archive=subprocess.check_output(['git','archive',sha],cwd=ROOT)
        source=PRIVATE/('source-'+sha);source.mkdir(parents=True,exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(archive)) as stream:stream.extractall(source,filter='data')
        with (PRIVATE/'build.log').open('w') as log:run(['docker','build','--label','org.opencontainers.image.revision='+sha,'-t',a.image,'-f','infra/Dockerfile','.'],cwd=source,stdout=log,stderr=subprocess.STDOUT)
        print(json.dumps({'source_commit':sha,'image':a.image,'git_archive':True}));return
    if a.action=='redeploy':
        isolation()
        run(compose(a.image)+['up','-d','--no-build','--no-deps','backend','frontend','websocket','queue-short','queue-long','scheduler'],capture_output=True,text=True)
        run(['docker','exec',PROJECT+'-backend-1','bench','--site',SITE,'clear-cache'],capture_output=True,text=True)
    elif a.action=='up':
        command=compose(a.image)
        # Explicit labels and unique names checked before creation, no shared volumes.
        run(command+['up','-d','--no-build'],capture_output=True,text=True)
    elif a.action=='read-hooks':
        print(execute("print(json.dumps({'effective':frappe.get_hooks('before_request'),'app':frappe.get_hooks('before_request',app_name='centrochange_core')},default=str));frappe.db.rollback();frappe.destroy()"));return
    elif a.action=='seed':
        print(execute("assert frappe.conf.cc_synthetic_dev==1\nfrappe.conf.cc_uat_demo=1\nfrom centrochange_core.uat import demo\nprint(json.dumps(demo.seed(),default=str));frappe.destroy()"));return
    print(json.dumps(isolation()))

if __name__=='__main__':main()
