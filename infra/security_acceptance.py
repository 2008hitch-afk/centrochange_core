"""Synthetic HTTP regression with distinct sessions and exact fixture teardown."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import http.cookiejar
import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def execute(method, kwargs=None):
    command=['docker','exec','centrochange-dev-backend-1','bench','--site','centrochange.local','execute',method]
    if kwargs:
        command += ['--kwargs',json.dumps(kwargs)]
    return json.loads(subprocess.check_output(command,text=True))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--env-file',required=True)
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
            value={}
        assert status==expected,(path,status,expected)
        return value
    def denied(label,opener,path,data=None):
        call(opener,path,data,403)
        checks.append(label)
    try:
        fixture=execute('centrochange_core.security.dev_acceptance.create_http')
        admin=session('Administrator',config['ADMIN_PASSWORD'])
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
            futures=[pool.submit(call,session('Administrator',config['ADMIN_PASSWORD']),
                '/api/method/centrochange_core.security.lifecycle.set_membership',
                {'user':fixture['users']['c']['name'],'center':fixture['centers'][1],'active':1,'reason':fixture['tag']}) for _ in range(2)]
            values=[future.result()['message']['name'] for future in futures]
            assert values[0]==values[1]
        checks.append('concurrent membership retry single relationship')
        call(admin,'/api/method/centrochange_core.security.lifecycle.reassign',{'patient':own,'center':fixture['centers'][0],
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
            for row in fixture['users'].values():
                row.pop('password',None)
            cleanup=execute('centrochange_core.security.dev_acceptance.destroy_http',{'fixture':fixture})
            assert cleanup['cleanup']=='PASS'
            print(json.dumps(cleanup))


if __name__=='__main__':
    main()
