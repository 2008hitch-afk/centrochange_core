"""Fictional XML, native payables and withdrawal regression, always rolled back."""
from hashlib import sha256
import frappe
from centrochange_core.security import dev_acceptance as security
from centrochange_core.finance import banking_acceptance,receivables_acceptance,incoming,banking
from centrochange_core.security.lifecycle import set_assignment


def xml(issuer='SYNTHETIC-PROVIDER-1',number='SYNTHETIC-EXPENSE-1',kind='TD01',vat=0):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<FatturaElettronica versione="FPR12"><FatturaElettronicaHeader>
<CedentePrestatore><DatiAnagrafici><IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>{issuer}</IdCodice></IdFiscaleIVA><Anagrafica><Denominazione>SYNTHETIC PROVIDER</Denominazione></Anagrafica></DatiAnagrafici></CedentePrestatore>
<CessionarioCommittente><DatiAnagrafici><IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>00000000000</IdCodice></IdFiscaleIVA></DatiAnagrafici></CessionarioCommittente>
</FatturaElettronicaHeader><FatturaElettronicaBody><DatiGenerali><DatiGeneraliDocumento><TipoDocumento>{kind}</TipoDocumento><Divisa>EUR</Divisa><Data>2026-10-05</Data><Numero>{number}</Numero><ImportoTotaleDocumento>{100+vat}</ImportoTotaleDocumento></DatiGeneraliDocumento></DatiGenerali>
<DatiBeniServizi><DettaglioLinee><NumeroLinea>1</NumeroLinea><Descrizione>SYNTHETIC reviewed professional expense</Descrizione><Quantita>1</Quantita><PrezzoUnitario>100</PrezzoUnitario><PrezzoTotale>100</PrezzoTotale><AliquotaIVA>{vat}</AliquotaIVA></DettaglioLinee><DatiRiepilogo><AliquotaIVA>{vat}</AliquotaIVA><ImponibileImporto>100</ImponibileImporto><Imposta>{vat}</Imposta></DatiRiepilogo></DatiBeniServizi></FatturaElettronicaBody></FatturaElettronica>'''


def checks(fixture):
    result=banking_acceptance.checks(fixture);reject=receivables_acceptance.rejected
    frappe.set_user('Administrator')
    patient,center,prac=[fixture[k] for k in ('patient','center','prac1')]
    set_assignment(patient,center,prac,1,'Synthetic payable fixture assignment')
    payload=xml(); before={dt:frappe.db.count(dt) for dt in ('Purchase Invoice','Payment Entry','GL Entry')}
    name=incoming.intake(center,payload,'Synthetic incoming XML retained')['name']
    assert incoming.intake(center,payload,'Synthetic exact XML retry')['replay']
    assert before=={dt:frappe.db.count(dt) for dt in before}
    source=frappe.get_doc('CC Incoming Invoice',name)
    assert source.state=='Needs Supplier Mapping'
    file=frappe.get_doc('File',source.payload_file)
    content=file.get_content()
    if isinstance(content,str):content=content.encode('utf-8')
    assert file.is_private and sha256(content).hexdigest()==source.payload_sha
    result.append('immutable private XML retained and deduped with unknown supplier and zero automatic postings')
    reject(lambda:incoming.intake(center,payload.replace('SYNTHETIC PROVIDER','SYNTHETIC PROVIDER CHANGED'),'Synthetic conflicting semantic duplicate'))
    source.total=999
    reject(lambda:source.save(ignore_permissions=True))
    reject(lambda:frappe.share.add_docshare('File',file.name,user=fixture['pro1'],read=1,flags={'ignore_share_permission':True}))
    reject(lambda:frappe.get_doc({'doctype':'File','file_name':'synthetic-alias.xml','is_private':0,'file_url':file.file_url}).insert(ignore_permissions=True))
    reject(lambda:frappe.get_doc({'doctype':'File','file_name':'synthetic-copy.xml','is_private':0,'content':payload}).insert(ignore_permissions=True))
    file.is_private=0
    reject(lambda:file.save(ignore_permissions=True))
    reject(lambda:frappe.delete_doc('File',file.name,ignore_permissions=True))
    retained=frappe.get_doc('File',source.payload_file).get_content()
    if isinstance(retained,str):retained=retained.encode('utf-8')
    assert sha256(retained).hexdigest()==source.payload_sha
    result.append('semantic duplicate raw source rewrite public attachment and deletion bypass denied')
    invalid=incoming.intake(center,'<!DOCTYPE x [<!ENTITY z SYSTEM "http://example.invalid">]><x>&z;</x>','Synthetic XXE input')['name']
    assert frappe.db.get_value('CC Incoming Invoice',invalid,'state')=='Invalid Source'
    unsupported=incoming.intake(center,xml(number='SYNTHETIC-CREDIT',kind='TD04'),'Synthetic unsupported credit review')['name']
    assert frappe.db.get_value('CC Incoming Invoice',unsupported,'state')=='Unsupported Document'
    result.append('unsafe malformed and unsupported XML retained as explicit exceptions without accounting documents')
    supplier=frappe.db.get_value('Healthcare Practitioner',prac,'supplier')
    frappe.db.set_value('Supplier',supplier,'tax_id','SYNTHETIC-PROVIDER-1')
    assert incoming.bind_supplier(name,supplier,'Synthetic exact fiscal supplier mapping')['state']=='Needs Classification'
    assert incoming.bind_supplier(name,supplier,'Synthetic supplier mapping retry')['replay']
    expense=frappe.db.get_value('Company',source.company,'default_expense_account')
    service='CC SYNTHETIC SESSION'
    frappe.db.set_value('Item',service,'is_purchase_item',1)
    args={'name':name,'items':[service],'expense_account':expense,'posting_date':'2026-10-05','due_date':'2026-10-31',
        'request_key':'synthetic-payable','reason':'Synthetic classified payable draft'}
    native=incoming.draft(**args)['name']
    assert incoming.draft(**args)['replay']
    assert frappe.db.get_value('Purchase Invoice',native,'docstatus')==0
    assert not frappe.db.count('GL Entry',{'voucher_no':native})
    assert frappe.db.get_value('Purchase Invoice',native,'cc_incoming_source')==name
    result.append('reviewed classified native payable draft retains XML supplier lines and total without GL')
    submitted=incoming.submit(native,'Synthetic explicit native payable posting')
    assert submitted['docstatus']==1 and submitted['outstanding']==100 and frappe.db.count('GL Entry',{'voucher_no':native})>0
    assert incoming.submit(native,'Synthetic payable posting retry')['replay']
    result.append('explicit native payable submission creates native liability and GL exactly once')
    movement={'external_id':'synthetic-expense-bank','date':'2026-10-05','withdrawal':40,'supplier':supplier,'reference':native,'description':'SYNTHETIC supplier transfer'}
    bank=banking.import_movements(center,[movement],'Synthetic expense withdrawal')['movements'][0]['name']
    candidate=banking.candidates(bank)
    assert candidate['state']=='Candidate' and candidate['document_type']=='Purchase Invoice'
    payment=banking.reconcile(bank,native,'Synthetic supplier bank reconciliation')
    assert incoming.position(native)['outstanding']==60 and payment['movement']['unallocated']==0
    assert banking.reconcile(bank,native,'Synthetic supplier bank replay')['movement']['replay']
    banking.cancel(bank,'Synthetic expense reconciliation reversal')
    assert incoming.position(native)['outstanding']==100
    result.append('native bank withdrawal posts supplier payment clearance and allocation; reversal restores payable')
    incoming.cancel(native,'Synthetic classification correction cancellation')
    assert incoming.cancel(native,'Synthetic payable cancel retry')['replay']
    amended=incoming.amend(native,expense,'2026-10-05','2026-10-31','synthetic-payable-amend','Synthetic explicit classification amendment')['name']
    assert incoming.amend(native,expense,'2026-10-05','2026-10-31','synthetic-payable-amend','Synthetic amendment retry')['replay']
    incoming.submit(amended,'Synthetic corrected payable posting')
    assert frappe.db.get_value('Purchase Invoice',amended,'amended_from')==native
    first=incoming.pay(amended,30,'2026-10-05','synthetic-supplier-partial','Synthetic partial supplier payment')
    assert first['invoice']['outstanding']==70
    assert incoming.pay(amended,30,'2026-10-05','synthetic-supplier-partial','Synthetic supplier payment retry')['invoice']['replay']
    assert incoming.pay(amended,70,'2026-10-05','synthetic-supplier-full','Synthetic full supplier payment')['invoice']['outstanding']==0
    result.append('native cancel amend reissue partial full supplier payments retain source history and idempotence')
    taxable=incoming.intake(center,xml(number='SYNTHETIC-VAT',vat=22),'Synthetic explicit tax input')['name']
    incoming.bind_supplier(taxable,supplier,'Synthetic tax supplier mapping')
    reject(lambda:incoming.draft(**{**args,'name':taxable,'request_key':'synthetic-tax','tax_account':None}))
    tax=frappe.db.get_value('Account',{'company':source.company,'account_type':'Tax','is_group':0},'name')
    tax_doc=incoming.draft(**{**args,'name':taxable,'request_key':'synthetic-tax','tax_account':tax})
    assert tax_doc['total']==122
    result.append('tax classification is explicit; reviewed native gross total reconciles with XML net and tax facts')
    for actor in (fixture['pro1'],fixture['pro2'],'accountant.cc-regression@example.invalid'):
        frappe.set_user(actor)
        reject(lambda:incoming.submit(amended,'Unauthorized payable mutation'))
        reject(lambda:incoming.intake(center,xml(number='UNAUTHORIZED'),'Unauthorized intake'))
        if actor!='accountant.cc-regression@example.invalid':
            for dt,id in [('CC Incoming Invoice',name),('Purchase Invoice',amended),('File',source.payload_file)]:
                reject(lambda:frappe.get_doc(dt,id).check_permission('read'))
        else:
            frappe.get_doc('CC Incoming Invoice',name).check_permission('read')
            frappe.get_doc('Purchase Invoice',amended).check_permission('read')
        result.append('professional/readonly accountant incoming source private file and native payable boundary')
    frappe.set_user('Administrator')
    set_assignment(patient,center,prac,0,'Synthetic payable fixture release')
    return result


def run():
    previous=frappe.flags.get('cc_test_clock')
    try:
        return security.run(extra_checks=checks)
    finally:
        frappe.flags.cc_test_clock=previous


@security.synthetic_test
def prepare_http(fixture, prepare_bank=True):
    if frappe.session.user!='Administrator' or frappe.conf.get('cc_synthetic_dev')!=1:
        frappe.throw('Synthetic DEV Administrator required')
    if isinstance(fixture,str):
        fixture=frappe.parse_json(fixture)
    assert fixture['tag'].startswith('CC-HTTP-')
    if prepare_bank:
        banking_acceptance.prepare_http(fixture)
    else:
        from centrochange_core.finance.dev_profile import setup
        setup(fixture['finance']['customer'])
        from centrochange_core.finance import banking
        banking.configure_bank(fixture['centers'][0],fixture['tag'])
    issuer='SYNTHETIC-'+fixture['tag']
    supplier=fixture['finance']['supplier']
    frappe.db.set_value('Supplier',supplier,'tax_id',issuer)
    item=fixture['catalog']['Item'][0]
    frappe.db.set_value('Item',item,'is_purchase_item',1)
    payload=xml(issuer,fixture['tag']+'-EXPENSE')
    native_company=frappe.db.get_value('Branch',fixture['centers'][0],'cc_company')
    frappe.db.commit()
    return {'xml':payload,'supplier':supplier,'item':item,
        'expense_account':frappe.db.get_value('Company',native_company,'default_expense_account')}



def cleanup_known_orphan_payloads():
    """Only orphan bytes from fixed synthetic acceptance vectors, never a retained File."""
    from pathlib import Path
    if frappe.session.user!='Administrator' or frappe.conf.get('cc_synthetic_dev')!=1:
        frappe.throw('Synthetic DEV Administrator required')
    known={sha256(payload.encode('utf-8')).hexdigest() for payload in [xml(),xml(number='SYNTHETIC-CREDIT',kind='TD04'),
        xml(number='SYNTHETIC-VAT',vat=22),'<!DOCTYPE x [<!ENTITY z SYSTEM "http://example.invalid">]><x>&z;</x>']}
    removed=0
    for private in (False,True):
        directory=Path(frappe.get_site_path('private' if private else 'public','files'))
        for path in directory.glob('CC-INCOMING-*.xml.payload'):
            digest=sha256(path.read_bytes()).hexdigest()
            url=('/private/files/' if private else '/files/')+path.name
            if digest in known and path.name.startswith('CC-INCOMING-'+digest) and not frappe.db.exists('File',{'file_url':url}):
                path.unlink();removed+=1
    return {'known_synthetic_orphans_removed':removed}
