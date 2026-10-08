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
        call('m','/api/resource/CC%20Finance%20Settings/CC%20Finance%20Settings',{'simulation_only':'0'},expected=403,verb='PUT')
        checks.append('management REST cannot disable DEV simulation gate with a string check value')
        prepared=execute('centrochange_core.finance.banking_acceptance.prepare_http',{'fixture':fixture})
        center=fixture['centers'][0]; patient=fixture['patients'][0]; tag=fixture['tag']
        prefix='/api/method/centrochange_core.finance.banking.'
        collection='/api/method/centrochange_core.finance.collections.'
        movement={'external_id':tag+'-statement-line','date':'2026-10-05','deposit':40,'description':'SYNTHETIC transfer'}
        data={'center':center,'movements':[movement],'reason':tag}
        name=call('f',prefix+'import_movements',data)['message']['movements'][0]['name']
        assert call('f',prefix+'import_movements',data)['message']['movements'][0]['replay']
        matching=call('f',prefix+'candidates?'+urllib.parse.urlencode({'name':name}))['message']
        assert matching['state']=='Ambiguous' and len(matching['invoices'])==2
        checks.append('finance HTTP native immutable movement dedupe and ambiguous candidates')
        other=call('s',prefix+'import_movements',{'center':center,'movements':[{**movement,'external_id':tag+'-unmatched','deposit':999}],'reason':tag})['message']['movements'][0]['name']
        assert call('s',prefix+'candidates?'+urllib.parse.urlencode({'name':other}))['message']['state']=='Unmatched'
        checks.append('secretariat HTTP import and unmatched movement projection')
        invoice=prepared['invoices'][0]
        selected=call('f',prefix+'reconcile',{'name':name,'invoice':invoice,'reason':tag})['message']
        assert selected['movement']['unallocated']==0
        assert call('s',prefix+'reconcile',{'name':name,'invoice':invoice,'reason':tag})['message']['movement']['replay']
        checks.append('finance HTTP native receipt bank allocation and cross-actor idempotent replay')
        for label in ('m','s','f','t'):
            call(label,'/api/resource/Bank%20Transaction/'+urllib.parse.quote(name,safe=''))
            call(label,'/api/resource/Bank%20Account/'+urllib.parse.quote(prepared['bank_account'],safe=''))
            assert call(label,collection+'position?'+urllib.parse.urlencode({'patient':patient,'center':center}))['message']['blocked']
            checks.append(label+' positive scoped bank REST and overdue projection')
        for label in ('a','b','t'):
            call(label,prefix+'reconcile',{'name':other,'invoice':invoice,'reason':tag},expected=403)
            call(label,collection+'override',{'patient':patient,'center':center,'reference_doctype':'Sales Invoice','reference_name':invoice,'due_date':'2099-02-28','request_key':tag+'-deny-'+label,'reason':tag},expected=403)
            if label!='t':
                call(label,'/api/resource/Bank%20Transaction/'+urllib.parse.quote(name,safe=''),expected=403)
                call(label,collection+'position?'+urllib.parse.urlencode({'patient':patient,'center':center}),expected=403)
                call(label,'/api/method/frappe.desk.reportview.export_query',{'doctype':'Bank Transaction','fields':'["name"]','file_format_type':'CSV'},expected=403)
            checks.append(label+' professional/readonly accountant bank action override and financial leakage negatives')
        notice=call('s',collection+'refresh',{'patient':patient,'center':center,'reason':tag})['message']
        assert notice['blocked'] and notice['notice']
        assert call('f',collection+'refresh',{'patient':patient,'center':center,'reason':tag})['message']['replay']
        saved=call('f','/api/resource/CC%20Payment%20Notice/'+notice['notice'])['data']
        assert saved['email_state']=='SIMULATED' and saved['communication']
        call('a','/api/resource/CC%20Payment%20Notice/'+notice['notice'],expected=403)
        call('a','/api/resource/Communication/'+saved['communication'],expected=403)
        comm_query=urllib.parse.urlencode({'doctype':'Communication','fields':json.dumps(['name','content']),'filters':json.dumps({'reference_doctype':'CC Payment Notice'})})
        assert not call('a','/api/method/frappe.client.get_list?'+comm_query)['message']
        checks.append('native local email trace internal block notice dedupe and professional denial')
        booking={'patient':patient,'practitioner':fixture['practitioners'][0],'center':center,'appointment_type':fixture['catalog']['Appointment Type'][0],
            'appointment_date':'2099-01-26','appointment_time':'09:00:00','request_key':tag+'-next','reason':tag}
        call('a','/api/method/centrochange_core.scheduling.booking.book',booking,expected=417)
        override_ids=[]
        for index,doc in enumerate(prepared['invoices']):
            value=call('s',collection+'override',{'patient':patient,'center':center,'reference_doctype':'Sales Invoice','reference_name':doc,'due_date':'2099-02-28','request_key':tag+'-override-'+str(index),'reason':tag})['message']
            override_ids.append(value['name'])
        assert call('a','/api/method/centrochange_core.scheduling.booking.book',booking)['message']['name']
        checks.append('professional direct booking blocked then authorized reasoned deadline overrides allow next session')
        assert call('s',prefix+'cancel',{'name':name,'reason':tag})['message']['docstatus']==2
        assert call('s',prefix+'cancel',{'name':name,'reason':tag})['message']['replay']
        assert call('f','/api/method/centrochange_core.finance.receivables.position?'+urllib.parse.urlencode({'name':invoice}))['message']['outstanding']==100
        checks.append('secretariat native bank/payment reversal restores original accounting balance and replays once')
        call('f','/api/resource/Bank%20Transaction/'+urllib.parse.quote(other,safe=''),{'description':'tampered'},expected=403,verb='PUT')
        call('f','/api/resource/CC%20Payment%20Override/'+override_ids[0],{'due_date':'2099-12-31'},expected=403,verb='PUT')
        checks.append('generic REST bank source and override rewrite denied')
        execute('centrochange_core.security.lifecycle.set_membership',{'user':fixture['users']['f']['name'],'center':center,'active':0,'reason':tag})
        execute('centrochange_core.security.lifecycle.set_membership',{'user':fixture['users']['f']['name'],'center':fixture['centers'][1],'active':1,'reason':tag})
        call('f',prefix+'candidates?'+urllib.parse.urlencode({'name':other}),expected=403)
        call('f','/api/resource/Bank%20Transaction/'+urllib.parse.quote(name,safe=''),expected=403)
        query=urllib.parse.urlencode({'doctype':'Bank Transaction','fields':json.dumps(['name'])})
        assert not call('f','/api/method/frappe.client.get_list?'+query)['message']
        checks.append('finance center revocation denies native bank direct API and list')
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
