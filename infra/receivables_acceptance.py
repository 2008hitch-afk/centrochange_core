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
        fixture=execute('centrochange_core.security.dev_acceptance.create_http',{'scheduling':True,'operations':True,'finance':True,'public_route':False})
        for label,row in fixture['users'].items():
            clients[label]=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            call(label,'/api/method/login',{'usr':row['name'],'pwd':row['password']})
        prepared=execute('centrochange_core.finance.receivables_acceptance.prepare_http',{'fixture':fixture})
        prefix='/api/method/centrochange_core.finance.receivables.'
        payload={'sources':[prepared['source']],'posting_date':'2026-10-05','due_date':'2026-10-31','request_key':fixture['tag']+'-invoice','reason':fixture['tag']}
        doc=call('f',prefix+'draft',payload)['message']; name=doc['name']
        assert doc['docstatus']==0 and doc['total']==100
        assert call('f',prefix+'draft',payload)['message']['replay']
        checks.append('finance HTTP reviewed draft and replay one native invoice')
        for label in ('m','s','f','t'):
            value=call(label,prefix+'position?'+urllib.parse.urlencode({'name':name}))['message']
            assert value['name']==name
            call(label,'/api/resource/Sales%20Invoice/'+urllib.parse.quote(name,safe=''))
            checks.append(label+' positive native invoice REST and projection')
        call('t',prefix+'submit',{'name':name,'reason':fixture['tag']},expected=403)
        checks.append('accountant HTTP submission denied')
        value=call('f',prefix+'submit',{'name':name,'reason':fixture['tag']})['message']
        assert value['docstatus']==1 and value['outstanding']==100
        checks.append('finance HTTP actual native invoice posting')
        payment={'name':name,'amount':40,'posting_date':'2026-10-05','request_key':fixture['tag']+'-receipt','reason':fixture['tag']}
        value=call('f',prefix+'pay',payment)['message']
        assert value['invoice']['outstanding']==60
        assert call('f',prefix+'pay',payment)['message']['invoice']['replay']
        checks.append('finance HTTP partial receipt native open balance and replay')
        full={**payment,'amount':60,'request_key':fixture['tag']+'-full'}
        assert call('f',prefix+'pay',full)['message']['invoice']['outstanding']==0
        credit=call('f',prefix+'credit',{'name':name,'posting_date':'2026-10-05','request_key':fixture['tag']+'-credit','reason':fixture['tag']})['message']['name']
        assert call('f',prefix+'submit',{'name':credit,'reason':fixture['tag']})['message']['docstatus']==1
        checks.append('finance HTTP full receipt and native credit correction posted')
        second=call('s',prefix+'draft',{**payload,'sources':[prepared['source2']],'request_key':fixture['tag']+'-secretariat'})['message']['name']
        call('s',prefix+'submit',{'name':second,'reason':fixture['tag']})
        call('s',prefix+'cancel',{'name':second,'reason':fixture['tag']})
        amended=call('s',prefix+'amend',{'name':second,'posting_date':'2026-10-05','due_date':'2026-10-31','request_key':fixture['tag']+'-amend','reason':fixture['tag']})['message']['name']
        assert call('s',prefix+'submit',{'name':amended,'reason':fixture['tag']})['message']['docstatus']==1
        checks.append('secretariat HTTP native draft submit cancel amend reissue')
        call('f','/api/method/frappe.handler.run_doc_method',{'dt':'Sales Invoice','dn':name,'method':'set_healthcare_services','args':{'checked_values':[]}},expected=403)
        call('f','/api/method/erpnext.accounts.utils.get_balance_on?cmd=irrelevant',expected=403)
        call('f','/api/v2/method/erpnext.accounts.utils.get_balance_on',expected=403)
        checks.append('native document billing method and v1/v2 financial helper bypass denied')
        for label in ('a','b'):
            call(label,prefix+'position?'+urllib.parse.urlencode({'name':name}),expected=403)
            call(label,prefix+'pay',payment,expected=403)
            call(label,'/api/resource/Sales%20Invoice/'+urllib.parse.quote(name,safe=''),expected=403)
            query=urllib.parse.urlencode({'doctype':'GL Entry','fields':json.dumps(['name','debit','credit'])})
            call(label,'/api/method/frappe.client.get_list?'+query,expected=403)
            call(label,'/api/method/frappe.desk.reportview.export_query',{'doctype':'Sales Invoice','fields':'["name"]','file_format_type':'CSV'},expected=403)
            call(label,'/api/method/frappe.core.doctype.data_export.exporter.export_data',{'doctype':'Sales Invoice','with_data':1},expected=403)
            checks.append(label+' professional native invoice receipt GL query and export denied')
        query=urllib.parse.urlencode({'doctype':'GL Entry','fields':json.dumps(['name','voucher_no','debit','credit'])})
        assert call('t','/api/method/frappe.client.get_list?'+query)['message']
        checks.append('accountant positive scoped native GL query')
        call('f','/api/resource/Sales%20Invoice/'+urllib.parse.quote(name,safe=''),{'due_date':'2026-11-01'},expected=403,verb='PUT')
        checks.append('direct REST native invoice mutation denied')
        call('f','/api/method/frappe.desk.query_report.run?'+urllib.parse.urlencode({'report_name':'General Ledger'}),expected=403)
        call('f','/api/method/erpnext.regional.italy.utils.export_invoices',{},expected=403)
        checks.append('unscoped native SQL report and e-invoice export routes denied')
        execute('centrochange_core.security.lifecycle.set_membership',{'user':fixture['users']['f']['name'],'center':fixture['centers'][0],'active':0,'reason':fixture['tag']})
        execute('centrochange_core.security.lifecycle.set_membership',{'user':fixture['users']['f']['name'],'center':fixture['centers'][1],'active':1,'reason':fixture['tag']})
        call('f',prefix+'position?'+urllib.parse.urlencode({'name':name}),expected=403)
        query=urllib.parse.urlencode({'doctype':'Sales Invoice','fields':json.dumps(['name'])})
        assert not call('f','/api/method/frappe.client.get_list?'+query)['message']
        assert not call('f','/api/method/frappe.client.get_list?'+urllib.parse.urlencode({'doctype':'GL Entry','fields':json.dumps(['name'])}))['message']
        checks.append('revoked finance center invoice direct list and GL deny after membership change')
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
