"""Build the audit index, keeping capability counts distinct from test counts."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/evidence/mvp-functional-audit'
ROWS = '''001|Runtime e isolamento DEV|infra/compose.yaml|Tecnico|PASS|Nove servizi, immagini e hook; baseline installata e W5 riusati|runtime-final.json
002|Identità professionista e utente|security/lifecycle.py|Direzione; setup tecnico|PASS|Creazione nativa, assegnazioni, cambio principal e disabilitazione con revoca|integrated-runtime.json; native-runtime.json
003|Anagrafica paziente centrale|operations/workspace.py|Segreteria/Direzione; setup tecnico|PASS|Intake e UID univoco, replay, rollback creazione non valida, salvataggio nativo|integrated-runtime.json; native-runtime.json
004|Assegnazione paziente/professionista|security/lifecycle.py|Direzione/Segreteria secondo azione|PASS|Riassegnazione e revoca effettive; accessi precedenti negati|integrated-runtime.json; supplemental-suites.json
005|Segregazione appuntamenti|security/permissions.py|Professionisti assegnati|PASS|Own/cross record, liste, API, revoca centro; HTTP W5 sulla stessa immagine|integrated-runtime.json; W5
006|Appuntamento e seduta canonica|scheduling/booking.py; operations/lifecycle.py|Operativi autorizzati|PASS|Prenota, sposta, cancella, chiude; stessa identità, replay e stati controllati|integrated-runtime.json
007|Disponibilità ricorrente e assenze|scheduling/availability.py|Professionista proprio; Direzione|PASS|Creazione/modifica orari, assenza nativa, cancellazione assenza, disponibilità ripristinata|integrated-runtime.json
008|Collisioni e concorrenza|scheduling/booking.py|Operativi autorizzati|PASS|Conflitti paziente/professionista; W5 HTTP: una sola prenotazione concorrente e una unità pacchetto|integrated-runtime.json; W5
009|Primo incontro pubblico limitato|scheduling/public_booking.py|Guest, route approvate|PASS|HTTP reale W5: route vincolata, creazione una volta, replay, route arbitraria/disabilitata negata|W5; supplemental-suites.json
010|Sedute successive solo backend|scheduling/public_booking.py; security/api.py|Operativi autenticati|PASS|W5 nega prenotazione pubblica successiva e bypass portale Marley|W5
011|Catalogo servizi centrale per sede|scheduling/booking.py; centro_change_core/doctype/cc_center_service|Setup tecnico; consultazione autorizzata|PASS|Item e tipo seduta creati/salvati; servizio disabilitato rifiutato; CC Center Service salvato|native-runtime.json; integrated-runtime.json
012|Listini e prezzi|scheduling/booking.py|Setup tecnico; uso operativo|PASS|Item Price salvato e riletto; selezione tariffa alla data prenotazione|native-runtime.json; integrated-runtime.json
013|Snapshot servizio/durata/prezzo|scheduling/booking.py|Operativi autorizzati|PASS|Cambio tariffa/catalogo non riscrive seduta; tampering rifiutato; spostamento conserva snapshot|integrated-runtime.json
014|Pagato operativo e metodo informativo|operations/lifecycle.py|Operativi autorizzati secondo stato|PASS|Correzioni ordinate e audit, replay, separazione dall'incasso contabile|integrated-runtime.json
016|Pacchetti e ledger|operations/packages.py|Operativi autorizzati|PASS|Assegna, riserva, consuma, rilascia, rettifica; concorrenza ultima unità e audit|integrated-runtime.json; native-runtime.json; W5
017|Note organizzative|operations/notes.py|Operativi autorizzati|PASS|Note operative nel contesto; storico e isolamento; contenuti esclusi dalla stampa allowlist|integrated-runtime.json
018|Note professionali riservate|operations/notes.py|Solo autore professionista autorizzato|PASS|Revisioni append-only; altri professionisti, Segreteria, Direzione e Administrator senza corpo riservato|integrated-runtime.json; supplemental-suites.json; W5
019|Scheda paziente unificata|operations/workspace.py|Operativi autorizzati|PASS|Anagrafica, agenda, storico e note nel medesimo scope; reporting contabile separato|integrated-runtime.json; supplemental-suites.json
020|Storico paziente|operations/workspace.py|Operativi autorizzati|PASS|Feed non vuoto con revisioni proprie, esclusione note altrui e controllo centro|integrated-runtime.json
022|Chiusura giornaliera|operations/lifecycle.py|Professionista/operativi autorizzati|PASS|Chiusura e stato economico, consumo unità una volta, modifica chiusa negata|integrated-runtime.json
023|Reminder ore 21|operations/automation.py|Job e destinatario autorizzato|PASS|Clock sintetico locale, catch-up/replay una volta; Notification Log locale realmente inserita|integrated-runtime.json; readonly-runtime.json
024|Auto-lock ore 07|operations/automation.py|Job; correzione autorizzata|PASS|Boundary e retry, blocco server delle azioni professionista, scheduler configurato|integrated-runtime.json; readonly-runtime.json
025|Disdetta 48h e rinuncia economica|operations/lifecycle.py|Operativi; deroga solo autorizzati|PASS|48h esatte tempestiva; un microsecondo meno tardiva/dovuta; DST; rinuncia conserva fatto storico|integrated-runtime.json
026|Riapertura e correzioni governate|operations/lifecycle.py|Segreteria/Direzione secondo policy|PASS|Riapertura auditata/idempotente e dinieghi; escluso spostamento storico #78 per DECISION-059|integrated-runtime.json
027|Notifiche e comunicazioni simulate|operations/notifications.py; operations/booking_confirmation.py|Destinatario; recovery Direzione|PASS|Communication primo incontro, failure/retry/replay; Notification Log; nessun Email Queue/invio reale|supplemental-suites.json; integrated-runtime.json
028|Reporting operativo|operations/reporting.py|Scope operativo del ruolo|PASS|Totali confrontati con record Agenda, stampa senza note, CSV formula-safe|integrated-runtime.json
029|Export e stampa autorizzati|operations/reporting.py; finance/reporting.py|Ruoli autorizzati|PARTIAL|Controlli di accesso e dati corretti; CSV umano conserva intestazioni inglesi e date ISO, contro #134|integrated-runtime.json; readonly-runtime.json
030|Dashboard direzionale|operations/reporting.py; finance/reporting.py|Direzione; Finance per contabilità|PASS|Aggregati riconciliati; unknown distinti da zero; margine non inventato senza policy|integrated-runtime.json; readonly-runtime.json
033|Modello generale permessi|security/guards.py; security/permissions.py|Sette ruoli, Guest, Administrator|PASS|Matrice ruoli, revoca, centro inattivo, segregazione clinica/contabile e setup tecnico|supplemental-suites.json; readonly-runtime.json; http-readonly.json; W5
034|Audit business immutabile|security/audit.py; security/audit_view.py|Direzione per registro|PASS|Modifica/cancellazione audit negate; attore/motivo/prima-dopo; eventi attuali trovati e altri ruoli negati|integrated-runtime.json; readonly-runtime.json
035|Backup DB/file/config|infra/issue139_install_gate.py|Tecnico|PASS|Backup cifrato e recupero completo già provati nella rehearsal/installazione 14 ottobre; non ripetuti|W5; THIRD-DEV-INSTALLATION-READINESS-REPORT
038|Autorizzazione API/web|security/api.py; finance/request_guard.py|Tutti i ruoli|PASS|REST/direct/API/export e Guest; controlli server attivi; sei hook presenti|http-readonly.json; runtime-final.json; W5
039|Regressione anti-leakage|security/dev_acceptance.py; infra/security_acceptance.py|Sette ruoli/Guest|PASS|38 test HTTP attuali riusati, note/finance/cross-center e namespace protetti|W5; supplemental-suites.json
040|Deploy riproducibile|infra/issue139_install_gate.py|Tecnico|PASS|Immagine e candidato identificati, backup/installazione/rollback già provati; nessuna modifica audit al runtime|runtime-final.json; W5
041|Bridge e master contabili|finance/bridge.py|Finance/Segreteria/Direzione; Commercialista lettura|PASS|Patient/Customer, Practitioner/Supplier, centro/Cost Center; correzione append-only e snapshot|integrated-runtime.json
042|Fatture pazienti, crediti e incassi|finance/receivables.py; finance/native_adapter.py|Finance/Segreteria/Direzione|PARTIAL|Bozza/GL, singola/aggregata, incasso parziale/totale, credito/cancel/reissue PASS; metodo carta/POS per singolo pagamento non coperto dal servizio/UI|integrated-runtime.json; readonly-runtime.json
043|Banca, scadenze e solleciti base|finance/banking.py; finance/collections.py|Finance/Segreteria/Direzione|PASS|Import dedupe, match/ambiguità, pagamento, reversal, blocco insoluti, differimento con debito invariato|integrated-runtime.json; browser-readonly.json; readonly-runtime.json
044|XML ricevuti e fatture professionisti|finance/incoming.py|Finance/Segreteria/Direzione; Commercialista lettura|PASS|XML privato, mapping, doppioni/XXE, bozza/submit, pagamento, annullo/rettifica, IVA sintetica|integrated-runtime.json
045|Compensi e confronto ricevuto|finance/professional_economics.py|Finance/Direzione; Commercialista lettura|PASS|Soglie N=0/1/2/5 per coppia, sospensione/override, rivalutazione incasso/storno, confronto OK/REVIEW|integrated-runtime.json; supplemental-suites.json; browser-readonly.json
046|Coda amministrativa|finance/admin_queue.py|Amministrativi autorizzati|PASS|Condizioni deduplicate, assegnazione, priorità, scadenza, rinvio/riapparizione, chiusura automatica e riapertura|integrated-runtime.json
047|Report Finance, ruoli e audit|finance/reporting.py; finance/patient_reporting.py; finance/request_guard.py|Finance/Segreteria/Direzione/Commercialista|PARTIAL|Viste Centro/Professionista/Paziente riconciliate; General Ledger e Trial Balance nativi non raggiungibili dai ruoli cliente|integrated-runtime.json; supplemental-suites.json; http-readonly.json
048|Adapter SdI simulato indipendente|finance/sdi.py; finance/fiscal.py|Finance/Direzione secondo azione|PASS|XML/protocollo simulato, successo/rifiuto/retry/limite, correzione, inbound e payload privato|integrated-runtime.json
049|Adapter TS ordinario simulato|finance/ts.py; finance/fiscal.py|Revisione Direzione; azioni Finance consentite|PASS|Eligibilità/opposizione persistenti per versione, retry/correzione, esiti e coda; nessun invio reale|integrated-runtime.json
050|Verifica integrata e readiness MVP|operations/integration_acceptance.py; infra/integrated_acceptance.py|Tecnico e successiva review Owner|PARTIAL|189 controlli backend reali PASS dopo adattamento test; vecchi gate falliscono per lingua/ID e il viaggio HTTP/browser completo con commit non è riprovato in sicurezza|integrated-runtime.json; initial-suite-results.json'''

matrix=[]
for line in ROWS.splitlines():
    number,title,implementation,roles,status,test,evidence=line.split('|')
    matrix.append(dict(id='CC-CAP-'+number,title=title,source='CAPABILITY-EVALUATION-MATRIX + MVP-IMPLEMENTATION-CAPABILITY-MAP; Discovery/decisioni approvate',implementation=implementation,roles=roles,status=status,test=test,evidence=evidence))
matrix.extend([
    dict(id='SCOPE-DOC',title='Allegati amministrativi manuali: PDF, ricevute, scansioni',source='SCOPE-DELTA-001 REV3 § Non-structured documents; DECISION-034',implementation='finance/files.py; File nativo',roles='Amministrativi autorizzati',status='PARTIAL',test='Guard prima insert rifiuta nuovo PDF privato su fattura; nessun servizio ordinario di allegato individuato. XML fiscali invece presenti e provati.',evidence='readonly-runtime.json'),
    dict(id='UAT-GLOBAL',title='Interfaccia operativa coerente, italiana e utilizzabile',source='Issue #136/#134/#75; requisiti trasversali Owner',implementation='public/js; public/css; centro_change_core/page/cc_unified_desk',roles='Sette ruoli cliente',status='PARTIAL',test='128 route e 22 List/Form già PASS; confronto mobile taglia le etichette, CSV inglese/ISO e altri residui. Review Owner non sostituita.',evidence='browser-readonly.json; screenshots/comparison-390.png; W5'),
])
for number,title in [('015','Percorso accounting storico sostituito da 041–050'),('021','Patient Progress/clinical analytics'),('031','Sito pubblico branded completo'),('032','Builder/Git per sito pubblico rinviato'),('036','DR completo come requisito di release produzione'),('037','Qualifica upgrade come requisito di release produzione')]:
    matrix.append(dict(id='CC-CAP-'+number,title=title,source='MVP capability map; decisioni scope',implementation='Rinvio/sostituzione approvati',roles='Non pertinente al gate corrente',status='FUTURE/OUT OF SCOPE',test='Non incluso nel totale MVP. Prove restore recenti non autorizzano GOAL-03.',evidence='docs/MVP-IMPLEMENTATION-CAPABILITY-MAP-v0.1.yaml'))

(OUT/'capability-matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
with (OUT/'capability-matrix.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(matrix[0]));w.writeheader();w.writerows(matrix)
counts=Counter(r['status'] for r in matrix)
assert len([r for r in matrix if r['id'].startswith('CC-CAP-') and r['status']!='FUTURE/OUT OF SCOPE'])==44
assert sum(counts.values())==52
(OUT/'counts.json').write_text(json.dumps({'unit':'44 capability attive + 2 requisiti espliciti di scope/UAT; non numero test','mvp_total':46,'status_counts':dict(counts)},indent=2)+'\n')
md=['| ID | Funzionalità | Implementazione¹ | Ruoli | Esito | Prova / limite | Evidenza |','|---|---|---|---|---|---|---|']
for row in matrix:
    md.append('| '+' | '.join([row['id'],row['title'],'`'+row['implementation']+'`',row['roles'],row['status'],row['test'],row['evidence']])+' |')
(OUT/'MATRIX.md').write_text('# Matrice funzionale completa\n\n¹ Percorsi applicativi relativi a `app/centrochange_core/centrochange_core`; percorsi `infra/` relativi al repository. Fonti puntuali e precedenza nel rapporto principale e in `source-provenance.json`. W5 indica la terza installazione DEV, non i tentativi ripristinati.\n\n'+'\n'.join(md)+'\n')
print(dict(counts))
