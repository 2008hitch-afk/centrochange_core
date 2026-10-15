#!/usr/bin/env python3
"""Exercise real Socket.IO authentication through the private tunnel Origin."""
import http.cookiejar, json, pathlib, urllib.error, urllib.parse, urllib.request
STATE=pathlib.Path('/home/empv26/.local/state/centrochange-single')
BASE='http://127.0.0.2:8082'
URL=BASE+'/socket.io/?EIO=4&transport=polling'
fixture=json.loads((STATE/'demo-owner.json').read_text())
user=(fixture.get('fixture') or fixture)['users']['m']

def request(opener,path,host,origin=None,data=None):
    headers={'Host':host}
    if origin is not None:headers['Origin']=origin
    try:
        with opener.open(urllib.request.Request(BASE+path,headers=headers,data=data),timeout=12) as response:
            return response.status,response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code,error.read().decode()

cookies=http.cookiejar.CookieJar()
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(cookies))
cases=[('centrochange.local:8082','http://centrochange.local:8082',200),
       ('127.0.0.1:8082','http://127.0.0.1:8082',200),
       ('127.0.0.1:8082',None,200),
       ('centrochange.local:8082','http://127.0.0.1:8082',403),
       ('centrochange.local:8082','http://evil.example',403),
       ('evil.example:8082','http://evil.example:8082',403)]
for host,origin,expected in cases:
    status,_=request(opener,'/socket.io/?EIO=4&transport=polling',host,origin)
    assert status==expected,(host,origin,status,expected)
# A real synthetic Manager login through the tunnel Host must authorize the namespace.
host='127.0.0.1:8082';origin='http://127.0.0.1:8082'
login=urllib.parse.urlencode({'usr':user['name'],'pwd':user['password']}).encode()
status,_=request(opener,'/api/method/login',host,data=login)
assert status==200,status
status,body=request(opener,'/socket.io/?EIO=4&transport=polling',host,origin)
assert status==200 and body.startswith('0{'),(status,body[:80])
sid=json.loads(body[1:])['sid']
path='/socket.io/?EIO=4&transport=polling&sid='+urllib.parse.quote(sid)
status,_=request(opener,path,host,origin,b'40/centrochange.local,')
assert status==200,status
for _ in range(4):
    status,body=request(opener,path,host,origin)
    if '40/centrochange.local,' in body: break
else: raise AssertionError('authenticated tunnel namespace was not accepted')
# An unauthenticated connection must be rejected by Frappe even with valid Host/Origin.
plain=urllib.request.build_opener(urllib.request.ProxyHandler({}))
status,body=request(plain,'/socket.io/?EIO=4&transport=polling',host,origin)
assert status==200 and body.startswith('0{')
sid=json.loads(body[1:])['sid'];path='/socket.io/?EIO=4&transport=polling&sid='+urllib.parse.quote(sid)
status,_=request(plain,path,host,origin,b'40/centrochange.local,')
assert status==200
status,body=request(plain,path,host,origin)
assert 'Missing cookie' in body or 'No authentication' in body,body[:120]
print(json.dumps({'status':'PASS','canonical_origin':200,'tunnel_origin':200,
                  'foreign_origin':403,'mismatched_origin':403,
                  'tunnel_manager_namespace':'AUTHENTICATED','guest_namespace':'DENIED'}))
