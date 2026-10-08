"""Synthetic HTTP regression with distinct sessions and exact fixture teardown."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import http.cookiejar
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def execute(method, kwargs=None):
    command=['docker','exec','centrochange-dev-backend-1','bench','--site','centrochange.local','execute',method]
    if kwargs:
        command += ['--kwargs',repr(kwargs)]
    result=subprocess.run(command,text=True,capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return json.loads(result.stdout)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--env-file',required=True)
    parser.add_argument('--with-booking',action='store_true')
    args=parser.parse_args()
    config=dict(line.split('=',1) for line in Path(args.env_file).read_text().splitlines() if line and not line.startswith('#'))
    assert config['SITE_NAME']=='centrochange.local'
    base='http://127.0.0.1:'+config['HTTP_PORT']
    fixture=None
    checks=[]
    def session(user,password):
        opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        call(opener,'/api/method/login',{'usr':user,'pwd':password})
        return opener
    def call(opener,path,data=None,expected=200):
        request=urllib.request.Request(base+path,data=urllib.parse.urlencode(data).encode() if data is not None else None)
        try:
            with opener.open(request,timeout=30) as response:
                status=response.status
                raw=response.read()
                try:
                    value=json.loads(raw)
                except json.JSONDecodeError:
                    value={"binary_response":True}
        except urllib.error.HTTPError as error:
            status=error.code
            value=json.loads(error.read())
        assert status in (expected if isinstance(expected,tuple) else (expected,)),(path,status,expected,value.get("exc_type"),value.get("exception"))
        value['http_status']=status
        return value
    def denied(label,opener,path,data=None):
        call(opener,path,data,403)
        checks.append(label)
    try:
        fixture=execute('centrochange_core.security.dev_acceptance.create_http',{'scheduling':args.with_booking})
        admin=session(fixture['users']['m']['name'],fixture['users']['m']['password'])
        a=session(**{'user':fixture['users']['a']['name'],'password':fixture['users']['a']['password']})
        b=session(**{'user':fixture['users']['b']['name'],'password':fixture['users']['b']['password']})
        c=session(fixture['users']['c']['name'],fixture['users']['c']['password'])
        own,cross=fixture['patients']
        resource=lambda name:'/api/resource/Patient/'+urllib.parse.quote(name,safe='')
        assert call(a,resource(own))['data']['name']==own
        checks.append('own REST read')
        denied('cross REST read denied',a,resource(cross))
        denied('zero assignment REST read denied',b,resource(own))
        listing=call(a,'/api/resource/Patient?fields='+urllib.parse.quote('["name"]'))['data']
        assert listing==[{'name':own}],listing
        checks.append('REST list scoped nonempty')
        for endpoint in ('frappe.client.get_list','frappe.desk.reportview.get'):
            value=call(a,'/api/method/'+endpoint,{'doctype':'Patient','fields':'["name"]','page_length':20})
            assert cross not in json.dumps(value) and own in json.dumps(value)
            checks.append(endpoint+' scoped')
        denied('native report export denied',a,'/api/method/frappe.desk.reportview.export_query',{'doctype':'Patient','fields':'["name"]','file_format_type':'CSV'})
        denied('native data export denied',a,'/api/method/frappe.core.doctype.data_export.exporter.export_data',{'doctype':'Patient','with_data':1})
        denied('Marley detail cross denied',a,'/api/method/healthcare.healthcare.doctype.patient.patient.get_patient_detail?patient='+urllib.parse.quote(cross))
        denied('unwhitelisted DEV fixture denied',a,'/api/method/centrochange_core.security.dev_acceptance.create_http')
        denied('generic relationship mutation denied',a,'/api/resource/CC%20Center%20Membership',{'data':json.dumps({'user':fixture['users']['a']['name'],'center':fixture['centers'][1],'active':1})})
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(call,session(fixture['users']['m']['name'],fixture['users']['m']['password']),
                '/api/method/centrochange_core.security.lifecycle.set_membership',
                {'user':fixture['users']['c']['name'],'center':fixture['centers'][1],'active':1,'reason':fixture['tag']}) for _ in range(2)]
            values=[future.result()['message']['name'] for future in futures]
            assert values[0]==values[1]
        checks.append('concurrent membership retry single relationship')
        if args.with_booking:
            payload={'patient':own,'practitioner':fixture['practitioners'][0],'center':fixture['centers'][0],
                'appointment_type':fixture['catalog']['Appointment Type'][0], 'appointment_date':'2099-01-12',
                'appointment_time':'09:00:00','reason':fixture['tag']}
            method='/api/method/centrochange_core.scheduling.booking.book'
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures=[pool.submit(call,session(fixture['users']['m']['name'],fixture['users']['m']['password']),method,
                    {**payload,'request_key':'race-'+str(index)},(200,417)) for index in range(2)]
                values=[future.result() for future in futures]
                assert sorted(value['http_status'] for value in values)==[200,417],values
            checks.append('concurrent same-slot booking one committed winner')
            winner=next(value['message']['name'] for value in values if value['http_status']==200)
            assert call(a,'/api/resource/Patient%20Appointment/'+urllib.parse.quote(winner,safe=''))['data']['name']==winner
            denied('unassigned appointment cross REST denied',b,'/api/resource/Patient%20Appointment/'+urllib.parse.quote(winner,safe=''))
            for endpoint in ('update_status','check_in_appointment'):
                denied('native '+endpoint+' bypass denied',admin,
                    '/api/method/healthcare.healthcare.doctype.patient_appointment.patient_appointment.'+endpoint,
                    {'appointment_id':winner,'status':'Closed'})
            denied('native portal arbitrary booking denied',a,
                '/api/method/healthcare.healthcare.api.patient_portal.make_appointment',
                {'practitioner':fixture['practitioners'][0],'patient':own,'date':'2099-01-12','slot':'10:00:00'})
            guest=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            public='/api/method/centrochange_core.scheduling.public_booking.first_meeting'
            public_payload={'route':'Marco','first_name':fixture['tag']+' SYNTHETIC','last_name':'Guest',
                'email':fixture['tag'].lower()+'-guest@example.invalid','sex':'Female',
                'appointment_date':'2099-01-12','appointment_time':'10:00:00','request_key':fixture['tag']+'-public'}
            public_result=call(guest,public,public_payload)['message']
            public_doc=call(admin,'/api/resource/Patient%20Appointment/'+urllib.parse.quote(public_result['name'],safe=''))['data']
            fixture['patients'].append(public_doc['patient'])
            assert public_doc['practitioner']==fixture['practitioners'][0] and public_doc['appointment_type']==fixture['catalog']['Appointment Type'][0]
            assert call(guest,public,public_payload)['message']=={'name':public_result['name'],'replay':True}
            checks.append('Guest first meeting fixed route and idempotent replay')
            denied('Guest cannot read created appointment',guest,'/api/resource/Patient%20Appointment/'+urllib.parse.quote(public_result['name'],safe=''))
            call(guest,public,{**public_payload,'route':'Arbitrary','request_key':fixture['tag']+'-bad-route'},expected=417)
            checks.append('unapproved public route denied')
            call(admin,'/api/method/frappe.client.set_value',{'doctype':'CC Public Booking Route','name':'Marco','fieldname':'enabled','value':0})
            denied('disabled public route denied',guest,public,{**public_payload,'email':fixture['tag'].lower()+'-other@example.invalid','request_key':fixture['tag']+'-disabled'})
            call(admin,'/api/method/frappe.client.set_value',{'doctype':'CC Public Booking Route','name':'Marco','fieldname':'enabled','value':1})
            call(admin,'/api/method/frappe.client.set_value',{'doctype':'Appointment Type','name':fixture['catalog']['Appointment Type'][0],'fieldname':'cc_first_meeting','value':0})
            denied('public subsequent-session profile denied',guest,public,{**public_payload,'email':fixture['tag'].lower()+'-other@example.invalid','request_key':fixture['tag']+'-subsequent'})
        call(admin,'/api/method/centrochange_core.security.lifecycle.reassign'  ,{'patient':own,'center':fixture['centers'][0],
             'old_practitioner':fixture['practitioners'][0],'new_practitioner':fixture['practitioners'][1],'reason':fixture['tag']})
        denied('former session revoked after commit',a,resource(own))
        assert call(b,resource(own))['data']['name']==own
        checks.append('replacement session granted after commit')
        call(admin,'/api/method/centrochange_core.security.lifecycle.replace_principal',
             {'practitioner':fixture['practitioners'][1],'new_user':fixture['users']['c']['name'],'reason':fixture['tag']})
        denied('old principal replacement revoked',b,resource(own))
        assert call(c,resource(own))['data']['name']==own
        checks.append('replacement principal granted')
        call(admin,'/api/method/centrochange_core.security.lifecycle.set_practitioner_state',{
             'practitioner':fixture['practitioners'][1],'active':0,'reason':fixture['tag']})
        # Native invalidation expires the session; either Guest authorization or disabled guard denies.
        denied('disabled existing session denied',c,resource(own))
        print(json.dumps({'status':'PASS','checks':checks}))
    finally:
        if fixture:
            for attempt in range(30):
                if execute('centrochange_core.security.dev_acceptance.pending_contacts',{'users':[row['name'] for row in fixture['users'].values()]})['pending']==0:
                    break
                time.sleep(1)
            else:
                raise AssertionError('Native fixture contact jobs did not finish')
            for row in fixture['users'].values():
                row.pop('password',None)
            cleanup=execute('centrochange_core.security.dev_acceptance.destroy_http',{'fixture':fixture})
            assert cleanup['cleanup']=='PASS'
            print(json.dumps(cleanup))


if __name__=='__main__':
    main()
