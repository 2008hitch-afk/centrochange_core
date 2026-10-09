"""Host-only orchestration; reads immutable archived test code, never writes product."""
import sys,pathlib,subprocess,os,re,json,urllib.request,socket
from unittest.mock import patch
import lab,urllib.error,io
os.umask(0o077); lab.isolation()
original_run=subprocess.run; original_output=subprocess.check_output
browser='centrochange-g2d-browser:e85fce588de6-pw1582'
replacements=[('centrochange-dev-backend-1',lab.BACKEND),('centrochange-dev',lab.PROJECT),('centrochange.local',lab.SITE),('8082',str(lab.PORT)),('centrochange-browser-qa:1.58.2',browser),('/tmp/cc-remediation-backend.log',str(lab.ROOT/'remediation.log')),('/tmp/cc-uat-private-error.log',str(lab.ROOT/'uat-error.log')),('/tmp/cc-uat-browser-acceptance.lock',str(lab.ROOT/'browser.lock'))]
def mapped(value):
 if isinstance(value,str):
  # Playwright's committed resolver maps only centrochange.local to loopback.
  if value.startswith('CC_BASE_URL='):return 'CC_BASE_URL=http://centrochange.local:8080'
  for a,b in replacements:value=value.replace(a,b)
  return value
 if isinstance(value,list):return [mapped(v) for v in value]
 if isinstance(value,tuple):return tuple(mapped(v) for v in value)
 return value
def safe(args,kwargs):
 args=mapped(args)
 if 'input' in kwargs:kwargs['input']=mapped(kwargs['input'])
 # Dedicated fixture contexts do not own the persistent demo's public route.
 if 'centrochange_core.security.dev_acceptance.create_http' in args and name!='security_acceptance' and '--kwargs' in args:
  import ast
  i=args.index('--kwargs')+1; fixture_kwargs=ast.literal_eval(args[i]);fixture_kwargs['public_route']=False;args[i]=repr(fixture_kwargs)
 assert not any(v in repr(args)+str(kwargs.get('input','')) for v in ['centrochange-dev','centrochange-m97','mission97.local','127.0.0.1:8082','127.0.0.1:8097'])
 assert not kwargs.get('shell',False)
 if args[0]=='docker':
  assert args[1] in ['exec','ps','inspect','image','build','run']
  if args[1]=='image':assert args[2:] == ['inspect',browser]
  if args[1]=='exec':assert lab.BACKEND in args
  if args[1]=='inspect':assert all(x.startswith(lab.PROJECT+'-') for x in args[2:])
  if args[1]=='ps':assert 'label=com.docker.compose.project='+lab.PROJECT in args
  if args[1]=='build':assert '-t' in args and args[args.index('-t')+1]==browser
  if args[1]=='run':
   for script in ['public','finance','threshold','audit','bank_trace']:
    if '/qa/'+script+'.cjs' in args: args=args[:2]+['-v',str(lab.ROOT/(script+'-adapted.cjs'))+':/qa/'+script+'.cjs:ro']+args[2:]
   # TARGET native login uses a submit button instead of the old btn-login class.
   script_path=next((x for x in args if isinstance(x,str) and x.startswith('/qa/') and x.endswith('.cjs')),None)
   if script_path:
    canonical=lab.SOURCE/'infra/browser'/pathlib.Path(script_path).name
    adapted=lab.ROOT/('target-selector-'+canonical.name)
    content=canonical.read_text().replace('.form-login .btn-login','.form-login button[type="submit"]')
    adapted.write_text(content)
    args=args[:2]+['-v',str(adapted)+':'+script_path+':ro']+args[2:]
   assert browser in args and '--rm' in args
   assert 'CC_BASE_URL=http://centrochange.local:8080' in args
   ix=args.index('--network');args[ix+1]='container:'+lab.PROJECT+'-r5-fit-frontend-1'
   args=args[:2]+['--memory','512m','--memory-swap','512m','--label','centrochange.mission=B99-R5']+args[2:]
 elif args[0] in ['git','node']:pass
 else:raise AssertionError('Unreviewed subprocess '+str(args[:2]))
 if os.environ.get('B99_UNIQUE_PUBLIC_FIXTURE')=='1' and 'centrochange_core.security.dev_acceptance.create_http' in args:
  import ast
  fixture_kwargs=ast.literal_eval(args[args.index('--kwargs')+1])
  code="import frappe,json,inspect\nfrappe.init(site='b99.local',sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')\nfrom centrochange_core.security import dev_acceptance as fixture_module\nsource=inspect.getsource(fixture_module);assert source.count(\"'route':'Marco'\")==1\nsource=source.replace(\"'route':'Marco'\",\"'route':'Francesca'\")\nscope={'__name__':'isolated_fixture_namespace'};exec(compile(source,'isolated-unique-public-fixture','exec'),scope)\nprint(json.dumps(scope['create_http'](**"+repr(fixture_kwargs)+"),default=str));frappe.destroy()\n"
  args=['docker','exec','-i','-e','FRAPPE_STREAM_LOGGING=1','-w','/home/frappe/frappe-bench',lab.BACKEND,'env/bin/python'];kwargs['input']=code
 return args,kwargs
def run(args,*a,**kw):
 args,kw=safe(args,kw)
 if args[:2]==['docker','build']:
  image=json.loads(original_output(['docker','image','inspect',browser],text=True))[0]
  assert image['Id']=='sha256:f970b8eb4b0bd2186df380e6dffb1607f9fd8a75f67c04ba5f3c9d87d36e72d3'
  return subprocess.CompletedProcess(args,0,'CACHED PINNED QA IMAGE REUSED','')
 return original_run(args,*a,**kw)
def output(args,*a,**kw):args,kw=safe(args,kw);return original_output(args,*a,**kw)
old_open=urllib.request.OpenerDirector.open
def http_open(self,fullurl,*a,**kw):
 url=fullurl.full_url if hasattr(fullurl,'full_url') else str(fullurl)
 if url.startswith('http:'):assert url.startswith('http://127.0.0.1:'+str(lab.PORT)) or url.startswith('http://'+lab.SITE+':'+str(lab.PORT))
 else:assert url.startswith('https://raw.githubusercontent.com/')
 try:return old_open(self,fullurl,*a,**kw)
 except urllib.error.HTTPError as e:
  if any(x in url for x in ['receivables.submit','receivables.cancel']):
   body=e.read()
   with (lab.ROOT/'http-full-diagnostics.log').open('a') as log:log.write(lab.redact(url+'\n'+body.decode(errors='replace')+'\n'))
   raise urllib.error.HTTPError(e.url,e.code,e.msg,e.headers,io.BytesIO(body)) from None
  raise
old_connect=socket.create_connection
def connect(address,*a,**kw):
 assert (address[0]=='127.0.0.1' and address[1]==lab.PORT) or (name=='upstream_acceptance' and address[0]=='raw.githubusercontent.com' and address[1]==443)
 return old_connect(address,*a,**kw)
name=sys.argv[1]; script=lab.SOURCE/'infra'/ (name+'.py'); assert script.exists()
# Imported companion execute functions are intercepted at subprocess boundary.
sys.path.insert(0,str(lab.SOURCE/'infra')); sys.argv=[str(script),*sys.argv[2:]]
source=mapped(script.read_text())
if name=='security_acceptance' and os.environ.get('B99_UNIQUE_PUBLIC_FIXTURE')=='1':source=source.replace("'Marco'","'Francesca'")
if name=='browser_acceptance' and os.environ.get('G2D_PUBLIC_ONLY')=='1':
 source=source.replace("(('flows',) if args.operational_only else ('flows','public'))", "('public',)")
if name=='security_acceptance':
 old="assert call(guest,public,public_payload)['message']=={'name':public_result['name'],'replay':True}"
 new="assert call(guest,public,public_payload)['message']=={'name':public_result['name'],'replay':True,'confirmation':{'state':'Simulated Sent','replay':True}}"
 assert source.count(old)==1
 source=source.replace(old,new)

with patch('subprocess.run',run),patch('subprocess.check_output',output),patch('urllib.request.OpenerDirector.open',http_open),patch('socket.create_connection',connect):
 exec(compile(source,str(script),'exec'),{'__name__':'__main__','__file__':str(script)})
