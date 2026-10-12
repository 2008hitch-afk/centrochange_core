# Missione C #109 — priorità assoluta UI, preparazione demo Desk

**Esito: `MISSION-C: PARTIAL`; `DEMO OWNER VISIBILE: NO`.** PR prodotto #112 DRAFT, stacked su #107. Questo rapporto distingue il codice UI preparato offline dalla prova runtime che manca. Nessun container C109 è stato riavviato dopo lo stop PSI registrato in `C109-UI-PRIORITY-2026-10-11.md`; RC22 non è stato modificato.

## Prodotto preparato

Il lavoro riparte dal prodotto `d213371cc372272106728e7a920325dab43fa4e3`; ultimo commit UI di questa iterazione `6c83704262e090d2b50c2df5362da710c50bfe52`. La Page `cc-unified-desk` ora apre una dashboard italiana “Inizio”, segna ogni schermata come “Versione dimostrativa · dati di prova” e offre un menu coerente con i ruoli. I collegamenti portano alle quattro superfici custom già giustificate dalla matrice C1 — Agenda, Finanza, Report professionisti, Report pazienti — oppure alle List/Form ERPNext/Healthcare autorizzate. Dashboard, routing e grafica non aggiungono API, ruoli, grant, business logic, contabilità o master duplicati.

Le schede di accesso diretto riusano le sezioni dei controller esistenti: Pazienti, Disponibilità, Notifiche e Gestione accessi nel workspace operativo; Banca, SdI simulato e TS simulato nel workspace Finance. I parametri `cc_ops_view`/`cc_fin_view` sono accettati solo dalla lista di viste già implementate e solo dentro il Desk. I guard server-side rimangono autorevoli; mostrare o nascondere un link non autorizza l'accesso. L'Audit rimane nella List nativa `CC Audit Event` per Manager. La webapp RC22 e il sito pubblico rimangono separati.

Il delta OCI locale per la demo è stato confezionato **senza build Docker** sopra l'immagine finale già presente: manifest `sha256:cc97a65c8fdd4d2cb8fd9c15fb861123bb0d3201cbbb204b4acd2352a84ada25`, revisione `6c83704`, archivio privato di 81.920 byte in `/home/empv26/.local/state/centrochange-c109-ui-r4-20261011/desk-demo-final.oci.tar`. È un artefatto di preparazione, **non importato né eseguito**. Restano i pin sperimentali TARGET: Frappe `f20f92d29706510551b4438cc196b0323a7f1a92`, ERPNext `7474d9e786277383de1242ab882f16856d17a9c9`, Healthcare `dda107b26e3a0fe1dbd65c7257371235de054a04`, Builder `37e958bc4f801d06d0438c21b97b42c45c4eaa51`; nessuna promozione in RC22.

## Verifiche eseguite

| Controllo | Esito |
| --- | --- |
| Git status, branch e conservazione lavoro esistente | **PASS**; branch dedicato #112, nessuna modifica locale perduta |
| Dashboard/routing offline Manager, Professional, Finance, incluso parametro non riconosciuto | **PASS**, 3 controlli con DOM simulato, senza browser |
| Sintassi JS dei tre controller toccati e diff check | **PASS** |
| Regressioni statiche C109 | **PASS**, 37/37 test già versionati |
| OCI packaging | **PASS offline**: revision label e byte di Page JS/CSS e controller corrispondono al sorgente |
| UI nel browser, 24 aree, ruoli, API/permessi e confronto C3 sulla nuova immagine | **NOT TESTED** |
| Accesso Owner alla nuova demo | **NON DISPONIBILE**; C109 resta spento |

Il precedente tentativo sul server condiviso ha avviato 8/8 servizi con cap effettivi e ottenuto ping C109 HTTP 200; il **primo Chromium** ha poi fatto scattare lo stop PSI I/O host (2,20% contro 1%). Il guard ha chiuso l'attivazione senza retry, zero OOM, RC22 HTTP 200/nove container invariati. Quei risultati riguardano l'immagine precedente `d213371`, non costituiscono test della dashboard `6c83704`.

## Gate unico per rendere visibile la demo

Serve **nuova autorizzazione Owner specifica** per una singola attivazione C109 sul server attuale dopo lo stop di sicurezza precedente: nuova finestra con margine di arresto, stesso watchdog/event monitor, cap 2 GiB runtime + 512 MiB QA, swap zero, soglia PSI I/O full <1%, verifica PID/cgroup prima del workload, RC22 HTTP 200/nove ID invariati, stop al primo evento senza retry. Il percorso minimo importa il piccolo delta OCI, usa i volumi sintetici C109 già presenti e apre `http://localhost:8109/app/cc-unified-desk` via tunnel Owner **solo dopo** ping e smoke browser positivi. Nessuna copia integrale dei volumi, migrazione o suite completa dei 24 moduli precede la prima dimostrazione visiva. Se il guard scatterà ancora, l'alternativa separata documentata nel rapporto precedente rimane l'unica via proposta; non si prova ripetutamente sul server condiviso.

Fino a quel gate, non esiste un URL di demo funzionante e non si dichiara `READY_FOR_OWNER_UAT`.
