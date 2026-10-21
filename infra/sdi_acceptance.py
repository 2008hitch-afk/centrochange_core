#!/usr/bin/env python3
"""Actual authenticated HTTP and real short-worker simulated SdI acceptance."""
import argparse,http.cookiejar,json,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
from security_acceptance import acceptance_base_url, execute


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--env-file',required=True);args=parser.parse_args()
    values={l.split('=',1)[0]:l.split('=',1)[1].strip() for l in Path(args.env_file).read_text().splitlines() if '=' in l and not l.startswith('#')}
    root=acceptance_base_url(values.get('HTTP_PORT','8082'));fixture=None;clients={};checks=[]
    def call(role,path,data=None,expected=200,verb=None,raw=False):
        req=urllib.request.Request(root+path,data=json.dumps(data).encode() if data is not None else None,method=verb or ('POST' if data is not None else 'GET'),headers={'Host':'centrochange.local','Content-Type':'application/json'})
        try:r=clients[role].open(req,timeout=30);status=r.status;body=r.read()
        except urllib.error.HTTPError as e:status=e.code;body=e.read()
        assert status==expected,(path,status,expected,body[:300] if status!=200 else '')
        return body if raw else json.loads(body)
    def poll(name):
        for _ in range(80):
            state=call('f','/api/method/centrochange_core.finance.fiscal.status?'+urllib.parse.urlencode({'name':name}))['message']
            if state['status']!='QUEUED':return state
            time.sleep(.25)
        raise AssertionError('Real short worker did not process queued simulated SdI attempt')
    try:
        fixture=execute('centrochange_core.security.dev_acceptance.create_http',{'scheduling':True,'operations':True,'finance':True})
        for role,row in fixture['users'].items():
            clients[role]=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));call(role,'/api/method/login',{'usr':row['name'],'pwd':row['password']})
        prepared=execute('centrochange_core.finance.incoming_acceptance.prepare_http',{'fixture':fixture});center=fixture['centers'][0];tag=fixture['tag'];sp='/api/method/centrochange_core.finance.sdi.';fp='/api/method/centrochange_core.finance.fiscal.'
        query=urllib.parse.urlencode({'doctype':'Sales Invoice','fields':json.dumps(['name']),'filters':json.dumps({'cc_center':center,'docstatus':1})})
        invoices=call('f','/api/method/frappe.client.get_list?'+query)['message'];assert len(invoices)==2
        first={'invoice':invoices[0]['name'],'request_key':tag+'-sdi-retry','reason':tag}
        retry=call('s',sp+'prepare',first)['message'];assert retry['status']=='PREPARED'
        assert call('f',sp+'prepare',first)['message']['replay']
        assert call('f',sp+'prepare',{**first,'request_key':tag+'-alias'})['message']['name']==retry['name']
        for role in ('m','s','f','t'):assert call(role,'/api/resource/CC%20Fiscal%20Transaction/'+retry['name'])['data']['route']=='SIMULATED'
        checks.append('scoped financial roles native fiscal REST positive and private native XML version preparation/replay/dedupe')
        for i in range(3):
            attempt={'name':retry['name'],'attempt_key':tag+'-attempt-'+str(i),'outcome':'Retryable Failure','reason':tag}
            call('f',sp+'queue',attempt);state=poll(retry['name'])
            assert state['status']==('FAILED_TERMINAL' if i==2 else 'FAILED_RETRYABLE')
            assert len(state['attempts'])==i+1 and all(a['processed_by']=='cc-automation-service@example.invalid' for a in state['attempts'])
            assert call('f',sp+'queue',attempt)['message']['replay']
        call('f',sp+'queue',{**attempt,'attempt_key':tag+'-over-limit','outcome':'Accepted'},expected=417)
        checks.append('actual short worker persists normalized attempts provenance and three-attempt retry exhaustion without provider traffic')
        second={'invoice':invoices[1]['name'],'request_key':tag+'-sdi-rejected','reason':tag}
        rejected=call('s',sp+'prepare',second)['message'];call('f',sp+'queue',{'name':rejected['name'],'attempt_key':tag+'-rejected-attempt','outcome':'Rejected','reason':tag});assert poll(rejected['name'])['status']=='REJECTED'
        file=call('f','/api/resource/File/'+rejected['payload_file'])['data'];original=call('f',file['file_url'],raw=True)
        call('s','/api/method/centrochange_core.finance.admin_queue.refresh',{'center':center,'reason':tag})
        call('s','/api/method/centrochange_core.finance.receivables.cancel',{'name':second['invoice'],'reason':tag})
        amended=call('s','/api/method/centrochange_core.finance.receivables.amend',{'name':second['invoice'],'posting_date':'2026-10-05','due_date':'2026-10-31','request_key':tag+'-correction','reason':tag})['message']['name']
        call('f','/api/method/centrochange_core.finance.receivables.submit',{'name':amended,'reason':tag})
        corrected=call('f',sp+'prepare',{'invoice':amended,'corrects':rejected['name'],'request_key':tag+'-corrected-xml','reason':tag})['message']
        call('s',sp+'queue',{'name':corrected['name'],'attempt_key':tag+'-corrected-attempt','outcome':'Accepted','reason':tag});assert poll(corrected['name'])['status']=='ACCEPTED_OR_DELIVERED'
        assert call('t',file['file_url'],raw=True)==original
        call('f','/api/method/centrochange_core.finance.admin_queue.refresh',{'center':center,'reason':tag})
        items=call('t','/api/method/centrochange_core.finance.admin_queue.list_items?'+urllib.parse.urlencode({'center':center,'include_closed':1}))['message']
        assert next(r for r in items if r['reference_name']==rejected['name'])['state']=='Closed'
        checks.append('rejected native correction retains original XML download after cancellation and accepted amendment auto-closes fiscal exception')
        inbound={'center':center,'external_message_id':'SYNTHETIC-'+tag,'xml':prepared['xml'],'reason':tag}
        result=call('s',sp+'intake',inbound)['message'];assert result['incoming_state']=='Needs Supplier Mapping'
        assert call('f',sp+'intake',inbound)['message']['replay']
        call('f',sp+'intake',{**inbound,'xml':prepared['xml']+' '},expected=417)
        checks.append('synthetic inbound message dedupe and immutable WP04 source handoff without automatic payable')
        call('t',sp+'prepare',first,expected=403);call('t',sp+'queue',attempt,expected=403)
        call('f','/api/resource/CC%20Fiscal%20Transaction/'+retry['name'],{'route':'REAL'},expected=403,verb='PUT')
        call('f','/api/resource/File/'+rejected['payload_file'],{'is_private':'0'},expected=403,verb='PUT')
        for role in ('a','b'):
            call(role,fp+'status?'+urllib.parse.urlencode({'name':retry['name']}),expected=403)
            call(role,'/api/resource/CC%20Fiscal%20Transaction/'+retry['name'],expected=403)
            call(role,'/api/resource/CC%20Fiscal%20Attempt/'+state['attempts'][0]['name'],expected=403)
            call(role,file['file_url'],expected=403,raw=True)
            call(role,sp+'intake',inbound,expected=403)
            call(role,'/api/method/frappe.desk.reportview.export_query',{'doctype':'CC Fiscal Transaction','fields':'["name"]','file_format_type':'CSV'},expected=403)
        checks.append('readonly Accountant mutation and professional direct result attempt payload download export/intake denied; generic route/file rewrite denied')
        call('f',sp+'intake',{**inbound,'center':fixture['centers'][1]},expected=403)
        execute('centrochange_core.security.lifecycle.set_membership',{'user':fixture['users']['f']['name'],'center':center,'active':0,'reason':tag})
        execute('centrochange_core.security.lifecycle.set_membership',{'user':fixture['users']['f']['name'],'center':fixture['centers'][1],'active':1,'reason':tag})
        call('f',fp+'status?'+urllib.parse.urlencode({'name':retry['name']}),expected=403);call('f',file['file_url'],expected=403,raw=True)
        query=urllib.parse.urlencode({'doctype':'CC Fiscal Transaction','fields':json.dumps(['name'])})
        assert not call('f','/api/method/frappe.client.get_list?'+query)['message']
        checks.append('cross-center intake and revoked-center fiscal result private file and native list denied')
        print(json.dumps({'status':'PASS','checks':checks}))
    finally:
        if fixture:
            for _ in range(30):
                if execute('centrochange_core.security.dev_acceptance.pending_contacts',{'users':[r['name'] for r in fixture['users'].values()]})['pending']==0:break
                time.sleep(1)
            print(json.dumps(execute('centrochange_core.security.dev_acceptance.recover_http',{'tag':fixture['tag']})))

if __name__=='__main__':main()
