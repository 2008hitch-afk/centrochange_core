#!/usr/bin/env python3
"""Synthetic WP-01 financial scope acceptance through actual HTTP, no real credentials."""
import argparse
import http.cookiejar
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request
from security_acceptance import acceptance_base_url, execute


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--env-file',required=True)
    args=parser.parse_args()
    values={line.split('=',1)[0]:line.split('=',1)[1].strip() for line in Path(args.env_file).read_text().splitlines() if '=' in line and not line.startswith('#')}
    root=acceptance_base_url(values.get('HTTP_PORT','8082'))
    fixture=None
    checks=[]
    clients={}
    def call(label,path,data=None,expected=200,verb=None):
        payload=json.dumps(data).encode() if data is not None else None
        request=urllib.request.Request(root+path,data=payload,method=verb or ('POST' if data is not None else 'GET'),headers={'Host':'centrochange.local','Content-Type':'application/json'})
        try:
            response=clients[label].open(request,timeout=30)
            status=response.status
            value=json.load(response)
        except urllib.error.HTTPError as error:
            status=error.code
            value=json.load(error)
        assert status==expected,(path,status,expected,value.get('exc_type'))
        return value
    try:
        fixture=execute('centrochange_core.security.dev_acceptance.create_http',{'scheduling':True,'operations':True,'finance':True})
        for label,row in fixture['users'].items():
            clients[label]=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            call(label,'/api/method/login',{'usr':row['name'],'pwd':row['password']})
        finance=fixture['finance']
        for label in ('m','s','f','t'):
            for doctype,name in [('CC Economic Source Link',finance['source']),('Customer',finance['customer']),('Supplier',finance['supplier'])]:
                path='/api/resource/'+urllib.parse.quote(doctype,safe='')+'/'+urllib.parse.quote(name,safe='')
                result=call(label,path)
                assert 'PRIVATE' not in json.dumps(result)
                checks.append(label+' authorized REST '+doctype)
        for label in ('a','b','f','t'):
            if label in ('a','b'):
                call(label,'/api/resource/CC%20Economic%20Source%20Link/'+finance['source'],expected=403)
                checks.append(label+' professional financial source REST denied')
            else:
                call(label,'/api/resource/Patient/'+urllib.parse.quote(fixture['patients'][0],safe=''),expected=403)
                checks.append(label+' accounting Patient clinical master REST denied')
            call(label,'/api/resource/CC%20Private%20Note/'+fixture['private_note'],expected=200 if label=='a' else 403)
        checks.append('accounting identities acquire no private clinical REST access')
        query=urllib.parse.urlencode({'doctype':'CC Economic Source Link','fields':json.dumps(['name','customer','price','center'])})
        rows=call('f','/api/method/frappe.client.get_list?'+query)['message']
        assert [row['name'] for row in rows]==[finance['source']]
        checks.append('financial client query positive nonempty and scoped')
        call('f','/api/resource/CC%20Economic%20Source%20Link/'+finance['source'],{'price':999},expected=403,verb='PUT')
        checks.append('generic REST financial snapshot rewrite denied')
        prefix='/api/method/centrochange_core.finance.bridge.'
        replay=call('f',prefix+'map_patient',{'patient':fixture['patients'][0],'center':fixture['centers'][0],'reason':'Synthetic finance API retry'})['message']
        assert replay['replay'] and replay['customer']==finance['customer']
        checks.append('authorized mapping API replay idempotent')
        for label,center in [('t',fixture['centers'][0]),('a',fixture['centers'][0]),('f',fixture['centers'][1])]:
            call(label,prefix+'map_patient',{'patient':fixture['patients'][0],'center':center,'reason':'Synthetic unauthorized finance mutation'},expected=403)
            checks.append(label+' unauthorized/cross-center mapping API denied')
        call('f','/api/method/centrochange_core.operations.workspace.patient_history?'+urllib.parse.urlencode({'patient':fixture['patients'][0],'center':fixture['centers'][0]}),expected=403)
        checks.append('financial identity cannot invoke clinical operational history')
        print(json.dumps({'status':'PASS','checks':checks}))
    finally:
        if fixture:
            for _ in range(30):
                if execute('centrochange_core.security.dev_acceptance.pending_contacts',{'users':[row['name'] for row in fixture['users'].values()]})['pending']==0:
                    break
                time.sleep(1)
            print(json.dumps(execute('centrochange_core.security.dev_acceptance.recover_http',{'tag':fixture['tag']})))


if __name__=='__main__':
    main()
