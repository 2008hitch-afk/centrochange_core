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
from security_acceptance import execute


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--env-file',required=True)
    args=parser.parse_args()
    values={line.split('=',1)[0]:line.split('=',1)[1].strip() for line in Path(args.env_file).read_text().splitlines() if '=' in line and not line.startswith('#')}
    root='http://127.0.0.1:'+values.get('HTTP_PORT','8082')
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
        assert status==expected,(path,status,expected,value.get('exc_type'),value.get('_server_messages'))
        return value
    try:
        fixture=execute('centrochange_core.security.dev_acceptance.create_http',{'scheduling':True,'operations':True,'finance':True})
        for label,row in fixture['users'].items():
            clients[label]=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            call(label,'/api/method/login',{'usr':row['name'],'pwd':row['password']})
        prepared=execute('centrochange_core.finance.incoming_acceptance.prepare_http',{'fixture':fixture})
        center=fixture['centers'][0];tag=fixture['tag'];prefix='/api/method/centrochange_core.finance.incoming.'
        intake={'center':center,'xml':prepared['xml'],'reason':tag}
        name=call('s',prefix+'intake',intake)['message']['name']
        assert call('f',prefix+'intake',intake)['message']['replay']
        checks.append('secretariat XML source intake and finance exact replay')
        for label in ('m','s','f','t'):
            data=call(label,'/api/resource/CC%20Incoming%20Invoice/'+name)['data']
            assert data['state']=='Needs Supplier Mapping' and not data.get('purchase_invoice')
            checks.append(label+' positive scoped incoming source REST without automatic payable')
        file_name=data['payload_file']
        metadata=call('f','/api/resource/File/'+file_name)['data']
        def download(label,url,expected):
            request=urllib.request.Request(root+url,headers={'Host':'centrochange.local'})
            try:
                response=clients[label].open(request,timeout=30);status=response.status;body=response.read()
            except urllib.error.HTTPError as error:
                status=error.code;body=error.read()
            assert status==expected,(url,status,expected)
            return body
        from hashlib import sha256
        content=download('f',metadata['file_url'],200)
        assert sha256(content).hexdigest()==data['payload_sha']
        for label in ('a','b'):
            call(label,'/api/resource/CC%20Incoming%20Invoice/'+name,expected=403)
            call(label,'/api/resource/File/'+file_name,expected=403)
            download(label,metadata['file_url'],403)
            call(label,prefix+'intake',intake,expected=403)
        checks.append('native private payload download hash and professional REST/file/download/intake denial')
        call('t',prefix+'bind_supplier',{'name':name,'supplier':prepared['supplier'],'reason':tag},expected=403)
        mapped=call('m',prefix+'bind_supplier',{'name':name,'supplier':prepared['supplier'],'reason':tag})['message']
        assert mapped['state']=='Needs Classification'
        args={'name':name,'items':[prepared['item']],'expense_account':prepared['expense_account'],'posting_date':'2026-10-05',
            'due_date':'2026-10-31','request_key':tag+'-payable','reason':tag}
        native=call('s',prefix+'draft',args)['message'];invoice=native['name']
        assert native['docstatus']==0 and native['total']==100
        assert call('s',prefix+'draft',args)['message']['replay']
        call('t',prefix+'submit',{'name':invoice,'reason':tag},expected=403)
        assert call('f',prefix+'submit',{'name':invoice,'reason':tag})['message']['outstanding']==100
        checks.append('management supplier binding secretariat reviewed native draft finance submit and accountant denial')
        bank_prefix='/api/method/centrochange_core.finance.banking.'
        movement={'external_id':tag+'-supplier-transfer','date':'2026-10-05','withdrawal':40,'supplier':prepared['supplier'],'reference':invoice,'description':'SYNTHETIC supplier transfer'}
        bank=call('f',bank_prefix+'import_movements',{'center':center,'movements':[movement],'reason':tag})['message']['movements'][0]['name']
        candidates=call('f',bank_prefix+'candidates?'+urllib.parse.urlencode({'name':bank}))['message']
        assert candidates['document_type']=='Purchase Invoice' and candidates['state']=='Candidate'
        assert call('f',bank_prefix+'reconcile',{'name':bank,'invoice':invoice,'reason':tag})['message']['movement']['unallocated']==0
        assert call('t',prefix+'position?'+urllib.parse.urlencode({'name':invoice}))['message']['outstanding']==60
        assert call('s',bank_prefix+'cancel',{'name':bank,'reason':tag})['message']['docstatus']==2
        assert call('f',prefix+'position?'+urllib.parse.urlencode({'name':invoice}))['message']['outstanding']==100
        checks.append('native supplier bank withdrawal reconciliation payable reduction and audited reversal')
        call('s',prefix+'cancel',{'name':invoice,'reason':tag})
        amended=call('s',prefix+'amend',{'name':invoice,'expense_account':prepared['expense_account'],'posting_date':'2026-10-05','due_date':'2026-10-31','request_key':tag+'-amend','reason':tag})['message']['name']
        call('f',prefix+'submit',{'name':amended,'reason':tag})
        receipt={'name':amended,'amount':30,'posting_date':'2026-10-05','request_key':tag+'-payment','reason':tag}
        assert call('f',prefix+'pay',receipt)['message']['invoice']['outstanding']==70
        assert call('f',prefix+'pay',receipt)['message']['invoice']['replay']
        assert call('f',prefix+'pay',{**receipt,'amount':70,'request_key':tag+'-full'})['message']['invoice']['outstanding']==0
        checks.append('native supplier cancel amend reissue partial full payment and replay through HTTP')
        for label in ('a','b'):
            call(label,'/api/resource/Purchase%20Invoice/'+urllib.parse.quote(amended,safe=''),expected=403)
            call(label,prefix+'position?'+urllib.parse.urlencode({'name':amended}),expected=403)
            call(label,'/api/method/frappe.desk.reportview.export_query',{'doctype':'Purchase Invoice','fields':'["name"]','file_format_type':'CSV'},expected=403)
        checks.append('professional native payable direct projection and export denied')
        call('f','/api/resource/CC%20Incoming%20Invoice/'+name,{'total':999},expected=403,verb='PUT')
        call('f','/api/resource/File/'+file_name,{'is_private':'0'},expected=403,verb='PUT')
        checks.append('generic incoming source rewrite and string-valued private-file declassification denied')
        call('f',prefix+'intake',{'center':fixture['centers'][1],'xml':prepared['xml'],'reason':tag},expected=403)
        execute('centrochange_core.security.lifecycle.set_membership',{'user':fixture['users']['f']['name'],'center':center,'active':0,'reason':tag})
        execute('centrochange_core.security.lifecycle.set_membership',{'user':fixture['users']['f']['name'],'center':fixture['centers'][1],'active':1,'reason':tag})
        call('f','/api/resource/CC%20Incoming%20Invoice/'+name,expected=403)
        download('f',metadata['file_url'],403)
        query=urllib.parse.urlencode({'doctype':'CC Incoming Invoice','fields':json.dumps(['name'])})
        assert not call('f','/api/method/frappe.client.get_list?'+query)['message']
        checks.append('cross-center intake and revoked-center native source list and private download denied')
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
