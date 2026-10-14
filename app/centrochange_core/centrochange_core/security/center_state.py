"""Audited operational state for existing ERPNext Branch records."""

import frappe

from centrochange_core.security.audit import append, atomic, internal_write
from centrochange_core.security.guards import is_manager
from centrochange_core.security.lifecycle import lock


@frappe.whitelist(methods=["GET"])
def list_centers():
    if not is_manager():
        frappe.throw("Gestione sedi riservata alla Direzione.", frappe.PermissionError)
    return frappe.get_list("Branch", fields=["name", "branch", "cc_operational"],
                           order_by="branch asc", page_length=100)


@frappe.whitelist(methods=["POST"])
@atomic
def set_operational(center, active, reason):
    lock()
    if not is_manager():
        frappe.throw("Gestione sedi riservata alla Direzione.", frappe.PermissionError)
    if str(active) not in ("0", "1") or not isinstance(reason, str) or not reason.strip():
        frappe.throw("Indica lo stato e il motivo del cambiamento.")
    doc = frappe.get_doc("Branch", center, for_update=True)
    target = int(active)
    before = int(doc.cc_operational or 0)
    if before == target:
        return {"center": doc.name, "active": before, "replay": True}
    if target and doc.name not in (frappe.conf.get("cc_operational_activation_allowed") or []):
        frappe.throw("L'attivazione della sede richiede una decisione e configurazione autorizzate.",
                     frappe.PermissionError)
    if not target:
        other = frappe.db.get_value("Branch", {"name": ["!=", doc.name], "cc_operational": 1}, "name",
                                    for_update=True)
        if not other:
            frappe.throw("Deve restare almeno una sede operativa.")
    with internal_write("cc_center_state_write"):
        doc.cc_operational = target
        doc.save(ignore_permissions=True)
    append("CENTER_OPERATIONAL_STATE", "Branch", doc.name,
           {"active": before}, {"active": target}, reason.strip())
    return {"center": doc.name, "active": target, "replay": False}


def protect_operational_state(doc, previous):
    if not previous and int(doc.get("cc_operational") or 0) and not frappe.flags.get("cc_center_state_write"):
        frappe.throw("Crea la nuova sede come non operativa; l'attivazione richiede un'azione tracciata.", frappe.PermissionError)
    if previous and int(doc.get("cc_operational") or 0) != int(previous.get("cc_operational") or 0):
        if not frappe.flags.get("cc_center_state_write"):
            frappe.throw("Lo stato della sede richiede l'azione autorizzata e tracciata.", frappe.PermissionError)
