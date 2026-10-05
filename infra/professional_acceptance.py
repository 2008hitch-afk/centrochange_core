#!/usr/bin/env python3
"""Synthetic WP-05 parametric economics and queue acceptance through actual HTTP, no real credentials."""
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
        ep='/api/method/centrochange_core.finance.professional_economics.'
        qp='/api/method/centrochange_core.finance.admin_queue.'
        query=urllib.parse.urlencode({'doctype':'CC Economic Source Link','fields':json.dumps(['name','appointment','service_item','practitioner']),'filters':json.dumps({'center':center,'performed':1})})
        sources=call('f','/api/method/frappe.client.get_list?'+query)['message']
        assert len(sources)==2
        rule_args={'center':center,'practitioner':sources[0]['practitioner'],'service_item':prepared['item'],'valid_from':'2099-01-01','basis':'Fixed Amount','value':100,'currency':'EUR','request_key':tag+'-rule','reason':tag}
        call('s',ep+'configure_rule',rule_args,expected=403)
        rule=call('m',ep+'configure_rule',rule_args)['message']['name']
        assert call('m',ep+'configure_rule',rule_args)['message']['replay']
        unresolved=call('f',ep+'capture',{'source':sources[0]['name'],'rule':rule,'reason':tag})['message']
        assert unresolved['state']=='REVIEW' and unresolved['amount'] is None
        read=call('t','/api/resource/CC%20Professional%20Expectation/'+unresolved['name'])['data']
        assert read['amount_known']==0 and read['problem']=='Professional Unpaid Threshold Missing'
        checks.append('management explicit compensation configuration and native REST unknown unpaid expectation without inferred zero')
        threshold_args={'center':center,'practitioner':sources[0]['practitioner'],'max_unpaid_sessions_compensated':0,'request_key':tag+'-threshold','reason':tag}
        call('s',ep+'configure_threshold',threshold_args,expected=403)
        threshold=call('m',ep+'configure_threshold',threshold_args)['message']['name']
        assert call('m',ep+'configure_threshold',threshold_args)['message']['replay']
        current=call('t',ep+'position?'+urllib.parse.urlencode({'center':center,'practitioner':sources[0]['practitioner']}))['message']['sessions']
        suspended=next(r for r in current if r['appointment']==sources[0]['appointment'])
        assert suspended['state']=='SUSPENDED' and not suspended['amount_known'] and suspended['unpaid_count']==2
        override_args={'expectation':suspended['name'],'reason':tag}
        for actor in ('a','b','s','f','t'):call(actor,ep+'override',override_args,expected=403)
        override=call('m',ep+'override',override_args)['message']
        assert override['state']=='OK' and override['amount']==100 and call('m',ep+'override',override_args)['message']['replay']
        preserved=call('t','/api/resource/CC%20Professional%20Expectation/'+suspended['name'])['data']
        assert preserved['state']=='SUSPENDED' and preserved['paid_snapshot']==0
        checks.append('DECISION-054 scoped threshold N0 suspension, immutable unpaid facts, Management audited override once and unauthorized override/configuration denied')
        query=urllib.parse.urlencode({'doctype':'Sales Invoice','fields':json.dumps(['name','outstanding_amount']),'filters':json.dumps({'cc_center':center,'docstatus':1})})
        invoices=call('f','/api/method/frappe.client.get_list?'+query)['message']
        for idx,row in enumerate(invoices):
            call('f','/api/method/centrochange_core.finance.receivables.pay',{'name':row['name'],'amount':row['outstanding_amount'],'posting_date':'2026-10-05','request_key':tag+'-patient-paid-'+str(idx),'reason':tag})
        expected=call('s',ep+'capture',{'source':sources[0]['name'],'rule':rule,'reason':tag})['message']
        assert expected['state']=='OK' and expected['amount']==100
        comparison=call('f',ep+'compare',{'purchase_invoice':amended,'expectations':[expected['name']],'reason':tag})['message']
        assert comparison['state']=='OK'
        assert call('f',ep+'compare',{'purchase_invoice':amended,'expectations':[expected['name']],'reason':tag})['message']['replay']
        call('s',ep+'capture',{'source':sources[1]['name'],'reason':tag})
        position=call('t',ep+'position?'+urllib.parse.urlencode({'center':center,'practitioner':sources[0]['practitioner']}))['message']
        assert position['expected_amount'] is None and position['unresolved_count']==1
        checks.append('native paid receivable permits explicit rule snapshot and native payable OK comparison; unknown aggregate stays explicit')
        missing=call('s',prefix+'intake',{'center':center,'xml':prepared['xml'].replace(tag+'-EXPENSE',tag+'-EXCEPTION'),'reason':tag})['message']['name']
        call('f',qp+'refresh',{'center':center,'reason':tag})
        assert not call('f',qp+'refresh',{'center':center,'reason':tag})['message']['changed']
        items=call('t',qp+'list_items?'+urllib.parse.urlencode({'center':center}))['message']
        work=next(i for i in items if i['reference_name']==missing)
        work_args={'name':work['name'],'priority':1,'assignee':fixture['users']['s']['name'],'due_at':'2099-02-01 12:00:00','defer_until':'2099-01-31 12:00:00','reason':tag}
        assert call('s',qp+'manage',work_args)['message']['state']=='Deferred'
        assert call('s',qp+'manage',work_args)['message']['replay']
        call('t',qp+'manage',work_args,expected=403)
        call('s',qp+'manage',{**work_args,'assignee':fixture['users']['a']['name']},expected=403)
        checks.append('center queue condition dedupe and audited assignment priority due deferral with read-only and unauthorized-assignee denial')
        ids=[('CC Unpaid Threshold',threshold),('CC Compensation Rule',rule),('CC Professional Expectation',expected['name']),('CC Professional Comparison',comparison['name']),('CC Admin Exception',work['name'])]
        for dt,ident in ids:
            path='/api/resource/'+urllib.parse.quote(dt,safe='')+'/'+urllib.parse.quote(ident,safe='')
            for label in ('m','s','f','t'):call(label,path)
            call('f',path,{'state':'OK'},expected=403,verb='PUT')
            for label in ('a','b'):
                call(label,path,expected=403)
                query=urllib.parse.urlencode({'doctype':dt,'fields':json.dumps(['name'])})
                call(label,'/api/method/frappe.client.get_list?'+query,expected=403)
                call(label,'/api/method/frappe.desk.reportview.export_query',{'doctype':dt,'fields':'["name"]','file_format_type':'CSV'},expected=403)
        for label in ('a','b'):
            call(label,ep+'position?'+urllib.parse.urlencode({'center':center,'practitioner':sources[0]['practitioner']}),expected=403)
            call(label,qp+'refresh',{'center':center,'reason':tag},expected=403)
        checks.append('all financial roles scoped REST positives; professional REST list export services and generic financial rewrites denied')
        call('f',prefix+'intake',{'center':fixture['centers'][1],'xml':prepared['xml'],'reason':tag},expected=403)
        execute('centrochange_core.security.lifecycle.set_membership',{'user':fixture['users']['f']['name'],'center':center,'active':0,'reason':tag})
        execute('centrochange_core.security.lifecycle.set_membership',{'user':fixture['users']['f']['name'],'center':fixture['centers'][1],'active':1,'reason':tag})
        call('f','/api/resource/CC%20Incoming%20Invoice/'+name,expected=403)
        download('f',metadata['file_url'],403)
        query=urllib.parse.urlencode({'doctype':'CC Incoming Invoice','fields':json.dumps(['name'])})
        assert not call('f','/api/method/frappe.client.get_list?'+query)['message']
        checks.append('cross-center intake and revoked-center native source list and private download denied')
        for dt,ident in ids:
            call('f','/api/resource/'+urllib.parse.quote(dt,safe='')+'/'+ident,expected=403)
        call('f',qp+'list_items?'+urllib.parse.urlencode({'center':center}),expected=403)
        checks.append('revoked-center professional snapshots comparisons rules and queue denied')
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
