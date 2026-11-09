"""Destructive synthetic-clone-only director and public booking acceptance."""
import logging,frappe,json
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
frappe.logger=lambda *a,**kw:logging.getLogger('clone')
frappe.init(site='centrochange.local',sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')
if frappe.conf.get('cc_synthetic_dev') != 1 or frappe.conf.get('cc_director_clone_test') != 1:
 raise RuntimeError('Acceptance test requires an explicitly flagged synthetic clone')
from centrochange_core.operations.directors import provision
from centrochange_core.scheduling.availability import set_schedule
from centrochange_core.scheduling.public_booking import available_slots,first_meeting
from centrochange_core.operations.workspace import agenda
extra = int(frappe.conf.get('cc_director_clone_ci') == 1)
expected={'Patient':18+extra,'Customer':17+extra,'Patient Appointment':35,'CC Operational Receipt':10,'CC Economic Source Link':35}
before={x:frappe.db.count(x) for x in expected};assert before==expected,before
center=frappe.db.get_value('CC Patient Assignment',{'active':1},'center')
date=(datetime.now(ZoneInfo('Europe/Rome')).date()+timedelta(days=2));day=date.strftime('%A');ids={}
for name in ('Marco','Francesca'):
 email=name.lower()+'.direzione@presentation.example.invalid'
 args={'center':center,'route':name,'email':email,'request_key':'director-test-'+name,'reason':'Collaudo sintetico isolato'}
 r=provision(**args);assert not r['replay'];second=provision(**args);assert second['replay'] and second['name']==r['name']
 assert frappe.db.get_value('User',email,'enabled')==1 and 'CC Manager' in frappe.get_roles(email)
 assert not frappe.db.exists('User Permission',{'user':email,'allow':'Healthcare Practitioner'})
 assert frappe.db.exists('CC Center Membership',{'user':email,'center':center,'active':1})
 assert frappe.db.get_value('CC Public Booking Route',name,'practitioner')==r['name']
 ids[name]=(r['name'],email)
 frappe.set_user('Guest')
 for mode in ('sede','online'):
  assert not available_slots(name,str(date),mode)['slots']
 frappe.set_user('Administrator')
 set_schedule(r['name'],center,[{'day':day,'from_time':'10:00:00','to_time':'12:00:00'}],'Solo clone sintetico')
 print('DIRECTOR_PASS',name)
assert {x:frappe.db.count(x) for x in expected}==before
from centrochange_core.operations.profiles import practitioners as professional_list
from centrochange_core.operations.workspace import bootstrap
names={row.name for row in professional_list(center)['rows']}
assert all(practitioner not in names for practitioner, _ in ids.values())
calendar_names={row.name for row in bootstrap(center)['practitioners']}
assert all(practitioner in calendar_names for practitioner, _ in ids.values())
print('ADMIN_CALENDAR_PROFILE_ISOLATION_PASS')
from centrochange_core.finance.report_dashboard import professional as finance_report
admin_ids={x.name for x in agenda(center,'2026-11-01','2026-11-30')['appointments']}
for name in ('Marco','Francesca'):
 frappe.set_user(ids[name][1])
 assert {x.name for x in agenda(center,'2026-11-01','2026-11-30')['appointments']}==admin_ids
 finance_report(center,'2026-11-01','2026-11-30')
 print('MANAGER_FINANCE_PASS',name)
frappe.set_user('Administrator')
for bad in ('Guest','giulia.moretti@presentation.example.invalid'):
 frappe.set_user(bad)
 try: provision(center,'Marco','forbidden@example.invalid','bad-'+bad,'Deny test')
 except frappe.PermissionError: pass
 else: raise AssertionError('unauthorized provisioning accepted')
 frappe.set_user('Administrator')
assert not frappe.db.exists('User','forbidden@example.invalid')
frappe.db.commit()
for name in ('Marco','Francesca'):
 for mode in ('sede','online'):
  frappe.set_user('Guest')
  slots=available_slots(name,str(date),mode)['slots'];assert slots,(name,mode)
  slot=slots[0];key='clone-'+name+'-'+mode
  args={'route':name,'mode':mode,'first_name':'Test','last_name':'Sintetico','email':key.lower()+'@example.invalid','sex':'Other','appointment_date':slot['date'],'appointment_time':slot['time'],'request_key':key}
  first=first_meeting(**args);second=first_meeting(**args);assert first['name']==second['name'] and second['replay']
  frappe.set_user('Administrator')
  ap=frappe.get_doc('Patient Appointment',first['name']);assert ap.practitioner==ids[name][0] and float(ap.duration)==20 and float(ap.cc_price_snapshot)==0
  admin=agenda(center,slot['date'],slot['date']);assert first['name'] in [x.name for x in admin['appointments']]
  frappe.set_user(ids[name][1]);personal=agenda(center,slot['date'],slot['date'],ids[name][0]);assert first['name'] in [x.name for x in personal['appointments']]
  frappe.set_user('Administrator');frappe.db.commit();print('BOOKING_PASS',name,mode)
assert frappe.db.count('Patient Appointment')==39
for d in ['Sales Invoice','Payment Entry','GL Entry','Email Queue','SMS Log','CC Fiscal Transaction']:assert frappe.db.count(d)==0,d
print('TESTS_PASS')
