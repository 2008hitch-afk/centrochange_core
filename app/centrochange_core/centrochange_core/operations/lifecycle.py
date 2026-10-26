"""Canonical session closure, cancellation facts and audited operational settlement."""
from datetime import datetime,timedelta,timezone
import json
from zoneinfo import ZoneInfo
import frappe
from frappe.utils import getdate,get_time,cint
from centrochange_core.security.audit import append,atomic,internal_write
from centrochange_core.security.guards import require_operations, require_center, require_operational_center, patient_names, is_manager, roles, practitioner_for, enabled
from centrochange_core.security.lifecycle import lock
from centrochange_core.scheduling.booking import require_booking
from centrochange_core.operations import packages
from centrochange_core.operations.notes import require_context

ROME=ZoneInfo('Europe/Rome')


def now_utc():
	if frappe.in_test and frappe.conf.get('cc_synthetic_dev')==1 and frappe.flags.get('cc_test_clock'):
		return frappe.flags.cc_test_clock
	return datetime.now(timezone.utc)


def _now_rome():
	return now_utc().astimezone(ROME)


def require_actor():
	if not enabled() or not (is_manager() or {'CC Professional','CC Secretariat'} & set(roles())):
		frappe.throw('Non hai accesso alla schermata operativa.', frappe.PermissionError)


def start_utc(doc):
	local=datetime.combine(getdate(doc.appointment_date),get_time(doc.appointment_time))
	first=local.replace(tzinfo=ROME,fold=0)
	second=local.replace(tzinfo=ROME,fold=1)
	if first.utcoffset()!=second.utcoffset() or first.astimezone(timezone.utc).astimezone(ROME).replace(tzinfo=None)!=local:
		frappe.throw('L’ora della seduta non esiste o è ambigua nel fuso Europe/Rome: correggila esplicitamente.')
	return first.astimezone(timezone.utc)


def cancellation_fact(start,at):
	if start.tzinfo is None or at.tzinfo is None:
		frappe.throw('Il calcolo della cancellazione richiede date con fuso orario.')
	delta=start.astimezone(timezone.utc)-at.astimezone(timezone.utc)
	microseconds=(delta.days*86400+delta.seconds)*1000000+delta.microseconds
	return {'notice_seconds':microseconds/1000000,'late':microseconds<48*3600*1000000}


def _doc(name):
	doc=frappe.get_doc('Patient Appointment',name,for_update=True)
	doc.check_permission('read')
	from centrochange_core.operations.notes import require_context
	require_context(doc.patient,doc.cc_center)
	return doc


def require_mutable(doc):
	if doc.cc_closure_state in ('Closed','Auto Locked'):
		frappe.throw('La seduta è bloccata: serve una riapertura o correzione autorizzata.',frappe.PermissionError)
	cutoff=datetime.combine(getdate(doc.appointment_date)+timedelta(days=1),get_time('07:00:00')).replace(tzinfo=ROME)
	if doc.cc_closure_state!='Reopened' and now_utc()>=cutoff.astimezone(timezone.utc):
		frappe.throw('La seduta ha superato il termine di blocco automatico.',frappe.PermissionError)


def _patch(doc,values):
	allowed={'status','cc_closure_state','cc_economic_state','cc_performed','cc_paid','cc_cancelled_at',
		'cc_cancel_notice_seconds','cc_late_cancellation','cc_revision','cc_settlement_revision','cc_locked_at'}
	if not frappe.flags.get('cc_operation_write') or set(values)-allowed:
		frappe.throw('La modifica operativa richiesta non è valida.',frappe.PermissionError)
	frappe.db.set_value('Patient Appointment',doc.name,values)
	for key,value in values.items():
		doc.set(key,value)


@frappe.whitelist(methods=['POST'])
@atomic
def cancel(appointment,reason):
	lock()
	doc=_doc(appointment)
	if doc.status=='Cancelled':
		return {'name':doc.name,'late':bool(doc.cc_late_cancellation),'replay':True}
	require_mutable(doc)
	if doc.cc_performed:
		frappe.throw('Una seduta svolta richiede una correzione, non una normale cancellazione.')
	at=now_utc()
	fact=cancellation_fact(start_utc(doc),at)
	revision=cint(doc.cc_revision)+1
	packages.disposition(doc,fact['late'],reason,revision)
	economic='Package Covered' if fact['late'] and doc.cc_package else ('Due' if fact['late'] else 'Non Due')
	with internal_write('cc_operation_write'):
		_patch(doc,{'status':'Cancelled','cc_closure_state':'Closed','cc_economic_state':economic,
			'cc_cancelled_at':at.replace(tzinfo=None),'cc_cancel_notice_seconds':fact['notice_seconds'],
			'cc_late_cancellation':int(fact['late']),'cc_revision':revision})
	append('SESSION_CANCELLED',doc.doctype,doc.name,None,{**fact,'economic':economic},reason)
	return {'name':doc.name,'late':fact['late'],'replay':False}


def _settlement(doc,paid,mode,reason):
	paid=cint(paid)
	if paid not in (0,1):
		frappe.throw('Lo stato di pagamento operativo deve essere sì o no.')
	if paid and (not mode or not frappe.db.get_value('Mode of Payment',mode,'enabled',for_update=True)):
		frappe.throw('Seleziona un metodo di pagamento informativo attivo.')
	rows=current_settlements(doc.name)
	if rows and rows[0].paid==paid and (rows[0].mode_of_payment or None)==(mode or None):
		return rows[0].name
	if not reason or not reason.strip():
		frappe.throw('Indica il motivo della registrazione del pagamento.')
	sequence=cint(doc.cc_settlement_revision)+1
	with internal_write('cc_operation_write'):
		event=frappe.get_doc({'doctype':'CC Settlement','appointment':doc.name,'paid':paid,'sequence':sequence,
			'mode_of_payment':mode,'actor':frappe.session.user,'event_time':frappe.utils.now_datetime(),'reason':reason}).insert(ignore_permissions=True)
		_patch(doc,{'cc_paid':paid,'cc_settlement_revision':sequence})
	append('OPERATIONAL_SETTLEMENT',doc.doctype,doc.name,None,{'paid':paid,'method':mode,'settlement':event.name},reason)
	return event.name


def current_settlements(appointment):
	from centrochange_core.security.guards import current_rows
	rows=current_rows('CC Settlement',{'appointment':appointment},fields=['name','paid','mode_of_payment','sequence'])
	return sorted(rows,key=lambda row:row.sequence,reverse=True)


@frappe.whitelist(methods=['POST'])
@atomic
def close(appointment,paid,reason,mode_of_payment=None):
	lock()
	doc=_doc(appointment)
	if doc.cc_closure_state=='Closed' and doc.cc_performed:
		rows=current_settlements(doc.name)
		if cint(paid)!=doc.cc_paid or rows and (rows[0].mode_of_payment or None)!=(mode_of_payment or None):
			frappe.throw('Il pagamento di una seduta chiusa richiede un servizio di correzione.')
		return {'name':doc.name,'replay':True}
	require_mutable(doc)
	if doc.status=='Cancelled':
		frappe.throw('Una seduta cancellata richiede una correzione economica autorizzata.')
	from centrochange_core.finance.collections import require_booking as require_payment_clearance
	require_payment_clearance(doc)
	if start_utc(doc)+timedelta(minutes=doc.duration)>now_utc():
		frappe.throw('Una seduta futura o in corso non può essere segnata come svolta.')
	revision=cint(doc.cc_revision)+1
	due=doc.cc_economic_state!='Waived'
	packages.disposition(doc,due,reason,revision)
	with internal_write('cc_operation_write'):
		_patch(doc,{'status':'Closed','cc_closure_state':'Closed','cc_performed':1,
			'cc_economic_state':('Package Covered' if doc.cc_package else 'Due') if due else 'Waived','cc_revision':revision})
	_settlement(doc,paid,mode_of_payment,reason)
	append('SESSION_CLOSED',doc.doctype,doc.name,None,{'performed':True,'economic':doc.cc_economic_state},reason)
	return {'name':doc.name,'replay':False}


@frappe.whitelist(methods=['POST'])
@atomic
def waive(appointment,reason):
	lock()
	doc=_doc(appointment)
	require_operations(doc.cc_center)
	if doc.cc_economic_state=='Waived':
		return {'name':doc.name,'replay':True}
	if doc.cc_economic_state not in ('Due','Package Covered'):
		frappe.throw('La seduta deve avere uno stato economico dovuto.')
	revision=cint(doc.cc_revision)+1
	packages.disposition(doc,False,reason,revision)
	with internal_write('cc_operation_write'):
		_patch(doc,{'cc_economic_state':'Waived','cc_revision':revision})
	append('ECONOMIC_WAIVER',doc.doctype,doc.name,{'late':bool(doc.cc_late_cancellation)},
		{'economic':'Waived','late':bool(doc.cc_late_cancellation)},reason)
	return {'name':doc.name,'replay':False}


@frappe.whitelist(methods=['POST'])
@atomic
def reopen(appointment,reason):
	lock()
	doc=_doc(appointment)
	require_operations(doc.cc_center)
	if doc.cc_closure_state=='Reopened':
		return {'name':doc.name,'replay':True}
	if doc.cc_closure_state not in ('Closed','Auto Locked'):
		frappe.throw('È richiesta una seduta definitiva.')
	before={'closure':doc.cc_closure_state}
	with internal_write('cc_operation_write'):
		_patch(doc,{'cc_closure_state':'Reopened','cc_revision':cint(doc.cc_revision)+1})
	append('SESSION_REOPENED',doc.doctype,doc.name,before,{'closure':'Reopened'},reason)
	return {'name':doc.name,'replay':False}


@frappe.whitelist(methods=['POST'])
@atomic
def record_settlement(appointment,paid,reason,mode_of_payment=None):
	lock()
	doc=_doc(appointment)
	if doc.cc_closure_state in ('Closed','Auto Locked'):
		require_operations(doc.cc_center)
		if doc.cc_closure_state=='Auto Locked':
			frappe.throw('Una seduta bloccata automaticamente deve essere riaperta prima della correzione.',frappe.PermissionError)
	else:
		require_mutable(doc)
	return {'settlement':_settlement(doc,paid,mode_of_payment,reason),'paid':cint(paid)}


@frappe.whitelist(methods=['GET'])
def get_day_closure_sessions(center, date=None):
	require_actor()
	require_center(center)
	require_operational_center(center)

	user_roles = roles()
	is_mgr = is_manager()
	my_prac = None
	allowed_patients = None
	if 'CC Professional' in user_roles and not is_mgr:
		my_prac = practitioner_for()
		if not my_prac:
			frappe.throw('Nessun profilo professionista associato al tuo account.', frappe.PermissionError)
		allowed_patients = set(patient_names() or [])
		if not allowed_patients:
			return {
				'date': str(getdate(date) if date else _now_rome().date()),
				'is_today': (getdate(date) if date else _now_rome().date()) == _now_rome().date(),
				'is_past': (getdate(date) if date else _now_rome().date()) < _now_rome().date(),
				'sessions': [],
				'arrear_dates': [],
				'practitioner': my_prac
			}

	today_rome = _now_rome().date()
	target_date = getdate(date) if date else today_rome

	arrear_filters = {
		'cc_center': center,
		'appointment_date': ['<', today_rome],
		'cc_closure_state': ['in', ['Pending', 'Auto Locked']],
		'status': ['!=', 'Cancelled']
	}
	if my_prac:
		arrear_filters['practitioner'] = my_prac
	if allowed_patients is not None:
		arrear_filters['patient'] = ['in', list(allowed_patients)]

	arrear_rows = frappe.get_all('Patient Appointment', filters=arrear_filters, fields=['appointment_date'], order_by='appointment_date desc')
	arrear_dates_set = {str(r.appointment_date) for r in arrear_rows if r.appointment_date}
	arrear_dates = sorted(list(arrear_dates_set), reverse=True)

	app_filters = {
		'cc_center': center,
		'appointment_date': target_date
	}
	if my_prac:
		app_filters['practitioner'] = my_prac
	if allowed_patients is not None:
		app_filters['patient'] = ['in', list(allowed_patients)]

	fields = [
		'name', 'appointment_date', 'appointment_time', 'duration',
		'patient', 'patient_name', 'practitioner', 'practitioner_name',
		'cc_service_label', 'status', 'cc_closure_state', 'cc_economic_state',
		'cc_performed', 'cc_paid', 'cc_late_cancellation',
		'cc_price_snapshot', 'cc_currency_snapshot', 'cc_revision'
	]
	raw_sessions = frappe.get_all('Patient Appointment', filters=app_filters, fields=fields, order_by='appointment_time,name')

	patient_ids = list({s.patient for s in raw_sessions if s.patient})
	if allowed_patients is not None:
		patient_ids = [pid for pid in patient_ids if pid in allowed_patients]

	names = {}
	if patient_ids:
		p_query = frappe.get_list if is_mgr else frappe.get_all
		p_rows = p_query('Patient', filters={'name': ['in', patient_ids]}, fields=['name', 'first_name', 'last_name'], page_length=len(patient_ids))
		for p in p_rows:
			p_name = getattr(p, 'name', None) or (p.get('name') if isinstance(p, dict) else None)
			names[p_name] = p

	now = now_utc()
	sessions = []
	for s in raw_sessions:
		s.appointment_time = str(get_time(s.appointment_time))
		ident = names.get(s.patient)
		if ident:
			s.patient_first_name = getattr(ident, 'first_name', None) or (ident.get('first_name') if isinstance(ident, dict) else None)
			s.patient_last_name = getattr(ident, 'last_name', None) or (ident.get('last_name') if isinstance(ident, dict) else None)
		else:
			s.patient_first_name = None
			s.patient_last_name = None

		settlements = current_settlements(s.name)
		s.mode_of_payment = settlements[0].mode_of_payment if settlements else None
		app_end_utc = start_utc(s) + timedelta(minutes=int(s.duration or 60))
		s.has_ended = 1 if app_end_utc <= now else 0
		sessions.append(s)

	return {
		'date': str(target_date),
		'is_today': target_date == today_rome,
		'is_past': target_date < today_rome,
		'sessions': sessions,
		'arrear_dates': arrear_dates,
		'practitioner': my_prac
	}


@frappe.whitelist(methods=['POST'])
@atomic
def close_day(center, date, sessions, reason=None, allow_partial=0):
	require_actor()
	require_center(center)
	require_operational_center(center)
	lock()

	allow_partial = cint(allow_partial)

	if isinstance(sessions, str):
		try:
			sessions = json.loads(sessions)
		except Exception:
			frappe.throw('Payload sessions non valido: formato JSON errato.')
	if not isinstance(sessions, list) or len(sessions) == 0:
		frappe.throw('Il parametro sessions deve essere un elenco non vuoto di sedute.')

	user_roles = roles()
	is_mgr = is_manager()
	my_prac = None
	allowed_patients = None
	if 'CC Professional' in user_roles and not is_mgr:
		my_prac = practitioner_for()
		if not my_prac:
			frappe.throw('Nessun profilo professionista associato al tuo utente.', frappe.PermissionError)
		allowed_patients = set(patient_names() or [])

	today_rome = _now_rome().date()
	target_date = getdate(date)
	base_reason = str(reason or '').strip()
	if not base_reason:
		base_reason = 'Chiusura della mia giornata' if target_date == today_rome else 'Completamento autonomo sedute arretrate'

	from centrochange_core.finance.collections import require_booking as require_payment_clearance

	# Query all actionable pending sessions for this practitioner/center on target_date
	closure_filters = {
		'cc_center': center,
		'appointment_date': target_date,
		'status': ['!=', 'Cancelled'],
		'cc_closure_state': ['in', ['Pending', 'Auto Locked', 'Reopened']]
	}
	if my_prac:
		closure_filters['practitioner'] = my_prac
	if allowed_patients is not None:
		closure_filters['patient'] = ['in', list(allowed_patients)]

	pending_candidates = frappe.get_all(
		'Patient Appointment',
		filters=closure_filters,
		fields=['name', 'appointment_date', 'appointment_time', 'duration']
	)
	now = now_utc()
	concluded_pending_names = []
	future_pending_names = []
	for p in pending_candidates:
		p_end_utc = start_utc(p) + timedelta(minutes=int(p.duration or 60))
		if p_end_utc <= now:
			concluded_pending_names.append(p.name)
		else:
			future_pending_names.append(p.name)

	updated = []
	seen = set()

	for item in sessions:
		if not isinstance(item, dict):
			frappe.throw('Ogni elemento di sessions deve essere un oggetto.')

		app_name = item.get('appointment') or item.get('name')
		if not app_name or not isinstance(app_name, str):
			frappe.throw('Identificativo seduta mancante o non valido.')

		if app_name in seen:
			frappe.throw(f'Seduta duplicata nel payload: {app_name}.')
		seen.add(app_name)

		# Explicit validation of performed
		if 'performed' not in item or item['performed'] is None:
			frappe.throw(f"Esito prestazione (performed) mancante per la seduta {app_name}.")
		performed_val = item['performed']
		if performed_val not in (0, 1, True, False):
			frappe.throw(f"Valore per 'performed' non valido per la seduta {app_name}: atteso 0 o 1.")
		performed = 1 if performed_val in (1, True) else 0

		# Explicit validation of paid & mode_of_payment
		paid_val = item.get('paid')
		if paid_val not in (0, 1, True, False, None):
			frappe.throw(f"Valore per 'paid' non valido per la seduta {app_name}: atteso 0 o 1.")
		paid = 1 if (performed and paid_val in (1, True)) else 0

		mode = None
		if performed and paid:
			mode = str(item.get('mode_of_payment') or '').strip()
			if not mode:
				frappe.throw(f"Metodo di pagamento obbligatorio per la seduta pagata {app_name}.")
			if not frappe.db.exists('Mode of Payment', mode):
				frappe.throw(f"Metodo di pagamento non riconosciuto nel sistema: {mode}.")

		item_note = str(item.get('note') or '').strip()
		session_reason = item_note if item_note else (base_reason if performed else 'Seduta non svolta')

		# Document load and permission check
		doc = frappe.get_doc('Patient Appointment', app_name, for_update=True)
		doc.check_permission('read')
		require_context(doc.patient, doc.cc_center)

		# Center verification
		if doc.cc_center != center:
			frappe.throw(f'La seduta {doc.name} appartiene al centro {doc.cc_center}, non al centro selezionato {center}.', frappe.PermissionError)

		# Date verification: doc date MUST match target_date
		if getdate(doc.appointment_date) != target_date:
			frappe.throw(f'La seduta {doc.name} ha data {doc.appointment_date}, diversa dalla data richiesta {target_date}.')

		# Practitioner verification (IDOR protection)
		if my_prac and doc.practitioner != my_prac:
			frappe.throw(f'Non sei autorizzato a modificare la seduta {doc.name} di un altro professionista.', frappe.PermissionError)

		# Cancelled verification
		if doc.status == 'Cancelled':
			frappe.throw(f'La seduta {doc.name} è cancellata e non può essere chiusa in questa procedura.')

		# Optimistic locking / revision check if supplied
		if item.get('revision') is not None:
			if cint(item['revision']) != cint(doc.cc_revision):
				frappe.throw(f'Conflitto di revisione per la seduta {doc.name}: attesa rev {doc.cc_revision}, inviata {item["revision"]}.', frappe.PermissionError)

		# Idempotent replay or conflict on already closed sessions
		if doc.cc_closure_state == 'Closed':
			existing_performed = 1 if doc.cc_performed else 0
			existing_paid = 1 if doc.cc_paid else 0
			existing_settlements = current_settlements(doc.name)
			existing_mop = existing_settlements[0].mode_of_payment if existing_settlements else None

			# Check exact match across all dimensions
			if existing_performed == performed and existing_paid == paid and (existing_mop or None) == (mode or None):
				updated.append({'name': doc.name, 'replay': True})
				continue
			frappe.throw(
				f'La seduta {doc.name} è già chiusa con parametri discordanti '
				f'(registrato: svolta={existing_performed}, pagata={existing_paid}, metodo={existing_mop}; '
				f'inviato: svolta={performed}, pagata={paid}, metodo={mode}). '
				f'Non è consentito sovrascrivere una seduta consolidata.',
				frappe.PermissionError
			)

		# Must be in finalizable state
		if doc.cc_closure_state not in ('Pending', 'Auto Locked', 'Reopened'):
			frappe.throw(f'Lo stato di chiusura della seduta {doc.name} ({doc.cc_closure_state}) non ne consente la finalizzazione.', frappe.PermissionError)

		# Temporal verification: NO closing future sessions (neither performed NOR no-show!)
		app_end_utc = start_utc(doc) + timedelta(minutes=int(doc.duration or 60))
		if app_end_utc > now_utc():
			frappe.throw(f'La seduta {doc.name} è programmata nel futuro (fine prevista: {app_end_utc.isoformat()}) e non può essere chiusa prima della sua conclusione.')

		was_auto_locked = (doc.cc_closure_state == 'Auto Locked')
		revision = cint(doc.cc_revision) + 1

		if performed:
			require_payment_clearance(doc)
			due = doc.cc_economic_state != 'Waived'
			packages.disposition(doc, due, session_reason, revision)
			economic = ('Package Covered' if doc.cc_package else 'Due') if due else 'Waived'

			with internal_write('cc_operation_write'):
				_patch(doc, {
					'status': 'Closed',
					'cc_closure_state': 'Closed',
					'cc_performed': 1,
					'cc_economic_state': economic,
					'cc_revision': revision
				})
			_settlement(doc, paid, mode, session_reason)

			if was_auto_locked:
				append('SESSION_LATE_COMPLETED', doc.doctype, doc.name,
					{'closure': 'Auto Locked', 'performed': 0, 'economic': 'Pending'},
					{'closure': 'Closed', 'performed': True, 'paid': bool(paid), 'economic': economic, 'method': mode if paid else None, 'note': item_note or None},
					session_reason)
			else:
				append('SESSION_CLOSED', doc.doctype, doc.name, None,
					{'performed': True, 'economic': economic, 'paid': bool(paid), 'method': mode if paid else None, 'note': item_note or None},
					session_reason)
		else:
			# Not performed:
			# Preserve existing economic state if already Due (e.g. late cancellation or package), or Waived
			if doc.cc_package:
				packages.disposition(doc, False, session_reason, revision)
				economic = 'Package Covered'
			elif doc.cc_economic_state == 'Due':
				economic = 'Due'
			elif doc.cc_economic_state == 'Waived':
				economic = 'Waived'
			else:
				economic = 'Non Due'

			with internal_write('cc_operation_write'):
				_patch(doc, {
					'status': 'No Show',
					'cc_closure_state': 'Closed',
					'cc_performed': 0,
					'cc_economic_state': economic,
					'cc_paid': 0,
					'cc_revision': revision
				})
			_settlement(doc, 0, None, session_reason)

			if was_auto_locked:
				append('SESSION_LATE_COMPLETED', doc.doctype, doc.name,
					{'closure': 'Auto Locked', 'performed': 0, 'economic': 'Pending'},
					{'closure': 'Closed', 'performed': False, 'paid': False, 'economic': economic, 'note': item_note or None},
					session_reason)
			else:
				append('SESSION_CLOSED', doc.doctype, doc.name, None,
					{'performed': False, 'economic': economic, 'paid': False, 'note': item_note or None},
					session_reason)

		updated.append({'name': doc.name, 'replay': False})

	# Full-Day Contract validation:
	unclosed_concluded = [name for name in concluded_pending_names if name not in seen]
	if unclosed_concluded and not allow_partial:
		frappe.throw(
			f"La chiusura della giornata è incompleta: risultano ancora {len(unclosed_concluded)} sedute pendenti concluse da gestire per la data {target_date}.",
			frappe.ValidationError
		)

	if future_pending_names and not allow_partial:
		frappe.throw(
			f"Impossibile completare la chiusura della giornata: risultano {len(future_pending_names)} sedute future non ancora concluse per la data {target_date}. Usa la chiusura parziale o attendi la conclusione della giornata.",
			frappe.ValidationError
		)

	day_closed = (len(unclosed_concluded) == 0 and len(future_pending_names) == 0)
	remaining_pending = len(unclosed_concluded) + len(future_pending_names)

	return {
		'status': 'PASS' if day_closed else 'PARTIAL',
		'day_closed': bool(day_closed),
		'remaining_pending': remaining_pending,
		'date': str(target_date),
		'updated_count': len(updated),
		'updated': updated
	}
