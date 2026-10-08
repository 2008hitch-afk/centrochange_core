#!/usr/bin/env python3
"""Repeatable synthetic browser acceptance. Run with Docker group access (sg docker)."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

IMAGE='centrochange-browser-qa:1.58.2'


def execute(method,kwargs=None):
    args=['docker','exec','centrochange-dev-backend-1','bench','--site','centrochange.local','execute',method]
    if kwargs is not None:
        args+=['--kwargs',repr(kwargs)]
    result=subprocess.run(args,capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError('Private DEV fixture command failed: '+method)
    return json.loads(result.stdout.strip())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--env-file',required=True)
    parser.add_argument('--output-dir',default='/tmp/centrochange-browser-evidence')
    parser.add_argument('--script',choices=('finance','threshold'),default='finance')
    args=parser.parse_args()
    repository=Path(__file__).resolve().parent.parent
    output=Path(args.output_dir).resolve()
    if output==repository or repository in output.parents:
        raise ValueError('Browser credentials and temporary QA output must stay outside Git')
    output.mkdir(mode=0o700,parents=True,exist_ok=True)
    os.chmod(output,0o700)
    values={line.split('=',1)[0]:line.split('=',1)[1].strip() for line in Path(args.env_file).read_text().splitlines() if '=' in line and not line.startswith('#')}
    port=int(values.get('HTTP_PORT','8082'))
    result=subprocess.run(['docker','build','-t',IMAGE,str(repository/'infra'/'browser')],capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError('Pinned browser QA image build failed')
    fixture=None
    credential=None
    reports=[]
    try:
        fixture=execute('centrochange_core.security.dev_acceptance.create_http',{'scheduling':True,'operations':True,'finance':True})
        fixture['incoming']=execute('centrochange_core.finance.incoming_acceptance.prepare_http',{'fixture':fixture})
        descriptor,credential=tempfile.mkstemp(prefix='cc-browser-fixture-',suffix='.json')
        with os.fdopen(descriptor,'w') as stream:
            json.dump(fixture,stream)
        os.chmod(credential,0o600)
        for script in (args.script,):
            command=['docker','run','--rm','--network','host','--user',str(os.getuid())+':'+str(os.getgid()),
                '-v',credential+':/qa-fixture.json:ro','-v',str(output)+':/qa-results',
                '-e','CC_BASE_URL=http://centrochange.local:'+str(port),IMAGE,'node','/qa/'+script+'.cjs']
            result=subprocess.run(command,capture_output=True,text=True)
            (output/(script+'.log')).write_text(result.stdout+result.stderr)
            if result.returncode:
                raise RuntimeError('Browser '+script+' acceptance failed; inspect '+str(output/(script+'.log')))
            report=json.loads(result.stdout.strip().splitlines()[-1])
            if report['status']!='PASS':
                raise RuntimeError('Browser '+script+' did not pass')
            reports.append(report)
        print(json.dumps({'status':'PASS','reports':reports,'browser_plugin':'unavailable','fallback':'pinned Playwright container','evidence':str(output)}))
    finally:
        if credential:
            Path(credential).unlink(missing_ok=True)
        if fixture:
            users=[row['name'] for row in fixture['users'].values()]
            for _ in range(30):
                if execute('centrochange_core.security.dev_acceptance.pending_contacts',{'users':users})['pending']==0:
                    break
                time.sleep(1)
            print(json.dumps(execute('centrochange_core.security.dev_acceptance.recover_http',{'tag':fixture['tag']})))


if __name__=='__main__':
    os.umask(0o077)
    main()
