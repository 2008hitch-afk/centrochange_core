import hashlib,subprocess
schema=frappe.db.sql('SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT,EXTRA FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,ORDINAL_POSITION',as_dict=True)
meta={}
for dt in ['DocType','Custom Field','Property Setter','DocPerm','Custom DocPerm','Role','Has Role','User Permission']:
 rows=frappe.get_all(dt,fields=['*'],order_by='name')
 rows=[{k:v for k,v in x.items() if k not in ['modified','modified_by','creation','owner']} for x in rows]
 meta[dt]={'count':len(rows),'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest()}
tables=frappe.db.get_tables();business={}
for table in sorted(tables):
 if table.startswith('tabCC ') or table in ['tabPatient','tabPatient Appointment','tabHealthcare Practitioner','tabSales Invoice','tabSales Invoice Item','tabPayment Entry','tabPayment Entry Reference','tabGL Entry','tabPayment Ledger Entry','tabPurchase Invoice','tabPurchase Invoice Item','tabCustomer','tabBank Transaction','tabBank Transaction Payments']:
  rows=frappe.db.sql('SELECT * FROM `'+table+'` ORDER BY name',as_dict=True)
  business[table]={'count':len(rows),'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest()}
files={}
from pathlib import Path
for folder in ['public/files','private/files']:
 for p in sorted(Path(frappe.get_site_path(folder)).rglob('*')):
  if p.is_file():files[str(p.relative_to(Path(frappe.get_site_path())))]=hashlib.sha256(p.read_bytes()).hexdigest()
pins={}
for app in ['frappe','erpnext','builder','healthcare']:
 try:pins[app]=subprocess.check_output(['git','-C','/home/frappe/frappe-bench/apps/'+app,'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()
 except subprocess.CalledProcessError:pins[app]={'version':__import__(app).__version__,'git_metadata':'official image omits .git'}
cc_fields=frappe.get_all('Custom Field',filters={'fieldname':['like','cc_%']},fields=['dt','fieldname','fieldtype','options','reqd','read_only','hidden','depends_on','mandatory_depends_on','permlevel'],order_by='dt, fieldname')
cc_perms={}
for dt in ['DocPerm','Custom DocPerm']:
 rows=frappe.get_all(dt,fields=['parent','role','permlevel','read','write','create','delete','submit','cancel','amend','select','print','email','report','import','export','share','if_owner'],order_by='parent, role, permlevel')
 cc_perms[dt]=[x for x in rows if x['parent'].startswith('CC ') or x['parent'] in ['Patient','Patient Appointment','Healthcare Practitioner','Sales Invoice','Payment Entry','Purchase Invoice','Customer']]
print('INVENTORY='+json.dumps({'cc_fields':cc_fields,'cc_perms':cc_perms,'schema':schema,'metadata':meta,'business':business,'files':files,'pins':pins,'installed_apps':frappe.get_installed_apps(),'core_patches':frappe.get_all('Patch Log',filters={'patch':['like','centrochange_core%']},pluck='patch')},default=str,sort_keys=True));frappe.db.rollback();frappe.destroy()
