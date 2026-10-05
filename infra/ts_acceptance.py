#!/usr/bin/env python3
"""Actual HTTP and short-worker independent synthetic TS acceptance."""
import argparse,http.cookiejar,json,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
from security_acceptance import execute


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--env-file',required=True);args=parser.parse_args()
    values={l.split('=',1)[0]:l.split('=',1)[1].strip() for l in Path(args.env_file).read_text().splitlines() if '=' in l and not l.startswith('#')}
    root='http://127.0.0.1:'+values.get('HTTP_PORT','8082');fixture=None;clients={};checks=[]
    def call(role,path,data=None,expected=200,verb=None,raw=False):
        req=urllib.request.Request(root+path,data=json.dumps(data).encode() if data is not None else None,method=verb or ('POST' if data is not None else 'GET'),headers={'Host':'centrochange.local','Content-Type':'application/json'})
        try:r=clients[role].open(req,timeout=30);status=r.status;body=r.read()
        except urllib.error.HTTPError as e:status=e.code;body=e.read()
        assert status==expected,(path,status,expected,body[:300] if status!=200 else '')
        return body if raw else json.loads(body)
    def poll(name):
        for _ in range(80):
            state=call('f','/api/method/centrochange_core.finance.fiscal.status?'+urllib.parse.urlencode({'name':name}))['message']
            if state['status']!='SUBMITTED':return state
            time.sleep(.25)
        raise AssertionError('Real short worker did not process queued simulated TS attempt')
    try:
        fixture=execute('centrochange_core.security.dev_acceptance.create_http',{'scheduling':True,'operations':True,'finance':True})
        for role,row in fixture['users'].items():
            clients[role]=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));call(role,'/api/method/login',{'usr':row['name'],'pwd':row['password']})
        execute('centrochange_core.finance.incoming_acceptance.prepare_http',{'fixture':fixture});center=fixture['centers'][0];tag=fixture['tag'];tp='/api/method/centrochange_core.finance.ts.';fp='/api/method/centrochange_core.finance.fiscal.'
        query=urllib.parse.urlencode({'doctype':'Sales Invoice','fields':json.dumps(['name','grand_total']),'filters':json.dumps({'cc_center':center,'docstatus':1})})
        invoice=call('f','/api/method/frappe.client.get_list?'+query)['message'][0]
        native=call('f','/api/resource/Sales%20Invoice/'+urllib.parse.quote(invoice['name'],safe=''))['data'];source=native['items'][0]['cc_economic_source']
        prep={'source':source,'invoice':invoice['name'],'request_key':tag+'-pending','reason':tag}
        pending=call('s',tp+'prepare',prep)['message'];assert pending['status']=='ELIGIBILITY_PENDING'
        assert call('f',tp+'prepare',prep)['message']['replay']
        attempt={'name':pending['name'],'attempt_key':tag+'-blocked','outcome':'Accepted','reason':tag}
        call('f',tp+'queue',attempt,expected=417)
        checks.append('unknown TS source document patient opposition and eligibility stays pending and cannot submit')
        review_args={'source':source,'invoice':invoice['name'],'opposition':'Opposed','eligibility':'SYNTHETIC_ELIGIBLE','expense_amount':invoice['grand_total'],'expense_code':'SYNTHETIC_EXPENSE','request_key':tag+'-opposed','reason':tag}
        for role in ('s','f','t'):call(role,tp+'review_inputs',review_args,expected=403)
        opposed=call('m',tp+'review_inputs',review_args)['message']['name'];assert call('m',tp+'review_inputs',review_args)['message']['replay']
        hold=call('f',tp+'prepare',{**prep,'request_key':tag+'-opposed-payload','input_review':opposed})['message'];assert hold['status']=='ELIGIBILITY_PENDING'
        call('f',tp+'queue',{**attempt,'name':hold['name']},expected=417)
        for role in ('m','s','f','t'):assert call(role,'/api/resource/CC%20TS%20Input%20Review/'+opposed)['data']['opposition']=='Opposed'
        call('m','/api/resource/CC%20TS%20Input%20Review/'+opposed,{'opposition':'No Opposition'},expected=403,verb='PUT')
        checks.append('management-only immutable opposition and synthetic eligibility review; opposed handling remains unverified and blocked')
        reviewed=call('m',tp+'review_inputs',{**review_args,'opposition':'No Opposition','request_key':tag+'-ready'})['message']['name']
        ready=call('s',tp+'prepare',{**prep,'request_key':tag+'-ready-payload','input_review':reviewed,'corrects':pending['name']})['message'];assert ready['status']=='READY'
        for idx,outcome in enumerate(('Retryable Failure','Accepted')):
            payload={'name':ready['name'],'attempt_key':tag+'-ts-attempt-'+str(idx),'outcome':outcome,'reason':tag}
            call('f',tp+'queue',payload);state=poll(ready['name']);assert state['status']==('RETRY_REQUIRED' if idx==0 else 'ACCEPTED')
            assert call('f',tp+'queue',payload)['message']['replay']
        assert len(state['attempts'])==2 and state['external_protocol'].startswith('SYNTHETIC-TS-')
        assert state['attempts'][1]['sequence']==2 and all(a['processed_by']=='cc-automation-service@example.invalid' for a in state['attempts'])
        receipt=json.loads(state['attempts'][-1]['receipt_json']);assert receipt['items'][0]['source']==source
        checks.append('actual short worker independent TS submitted transient retry accepted protocol ordered immutable attempt and item results')
        duplicate_review=call('m',tp+'review_inputs',{**review_args,'opposition':'No Opposition','expense_code':'SYNTHETIC_DUPLICATE','request_key':tag+'-duplicate-review'})['message']['name']
        call('f',tp+'prepare',{**prep,'request_key':tag+'-independent-duplicate','input_review':duplicate_review},expected=417)
        checks.append('fresh review cannot independently resubmit an accepted native expense')
        second=call('f','/api/method/frappe.client.get_list?'+query)['message'][1]
        second_native=call('f','/api/resource/Sales%20Invoice/'+urllib.parse.quote(second['name'],safe=''))['data']
        source=second_native['items'][0]['cc_economic_source'];invoice=second
        prep.update(source=source,invoice=invoice['name'])
        review_args.update(source=source,invoice=invoice['name'],expense_amount=invoice['grand_total'])
        reject_review=call('m',tp+'review_inputs',{**review_args,'opposition':'No Opposition','expense_code':'SYNTHETIC_REJECT','request_key':tag+'-reject-review'})['message']['name']
        rejected=call('s',tp+'prepare',{**prep,'request_key':tag+'-reject-payload','input_review':reject_review})['message']
        call('f',tp+'queue',{'name':rejected['name'],'attempt_key':tag+'-reject-attempt','outcome':'Rejected','reason':tag});assert poll(rejected['name'])['status']=='REJECTED'
        old_file=call('t','/api/resource/File/'+rejected['payload_file'])['data'];old_bytes=call('t',old_file['file_url'],raw=True)
        exhausted_review=call('m',tp+'review_inputs',{**review_args,'opposition':'No Opposition','expense_code':'SYNTHETIC_EXHAUSTION','request_key':tag+'-exhaust-review'})['message']['name']
        exhausted=call('s',tp+'prepare',{**prep,'request_key':tag+'-exhaust-payload','input_review':exhausted_review,'corrects':rejected['name']})['message']
        for i in range(3):call('f',tp+'queue',{'name':exhausted['name'],'attempt_key':tag+'-exhaust-'+str(i),'outcome':'Retryable Failure','reason':tag});state=poll(exhausted['name'])
        assert state['status']=='FAILED_TERMINAL' and state['attempt_count']==3 and state['error_class']=='SYNTHETIC_TS_RETRY_EXHAUSTED'
        call('f',tp+'queue',{'name':exhausted['name'],'attempt_key':tag+'-exhaust-4','outcome':'Accepted','reason':tag},expected=417)
        fix_review=call('m',tp+'review_inputs',{**review_args,'opposition':'No Opposition','expense_code':'SYNTHETIC_CORRECTED','request_key':tag+'-fix-review'})['message']['name']
        fixed=call('s',tp+'prepare',{**prep,'request_key':tag+'-fix-payload','input_review':fix_review,'corrects':exhausted['name']})['message']
        call('f',tp+'queue',{'name':fixed['name'],'attempt_key':tag+'-fix-attempt','outcome':'Accepted','reason':tag});assert poll(fixed['name'])['status']=='ACCEPTED'
        assert call('t',old_file['file_url'],raw=True)==old_bytes
        assert call('t',fp+'status?'+urllib.parse.urlencode({'name':rejected['name']}))['message']['status']=='REJECTED'
        checks.append('explicit corrected reviewed TS version retains original opposition payload rejection and protocol history')
        call('s','/api/method/centrochange_core.finance.admin_queue.refresh',{'center':center,'reason':tag})
        items=call('t','/api/method/centrochange_core.finance.admin_queue.list_items?'+urllib.parse.urlencode({'center':center}))['message']
        assert not any(r['reference_name'] in (exhausted['name'],rejected['name'],pending['name']) for r in items)
        checks.append('actual TS three-attempt failure becomes terminal and queue keeps unresolved conditions while accepted corrections close originals')
        call('t',tp+'prepare',prep,expected=403);call('t',tp+'queue',attempt,expected=403)
        for role in ('a','b'):
            call(role,tp+'review_inputs',review_args,expected=403);call(role,tp+'prepare',prep,expected=403)
            call(role,fp+'status?'+urllib.parse.urlencode({'name':ready['name']}),expected=403)
            call(role,'/api/resource/CC%20TS%20Input%20Review/'+reviewed,expected=403)
            call(role,old_file['file_url'],raw=True,expected=403)
            call(role,'/api/method/frappe.desk.reportview.export_query',{'doctype':'CC TS Input Review','fields':'["name"]','file_format_type':'CSV'},expected=403)
        checks.append('readonly Accountant mutation and professional source review result private payload export services denied')
        execute('centrochange_core.security.lifecycle.set_membership',{'user':fixture['users']['f']['name'],'center':center,'active':0,'reason':tag})
        execute('centrochange_core.security.lifecycle.set_membership',{'user':fixture['users']['f']['name'],'center':fixture['centers'][1],'active':1,'reason':tag})
        call('f',fp+'status?'+urllib.parse.urlencode({'name':ready['name']}),expected=403);call('f','/api/resource/CC%20TS%20Input%20Review/'+reviewed,expected=403);call('f',old_file['file_url'],raw=True,expected=403)
        query=urllib.parse.urlencode({'doctype':'CC TS Input Review','fields':json.dumps(['name'])});assert not call('f','/api/method/frappe.client.get_list?'+query)['message']
        checks.append('revoked-center TS input native list result and private download denied')
        print(json.dumps({'status':'PASS','checks':checks}))
    finally:
        if fixture:
            for _ in range(30):
                if execute('centrochange_core.security.dev_acceptance.pending_contacts',{'users':[r['name'] for r in fixture['users'].values()]})['pending']==0:break
                time.sleep(1)
            print(json.dumps(execute('centrochange_core.security.dev_acceptance.recover_http',{'tag':fixture['tag']})))

if __name__=='__main__':main()
