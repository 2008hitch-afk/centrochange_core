import subprocess,json,http.cookiejar,urllib.request,urllib.parse,urllib.error,re,os
from datetime import datetime
from zoneinfo import ZoneInfo
manifest=json.loads(subprocess.check_output(['docker','exec',os.environ.get('CC156_CLONE_BACKEND', 'cc156-ci-backend'),'cat','/home/frappe/frappe-bench/sites/centrochange.local/private/uat/demo.json']))
user=manifest['fixture']['users']['m']
center=manifest['fixture']['centers'][0]
patient=manifest['patients']['Zeta']
appointment=manifest['appointments']['Zeta configurazione mancante']
jar=http.cookiejar.CookieJar(); opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
base='http://127.0.0.1:8099'
def req(path,data=None,headers=None):
    h={'Host':'centrochange.local','Accept':'application/json',**(headers or {})}
    try:
        with opener.open(urllib.request.Request(base+path,data=data,headers=h),timeout=20) as res: return res.status,res.read().decode()
    except urllib.error.HTTPError as e: return e.code,e.read().decode()
path='/api/method/centrochange_core.finance.operational_receipts.history?'+urllib.parse.urlencode({'patient':patient,'center':center})
assert req(path)[0] in (401,403,417)
reverse_path='/api/method/centrochange_core.finance.operational_receipts.reverse'
assert req(reverse_path,json.dumps({'patient':patient,'center':center,'receipt':'missing','reason':'Guest','request_key':'guest'}).encode(),{'Content-Type':'application/json'})[0] in (401,403,417)
status,_=req('/api/method/login',urllib.parse.urlencode({'usr':user['name'],'pwd':user['password']}).encode(),{'Content-Type':'application/x-www-form-urlencoded'})
assert status==200
status,html=req('/premium'); assert status==200
csrf=re.search(r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)',html).group(1)
status,body=req(path); assert status==200 and isinstance(json.loads(body)['message'],list)
methods=json.loads(req('/api/method/centrochange_core.operations.workspace.bootstrap?'+urllib.parse.urlencode({'center':center}))[1])['message']['payment_methods']
payload={'patient':patient,'center':center,'receipt_date':datetime.now(ZoneInfo('Europe/Rome')).date().isoformat(),'mode_of_payment':methods[0], 'reason':'Synthetic HTTP test','request_key':'cc156-http','allocations':[{'appointment':appointment,'amount':1}]}
body=json.dumps(payload).encode()
status,_=req('/api/method/centrochange_core.finance.operational_receipts.record',body,{'Content-Type':'application/json'})
assert status in (400,401,403,417),status
status,reply=req('/api/method/centrochange_core.finance.operational_receipts.record',body,{'Content-Type':'application/json','X-Frappe-CSRF-Token':csrf})
assert status==200,(status,reply)
receipt=json.loads(reply)['message']; assert not receipt['replay']
status,reply=req('/api/method/centrochange_core.finance.operational_receipts.record',body,{'Content-Type':'application/json','X-Frappe-CSRF-Token':csrf})
assert status==200 and json.loads(reply)['message']['replay']
correction=json.dumps({'patient':patient,'center':center,'receipt':receipt['name'],'reason':'Synthetic HTTP correction','request_key':'cc156-http-reverse'}).encode()
assert req(reverse_path,correction,{'Content-Type':'application/json'})[0] in (400,401,403,417)
status,reply=req(reverse_path,correction,{'Content-Type':'application/json','X-Frappe-CSRF-Token':csrf})
assert status==200 and not json.loads(reply)['message']['replay'],(status,reply)
status,reply=req(reverse_path,correction,{'Content-Type':'application/json','X-Frappe-CSRF-Token':csrf})
assert status==200 and json.loads(reply)['message']['replay']
print('PASS HTTP guest denied, CSRF denied, receipt and correction replay accepted')
