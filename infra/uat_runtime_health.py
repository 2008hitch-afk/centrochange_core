#!/usr/bin/env python3
"""Preserved-site health only: no empty-DB assumptions, seed or reset."""
import json
import os
import socket
import subprocess
import time
import urllib.request
import uuid
from runtime_acceptance import execute


def main():
    os.umask(0o077)
    def get(path):
        with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8082'+path,headers={'Host':'centrochange.local'}),timeout=20) as r:
            assert r.status==200
            return r.read()
    assert json.loads(get('/api/method/ping'))['message']=='pong'
    for path in ('/login','/assets/centrochange_core/js/workspace.js','/assets/centrochange_core/css/workspace.css'):
        assert len(get(path))>100
    with socket.create_connection(('127.0.0.1',8082),timeout=10) as c:
        c.sendall(b'GET /socket.io/?EIO=4&transport=websocket HTTP/1.1\r\nHost: centrochange.local\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n')
        assert b'101 Switching Protocols' in c.recv(4096)
    assert execute("frappe.db.get_single_value('System Settings','enable_scheduler')")==1
    doctor=subprocess.check_output(['docker','exec','centrochange-dev-backend-1','bench','doctor'],text=True)
    assert 'Workers online: 2' in doctor and 'disabled' not in doctor.lower()
    for queue in ('short','long'):
        key='goal02-remediation-'+queue+'-'+uuid.uuid4().hex
        execute("{'id':frappe.enqueue('frappe.utils.now',queue="+repr(queue)+",job_id="+repr(key)+").id}")
        for _ in range(20):
            result=execute("{'status':__import__('frappe.utils.background_jobs',fromlist=['get_job']).get_job("+repr(key)+").get_status()}")
            if result['status']=='finished':break
            time.sleep(1)
        assert result['status']=='finished'
    rows=subprocess.check_output(['docker','ps','--filter','label=com.docker.compose.project=centrochange-dev','--format','{{.Names}}'],text=True).splitlines()
    assert len(rows)==9
    print(json.dumps({'status':'PASS','http_assets':True,'websocket_upgrade':True,'workers_online':2,'fresh_short_long_jobs_finished':True,'scheduler_enabled':True,'running_services':9,'business_data_mutations':False,'periodic_job_execution_claim':'not inferred from scheduler timestamp'}))


if __name__=='__main__':main()
