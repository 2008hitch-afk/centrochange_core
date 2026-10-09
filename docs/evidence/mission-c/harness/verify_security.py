import pathlib,json,urllib.request,urllib.error,http.cookiejar,urllib.parse,time
r=pathlib.Path(__file__).parent;d=json.loads((r/'qa-fixture.json').read_text());f=d['fixture'];base='http://127.0.0.1:8109';out=[]
def request(op,path,args=None,post=False):
 data=json.dumps(args).encode() if post else None
 if args and not post:path+='?'+urllib.parse.urlencode(args)
 req=urllib.request.Request(base+path,data=data,headers={'Content-Type':'application/json'} if post else {})
 try:
  res=op.open(req,timeout=30);return res.status,json.loads(res.read())
 except urllib.error.HTTPError as e:
  try:return e.code,json.loads(e.read())
  except:return e.code,{}
def test(name,condition,details=None):
 out.append({'name':name,'status':'PASS' if condition else 'FAIL',**({'observed':details} if details is not None else {})})
for role,user in f['users'].items():
 assert not (r/'safety-stop.json').exists()
 op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
 status,_=request(op,'/api/method/login',{'usr':user['name'],'pwd':user['password']},True);test(role+' login',status==200)
 for center in f['centers']:
  status,data=request(op,'/api/method/centrochange_core.operations.workspace.agenda',{'center':center,'start':'2026-09-28','end':'2026-10-04'})
  expected=(role in ['m','s','a','b','c']) and (role=='m' or center==f['centers'][0])
  test(role+' agenda '+str(f['centers'].index(center)),status==200 if expected else status==403,{'http':status})
  if status==200:
   rows=data['message']['appointments']
   if role in ['a','b']:test(role+' own appointments only',all(x['practitioner']==f['practitioners'][0 if role=='a' else 1] for x in rows))
   if role=='c':test('c no appointments',len(rows)==0)
  status,data=request(op,'/api/method/centrochange_core.finance.reporting.summary',{'center':center,'start':'2026-09-28','end':'2026-10-31'})
  expected=role in ['m','s','f','t'] and (role=='m' or center==f['centers'][0]);test(role+' finance '+str(f['centers'].index(center)),status==200 if expected else status==403,{'http':status})
  if status==200:test(role+' finance no private note field','private_notes' not in json.dumps(data))
 status,data=request(op,'/api/method/frappe.client.get_list',{'doctype':'Patient Appointment','fields':json.dumps(['name','practitioner','cc_center']),'limit_page_length':100})
 if status==200 and role in ['a','b']:
  test(role+' native list own only',all(x['practitioner']==f['practitioners'][0 if role=='a' else 1] for x in data.get('message',[])))
 if role=='c':test('c native list no appointments',status==403 or data.get('message')==[])
 status,_=request(op,'/api/method/frappe.client.get',{'doctype':'CC Private Note','name':f['private_note']});test(role+' private-note boundary',status==200 if role=='a' else status==403,{'http':status})
 status,_=request(op,'/api/method/frappe.desk.query_report.run',{'report_name':'General Ledger'});test(role+' generic accounting query guard',status==403 if role!='m' else status==403,{'http':status})
 if role in ['a','b','c']:
  for endpoint in ['finance.reporting.export_csv','finance.reporting.professional_view','finance.patient_reporting.patient_view']:
   args={'center':f['centers'][0],'start':'2026-09-28','end':'2026-10-31','practitioner':f['practitioners'][1 if role=='a' else 0],'key':'Patient:'+d['patients']['Alfa']}
   status,_=request(op,'/api/method/centrochange_core.'+endpoint,args);test(role+' '+endpoint+' denied',status==403,{'http':status})
(r/'security-results.json').write_text(json.dumps(out,indent=2));print(json.dumps({'checks':len(out),'pass':sum(x['status']=='PASS' for x in out),'fail':[x for x in out if x['status']=='FAIL']},indent=2))
